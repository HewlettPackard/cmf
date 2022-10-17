from fastapi import FastAPI,Request

app = FastAPI()


@app.get("/")
def read_root():
    return {"Use this api for sending json payload":"http://127.0.0.1:8000/mlmd/"}


@app.post("/mlmd")
async def sendmlmd(info: Request):
    req_info=await info.json()

    return{
        'status':'success',
        'data':req_info
    }

