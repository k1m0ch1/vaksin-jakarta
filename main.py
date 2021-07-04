import uvicorn

from fastapi import FastAPI
from routes import root

app = FastAPI()

app.include_router(root.root)

if __name__ == '__main__':
    uvicorn.run('main:app', host='127.0.0.1', port=8010, log_level="info", reload=True)