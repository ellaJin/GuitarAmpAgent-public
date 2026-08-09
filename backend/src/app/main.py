import logging
import json
import time
import sys
import types as _types

# ragas==0.4.3 imports langchain_community.chat_models.vertexai at module load
# time, but langchain-community>=0.3 removed that module. Stub it so the import
# doesn't blow up before we ever call any VertexAI code.
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _pkg = sys.modules.setdefault(
        "langchain_community.chat_models",
        _types.ModuleType("langchain_community.chat_models"),
    )
    _stub = _types.ModuleType("langchain_community.chat_models.vertexai")
    _stub.ChatVertexAI = type("ChatVertexAI", (), {})  # type: ignore[assignment]
    sys.modules["langchain_community.chat_models.vertexai"] = _stub

from fastapi import FastAPI, Request
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.devices import router as device_router
from app.routers.google import router as google_router
from app.routers.chat import router as chat_router
from app.routers.jobs import router as jobs_router
from app.routers.admin_device import router as admin_router
from app.routers.admin_eval import router as admin_eval_router
from app.routers.conversations import router as conversations_router
from app.routers.songs import router as songs_router
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("http_access")

app = FastAPI(title="Guitar Effects Agent API")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": request.method,
        "endpoint": request.url.path,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
    }))
    return response


from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(device_router)
app.include_router(google_router)
app.include_router(chat_router)
app.include_router(jobs_router)
app.include_router(admin_router)
app.include_router(admin_eval_router)
app.include_router(conversations_router)
app.include_router(songs_router)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    settings.FRONTEND_URL,
]
origins = list(dict.fromkeys(origins))  # de-dupe -- FRONTEND_URL defaults to a value already in this list

# frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
