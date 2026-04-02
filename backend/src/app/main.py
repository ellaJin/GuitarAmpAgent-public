from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.devices import router as device_router
from app.routers.google import router as google_router
from app.routers.chat import router as chat_router
from app.routers.jobs import router as jobs_router
from app.routers.admin_device import router as admin_router
from app.routers.conversations import router as conversations_router
from app.routers.songs import router as songs_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Guitar Effects Agent API")

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(device_router)
app.include_router(google_router)
app.include_router(chat_router)
app.include_router(jobs_router)
app.include_router(admin_router)
app.include_router(conversations_router)
app.include_router(songs_router)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
