from sqlmodel import Session
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from app.database import getSession
from app.crud import createUser
from app.database import getSession
from app.schemas import LoginUser, RegisterUser
from services.auth.login import authenticateUser
from app.crud import ACCESS_TOKEN_EXPIRE_MINUTES, createAccessToken
from services.road.geoservice import generate_road_with_flow
from services.websocket.flow_update import start_flow_updates, stop_flow_updates
from services.websocket.manager import manager

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

app = FastAPI()

# CORS 同源策略
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动事件
@app.on_event("startup")
def startup_event():
    # 启动流量更新任务，默认每10秒更新一次
    start_flow_updates(interval_seconds=60)

# 停止事件
@app.on_event("shutdown")
def shutdown_event():
    # 停止流量更新任务
    stop_flow_updates()

# WebSocket 端点
@app.websocket("/ws/road_flow")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃，等待客户端消息
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# 注册路由
@app.post("/user/register")
def createNewUser(user: RegisterUser, db: Session = Depends(getSession)):
    createUser(db, user)
    return {"message": "User registered successfully"}

# 登录路由
@app.post("/user/login")
def login(loginUser: LoginUser, db: Session = Depends(getSession)):
    user = authenticateUser(db, loginUser.username, loginUser.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    accessTokenExpires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    accessToken = createAccessToken(
        data={"sub": user.username}, expiresDelta=accessTokenExpires
    )
    return accessToken

@app.get("/get_road_flow")
def get_road_flow():
    """获取道路网络流量数据"""
    try:
        geo_data = generate_road_with_flow()
        return geo_data.__geo_interface__
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取路网流量数据失败: {str(e)}")

# 手动控制流量更新任务的端点
@app.post("/admin/flow_updates/start")
def start_updates(interval_seconds: int = 10):
    """启动流量更新任务"""
    start_flow_updates(interval_seconds)
    return {"message": f"流量更新任务已启动，更新间隔为 {interval_seconds} 秒"}

@app.post("/admin/flow_updates/stop")
def stop_updates():
    """停止流量更新任务"""
    stop_flow_updates()
    return {"message": "流量更新任务已停止"}
