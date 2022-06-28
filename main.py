from subprocess import Popen, PIPE, STDOUT
from typing import Union
from fastapi import FastAPI
from fastapi_utils.cbv import cbv 
from fastapi_utils.inferring_router import InferringRouter
import json
from utils import Sopen, MinecraftServer
import os


app = FastAPI()
router = InferringRouter()

@app.get("/machine")
async def status():
    return {"message": "online"}


@cbv(router)
class ServerManager:
    server_session = None
    server_name: Union[str, None] = None
    with open("config.json", "r") as f:
        config = json.load(f)
    server_config = config['servers']

    @router.get("/server/list")
    # @staticmethod
    async def get_list(self):
        return list(ServerManager.server_config.keys())

    @router.get("/server")
    # @staticmethod
    async def get_status(self):
        if ServerManager.server_session is None:
            return {"message": "offline"}
        else:
            return {"message": "online", "server_name": ServerManager.server_name}
    
    # async def status(self):
    #     if ServerManager.server_session is None:
    #         return {"message": "offline"}
    #     else:
    #         return {"message": "online", "server_name": ServerManager.server_name}

    @router.get("/server/start")
    # @staticmethod
    async def start(self, server: str):
        if ServerManager.server_session is not None:
            return {"message": 
            """there's already running server""", 
            "server_name": ServerManager.server_name}
        _dir = ServerManager.server_config[server]['destination']
        os.chdir(_dir)
        if 'minecraft' in _dir:
            ServerManager.server_session = MinecraftServer(ServerManager.server_config[server]['cmd'])
        else:
            ServerManager.server_session = Sopen(ServerManager.server_config[server]['cmd'])
        ServerManager.server_name = server
        ServerManager.server_session.join_no_response()
        x = ServerManager.server_session.communicate("/list")
        if bool(x):
            return {"message": "start server successfully", "exit_code": 0}
        ServerManager.server_session.kill()
        ServerManager.server_session = None
        return {"message": "there is something wrong", "exit_code": 1}

    @router.get("/server/stop")
    # @staticmethod
    async def stop(self):
        if ServerManager.server_session is None:
            return {"message": "server is offline", "exit_code": 0}
        ServerManager.server_session.kill()
        ServerManager.server_session = None
        return {"messgae": "server have been stopped", "exit_code": 0}


# app.get('/server', ServerManager.get_status)
# app.get('/server/list', ServerManager.get_list)
# app.get('/server/start', ServerManager.start)
# app.get('/server/stop', ServerManager.stop)

app.include_router(router)
# server status
# server start
# server stop
