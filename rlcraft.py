import asyncio
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Lock
from multiprocessing import Process, Queue
import logging

# thread_lock = Lock()



# def returnable(func, busket):
#     busket = func()
#     # print(busket)

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        # print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, timeout=None, *args):
        Thread.join(self, *args)
        return self._return

async def async_readline(stdout):
    return stdout.readline()

async def async_flush_init(stdout):
    while True:
        line = await async_readline(stdout)
        if "seed:" in line.lower():
            break
    return 0


def ts_print(*args, **kwargs):
    with thread_lock:
        print(*args, **kwargs)

def ts_nonblock_print(*args, **kwargs):
    thread_lock.acquire(blocking=False)
    print(*args, **kwargs)
    thread_lock.release()


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
        # while initializing server produce a lot of stdout but process.stdout.read() wait forever if process still running
        # terminate read() kill the process
        # first try using process.stdout.readline() but if the process still running,
        # next line are not printed. readline() wait for the next line forever.
        # terminate readline() kill the process, 
        # I am thinking about using thread because if can timeout the readline() function
        # if we wait until it is timeout we can send stdin to check weather the server is ready
        # line = ''
        # prev_line = 'not'
        # while True:
        #     if line == prev_line:
        #         logging.info("join timeout")
        #         self.process.stdin.write("/seed\n")
        #     prev_line = line
        #     t = ThreadWithReturnValue(target=self.process.stdout.readline)
        #     t.start()
        #     line = t.join(timeout=5.0)
        #     # returnable(self.process.stdout.readline, line)
        #     # line = self.process.stdout.readline()
        #     # logging.info("print line")
        #     print(line, end='') # \n is givened when readline()
        #     if 'seed:' in line.lower():
        #         break

        # flush_loop = asyncio.to_thread(async_flush_init, self.process.stdout)
        # await asyncio.wait([asyncio.shield(flush_loop)], timeout=180)
        # x = True
        # while x:
        #     self.process.stdin.write("\seed\n")
        #     x = await asyncio.wait([asyncio.shield(flush_loop)], timeout=1)
        
        # t = ThreadWithReturnValue(target=lambda: flush_init(self.process.stdout))
        # t.start()
        # print("start initialize")
        # t.join(timeout=5)
        # raise "pass join"
        # print("waited 1 seconds")
        # x = True
        # while x:
        #     self.process.stdin.write("\seed\n")
        #     x = t.join(timeout=1)
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