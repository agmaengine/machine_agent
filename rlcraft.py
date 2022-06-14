import asyncio
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Lock
from multiprocessing.connection import Connection
from multiprocessing import Process, Queue, Pipe
import logging
import time
import io




def flush_until_block(stdout: io.BufferedReader, pipe: Connection):
    logger = logging.getLogger("flush_until_block")
    while True:
        line = stdout.readline() # block line release when stdin
        pipe.send(line) # only send each lines
        # print(f"{line} length: {len(line)}", end="")
        busy = pipe.poll() # check if there is something sent ?
        if busy:
            logger.info("reader: get something from pipe")
            terminate = pipe.recv() # get terminate signal
            logger.info("reader: it is terminate signal")
            if terminate: 
                break


def wait_until_input_availabel(process: Popen, wait_for: float = 5.0, get_return: bool=False) -> list:
    """
        stdin as _io.TextIOWarpper, 
        stdout as _io.BufferedReader
        return remaining line that is not flushed
    """
    line_busket = []
    pipe, pipe_client = Pipe()
    p = Process(target=flush_until_block, args=(process.stdout, pipe_client))
    logging.info("start listening to stdout")
    p.start()

    def recv():
        line = pipe.recv()
        print(line, end="")
        if not get_return:
            line_busket.append(line)

    while True:
        # p.join(timeout=1)
        busy = pipe.poll(timeout=wait_for) #
        if not busy:
            logging.info("process stop reporting for 5 seconds, try sending input to see if the process response")
            # poking to see if the subprocess is responding to input
            process.stdin.write("\n")
            process.stdin.flush()
            busy = pipe.poll(timeout=0.2) # wait for 200 ms
            if busy: # means the process is ready to recieve input
                logging.info("the process responded, it is ready for input")
                # logging.info("try sending terminate signal to reader")
                logging.info("try to terminate process")
                while p.is_alive():
                    logging.info("sending terminate signal")
                    while pipe.poll(timeout=0.2):
                        recv()
                    pipe.send(True) # send terminate signal
                    # poke the subprocess again to release the process from 
                    # blocking readline() and recieve the terminate signal
                    process.stdin.write("\n")
                    process.stdin.flush()
                    time.sleep(0.2) # if not wait it is slipping
                break
        
        recv()
    
    p.close()
    pipe.close()
    pipe_client.close()
    logging.info("closing all connections and terminate reader process")
    return line_busket
            

def communicate(process: Popen, process_cmd: str, wait_for=0.2):
    logging.info(f"write to stdin stream: {process_cmd}")
    process.stdin.write(f"{process_cmd}\n")
    process.stdin.flush()
    return wait_until_input_availabel(process, get_return=True)


class MinecraftServer:

    process: Popen
    status: bool = False
    player: int = 0


    def start_server(self, Popen_command: list):
        self.process = Popen(Popen_command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True)
        exit_code = self.process.poll()
        if exit_code is not None:
            return exit_code
        # self.process.stdin.reconfigure(line_buffering=True) # flush buffer when \n is written
        wait_until_input_availabel(self.process)
        self.status = True

    def send_command(self, server_cmd: str):
        # command validation
        communicate(self.process, server_cmd)
        pass
