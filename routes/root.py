import json
from fastapi import APIRouter

root = APIRouter()


@root.get("/")
async def index(start: int = 0, end: int = -1):
    f = open("jadwal.json", "r")
    data = json.loads(f.read())[start:end]
    return data
