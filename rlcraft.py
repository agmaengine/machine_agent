import asyncio
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Lock
from multiprocessing import Process, Queue
import logging


class FQueue:
    def __init__(self, *args, **kwargs):
        self.q = Queue(*args, **kwargs)

    def flush(self):
        q = []
        while not self.empty():
            q.append(self.q.get())
        return q

    def put(self, item, *args, **kwargs):
        return self.q.put(item, *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.q.get(*args, **kwargs)

    def full(self, *args, **kwargs):
        return self.q.full(*args, **kwargs)
        
    def empty(self, *args, **kwargs):
        return self.q.empty(*args, **kwargs)


class LineBusket(FQueue):
    def put(self, item, *args, **kwargs):
        # validate if item is str
        assert type(item) is str, "item is expected to be string"
        super().put(item, *args, **kwargs)

    def flush(self):
        q = []
        while not self.empty():
            line = self.get()
            q.append(line)
            print(line, end='')
        return q


def flush_until_block(stdout, break_sig, line_busket):
    while True:
        line = stdout.readline()
        line_busket.put(line)
        # print(f"{line} length: {len(line)}", end="")
        if not line:
            # print(f"{line} length: {len(line)}, bool: {bool(line)}", end="")
            break
    break_sig.put(False)


def wait_until_input_availabel(process: Popen, method=flush_until_block):
    """
        stdin as _io.TextIOWarpper, 
        stdout as _io.BufferedReader
        return remaining line that is not flushed
    """
    nexit=True
    break_sig = Queue(maxsize=1)
    line_busket = LineBusket(maxsize=30)
    p = Process(target=method, args=(process.stdout, break_sig, line_busket))
    logging.info("start listening to stdout")
    p.start()
    while nexit:
        process.stdin.write("\n")
        process.stdin.flush()
        p.join(timeout=1)
        if line_busket.full():
            line_busket.flush()
        if break_sig.full():
            nexit = break_sig.get()
    return line_busket.flush()
            
    

class MinecraftServer:

    process: Popen
    status: bool = False
    player: int = 0


    def start_server(self, Popen_command: list):
        self.process = Popen(Popen_command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True)
        exit_code = self.process.poll()
        if exit_code is not None:
            return exit_code
        self.process.stdin.reconfigure(line_buffering=True) # flush buffer when \n is written
        wait_until_input_availabel(self.process)
        self.status = True

    def send_command(self, server_command: str):
        # command validation
        pass