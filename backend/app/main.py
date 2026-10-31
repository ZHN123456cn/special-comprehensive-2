from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.database import Base, engine
from app.routers import auth, games

app = FastAPI(title="小游戏自动生成平台 API", version="1.0.0")

# 跨域配置（开发阶段允许前端 Vite 访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(games.router)


@app.on_event("startup")
def on_startup():
    # 开发阶段自动建表（生产建议用 Alembic 迁移）
    Base.metadata.create_all(bind=engine)


@app.get("/api/health", summary="健康检查")
def health():
    return {"status": "ok"}
