from fastapi import FastAPI,Request
from server.app.mlmd import merge_mlmd

app = FastAPI()


@app.get("/")
def read_root():
    return {"Use this api for sending json payload":"http://127.0.0.1:8000/mlmd_push/"}


@app.post("/mlmd_push")
async def mlmd_push(info: Request):
    req_info=await info.json()
    merge_mlmd(req_info)

    return{
        'status':'success',
        'data':req_info
    }

