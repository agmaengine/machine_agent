import io
import subprocess
from subprocess import Popen, PIPE, STDOUT
import multiprocessing
from multiprocessing import Process, Pipe
import logging



class Sopen(Popen):
    def __init__(self, cmd):
        """
            start process with PIPE stdin and stdout
            add control over longrunning process
        """
        super().__init__(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True)
        self.logger = logging.getLogger("Sopen")
        self._pipe, self._read_pipe = Pipe()
        self._reader_process = Process(target=self._flush_until_block)
        self._reader_process.start()

    def _flush_until_block_terminatable(self):
        while True:
            line = self.stdout.readline() # block line release when stdin
            self._read_pipe.send(line) # only send each lines
            # print(f"{line} length: {len(line)}", end="")
            busy = self._read_pipe.poll() # check if there is something sent ?
            if busy:
                self.logger.info("reader: get something from pipe")
                terminate = self._read_pipe.recv() # get terminate signal
                self.logger.info("reader: it is terminate signal")
                if terminate: 
                    break
    
    def _flush_until_block(self):
        line = True
        while bool(line):
            line = self.stdout.readline() # block line release when stdin
            self._read_pipe.send(line) # only send each lines
            # print(f"{line} length: {len(line)}", end="")
            # exit when reached EOF

    
    def join_no_response(self, timeout: float = 5.0, get_return: bool=False) -> list:
        """
            join the process when there is no response 
            from the process for {timeout} seconds
        """
        line_busket = []
        while True:
            if timeout is None:
                busy = self._pipe.poll(timeout)
            else:
                busy = self._pipe.poll(timeout=timeout)
            if not busy:
                self.logger.info(f"no response for {timeout} seconds")
                break
            
            line = self._pipe.recv()
            print(line, end="")
            if get_return:
                line_busket.append(line)

        return line_busket

    def flush_pipe(self):
        while self._pipe.poll(timeout=0.2):
            line = self._pipe.recv()
            print(line, end='')

    def communicate(self, input_cmd: str, wait_for=0.2):
        self.flush_pipe()
        self.stdin.write(f'{input_cmd}\n')
        self.stdin.flush()
        return self.join_no_response(timeout=wait_for, get_return=True)

    def _stop_reader(self):
        self._reader_process.terminate()
        self._pipe.close()
        self._read_pipe.close()

    def terminate(self):
        self._stop_reader()
        super().terminate()
    
    def kill(self):
        self._stop_reader()
        super().kill()

class MinecraftServer(Sopen):
    def terminate(self):
        self.communicate('/save-all')
        self.communicate('/stop', wait_for=5)
        super().terminate

    def kill(self):
        self.communicate('/save-all')
        self.communicate('/stop', wait_for=5)
        super().kill