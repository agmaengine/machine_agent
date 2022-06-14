import asyncio
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Lock
from multiprocessing import Process, Queue
import logging


def flush_init(stdout, q):
    while True:
        line = stdout.readline()
        print(f"{line}", end="")
        if line:
            break
    q.put(False)



    

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

        nexit=True
        busket = Queue(maxsize=1)
        p = Process(target=flush_init, args=(self.process.stdout, busket))
        p.start()
        print("start initialize")
        p.join(timeout=20)
        print("waited 20 seconds")
        while nexit:
            self.process.stdin.write("\n")
            p.join(timeout=1)
            if busket.full():
                nexit = busket.get()
            # print(f"looping ? nexit {nexit}")

        self.status = True

    def send_command(self, server_command: str):
        # command validation
        pass