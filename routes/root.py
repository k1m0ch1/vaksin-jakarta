import json
from fastapi import APIRouter

root = APIRouter()

@root.get("/")
async def index():
    f = open("jadwal.json", "r")
    data = json.loads(f.read())
    return data
