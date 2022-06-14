from subprocess import Popen, PIPE, STDOUT
from fastapi import FastAPI



app = FastAPI()

server_list = ['rlcraft', 'minecraft']

@app.get("/machine")
async def status():
    return {"message": "online"}


@app.get("/servers")
async def get_server_list():
    return server_list


@app.get("/servers")
async def release():
    return {"message": "undefined"}

