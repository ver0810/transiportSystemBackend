from sqlmodel import Session
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from app.database import getSession
from app.crud import createUser, updateUsername, updatePassword, getUserByUsername
from app.schemas import LoginUser, PasswordUpdateRequest, RegisterUser, UsernameUpdateRequest
from services.auth.login import authenticateUser
from app.crud import ACCESS_TOKEN_EXPIRE_MINUTES, createAccessToken
from services.websocket.flow_update import start_flow_updates, stop_flow_updates
import asyncio
import logging
from typing import List, Dict, Any
import time
from services.data.TrafficDataGenerate import TrafficDataGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

app = FastAPI(title="深圳交通可视化系统后端")

# CORS 同源策略
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://192.168.1.*",  # 允许本地网络访问
    "https://your-production-domain.com",  # 如果需要，添加生产域名
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量用于控制定时更新任务
update_interval = 60  # 默认10秒更新一次
background_task = None
is_updating = False

# 注册路由
@app.post("/user/register")
def createNewUser(user: RegisterUser, db: Session = Depends(getSession)):
    try:
        result = createUser(db, user)
        return {
            "message": "User registered successfully", 
            "username": result.username,
            "id": result.id
        }
    except HTTPException as e:
        # FastAPI会自动处理HTTPException
        raise e
    except Exception as e:
        logging.error(f"注册用户时出现未知错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )

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


# 修改用户名路由
@app.post("/user/update-username")
def update_username(request: UsernameUpdateRequest, db: Session = Depends(getSession)):
    try:
        result = updateUsername(db, request.current_username, request.new_username)
        return {
            "message": "Username updated successfully",
            "username": result.username,
            "id": result.id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"修改用户名时出现未知错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )

# 修改密码路由
@app.post("/user/update-password")
def update_password(request: PasswordUpdateRequest, db: Session = Depends(getSession)):
    try:
        result = updatePassword(db, request.username, request.current_password, request.new_password)
        return {
            "message": "Password updated successfully",
            "username": result.username,
            "id": result.id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"修改密码时出现未知错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )

# 获取用户信息路由
@app.get("/user/info")
def get_user_info(username: str, db: Session = Depends(getSession)):
    try:
        user = getUserByUsername(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {
            "username": user.username,
            "id": user.id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"获取用户信息时出现未知错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}"
        )

# 手动控制流量更新任务的端点
@app.post("/admin/flow_updates/start")
async def start_updates(interval_seconds: int = 10):
    """启动流量更新任务"""
    global update_interval, is_updating
    update_interval = interval_seconds
    
    if not is_updating:
        # 启动后台任务
        background_task = asyncio.create_task(periodic_data_update())
        is_updating = True
        logging.info(f"流量更新任务已启动，更新间隔为 {interval_seconds} 秒")
    else:
        logging.info(f"更新间隔已修改为 {interval_seconds} 秒")
    
    return {"message": f"流量更新任务已启动，更新间隔为 {interval_seconds} 秒"}

@app.post("/admin/flow_updates/stop")
async def stop_updates():
    """停止流量更新任务"""
    global is_updating
    
    if is_updating:
        is_updating = False
        logging.info("流量更新任务已停止")
    
    return {"message": "流量更新任务已停止"}

# 初始化数据生成器
data_generator = TrafficDataGenerator(
    road_network_file="public/road_network/shenzhen_road.geojson",
    district_file="public/distriction/440300.json"
)

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "road_flow": [],
            "traffic_events": [],
            "district_data": [],
            "statistics": [],
            "trend_data": [],
            "prediction_data": [],
            "hotspots_data": [],
            "all_data": []
        }
    
    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        if (client_type in self.active_connections):
            self.active_connections[client_type].append(websocket)
            logging.info(f"{client_type} 客户端连接成功，当前连接数: {len(self.active_connections[client_type])}")
        else:
            logging.warning(f"未知的客户端类型: {client_type}")
    
    def disconnect(self, websocket: WebSocket, client_type: str):
        if client_type in self.active_connections and websocket in self.active_connections[client_type]:
            self.active_connections[client_type].remove(websocket)
            logging.info(f"{client_type} 客户端断开连接，当前连接数: {len(self.active_connections[client_type])}")
    
    async def broadcast(self, client_type: str, message: Dict[str, Any]):
        """向特定类型的所有连接客户端广播消息"""
        if client_type not in self.active_connections:
            logging.warning(f"未知的客户端类型: {client_type}")
            return
        
        disconnected = []
        for connection in self.active_connections[client_type]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"发送消息失败: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        for conn in disconnected:
            self.disconnect(conn, client_type)

# 只定义一次manager实例
manager = ConnectionManager()

# 定期更新和广播数据的后台任务
async def periodic_data_update():
    """定期更新和广播交通数据"""
    global is_updating, update_interval
    
    logging.info(f"开始定期更新数据，间隔：{update_interval}秒")
    
    while is_updating:
        try:
            start_time = time.time()
            logging.info(f"正在更新交通数据...")
            
            # 更新所有数据
            all_data = data_generator.update_all_data()
            timestamp = int(time.time())
            
            # 广播道路流量数据
            if manager.active_connections["road_flow"]:
                flow_data = {
                    "timestamp": timestamp,
                    "data": data_generator.generate_flow_geojson()
                }
                await manager.broadcast("road_flow", flow_data)
            
            # 广播交通事件数据
            if manager.active_connections["traffic_events"]:
                events_data = {
                    "timestamp": timestamp,
                    "data": data_generator.generate_events_geojson()
                }
                await manager.broadcast("traffic_events", events_data)
            
            # 广播区域数据
            if manager.active_connections["district_data"]:
                district_data = {
                    "timestamp": timestamp,
                    "data": data_generator.generate_district_geojson()
                }
                await manager.broadcast("district_data", district_data)
            
            # 广播统计数据
            if manager.active_connections["statistics"]:
                statistics_data = {
                    "timestamp": timestamp,
                    "data": data_generator.generate_traffic_statistics()
                }
                await manager.broadcast("statistics", statistics_data)
            
            # 广播趋势数据
            if manager.active_connections["trend_data"]:
                trend_data = {
                    "timestamp": timestamp,
                    "data": data_generator.generate_traffic_trend_data()
                }
                await manager.broadcast("trend_data", trend_data)
            
            # 广播预测数据
            if manager.active_connections["prediction_data"]:
                prediction_data = {
                    "timestamp": timestamp,
                    "data": data_generator.generate_prediction_data()
                }
                await manager.broadcast("prediction_data", prediction_data)
            
            # 广播热点数据
            if manager.active_connections["hotspots_data"]:
                hotspots_data = {
                    "timestamp": timestamp,
                    "data": data_generator.generate_hotspots_data()
                }
                await manager.broadcast("hotspots_data", hotspots_data)
            
            # 广播所有数据
            if manager.active_connections["all_data"]:
                await manager.broadcast("all_data", all_data)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 确保间隔时间是准确的
            sleep_time = max(0.1, update_interval - processing_time)
            logging.info(f"数据更新完成，处理时间：{processing_time:.2f}秒，将在{sleep_time:.2f}秒后再次更新")
            
            # 等待一段时间再更新
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            logging.error(f"更新数据时出错: {e}")
            await asyncio.sleep(5)  # 出错后等待5秒再重试

# WebSocket路由
@app.websocket("/ws/road_flow")
async def websocket_road_flow(websocket: WebSocket):
    await manager.connect(websocket, "road_flow")
    try:
        # 发送初始数据
        initial_data = {
            "timestamp": int(time.time()),
            "data": data_generator.generate_flow_geojson()
        }
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            # 接收客户端消息（可选）
            data = await websocket.receive_text()
            # 这里可以处理客户端发送的消息
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "road_flow")

@app.websocket("/ws/traffic_events")
async def websocket_traffic_events(websocket: WebSocket):
    await manager.connect(websocket, "traffic_events")
    try:
        # 发送初始数据
        initial_data = {
            "timestamp": int(time.time()),
            "data": data_generator.generate_events_geojson()
        }
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "traffic_events")

@app.websocket("/ws/district_data")
async def websocket_district_data(websocket: WebSocket):
    await manager.connect(websocket, "district_data")
    try:
        # 发送初始数据
        initial_data = {
            "timestamp": int(time.time()),
            "data": data_generator.generate_district_geojson()
        }
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "district_data")

@app.websocket("/ws/statistics")
async def websocket_statistics(websocket: WebSocket):
    await manager.connect(websocket, "statistics")
    try:
        # 发送初始数据
        initial_data = {
            "timestamp": int(time.time()),
            "data": data_generator.generate_traffic_statistics()
        }
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "statistics")

@app.websocket("/ws/trend_data")
async def websocket_trend_data(websocket: WebSocket):
    await manager.connect(websocket, "trend_data")
    try:
        # 发送初始数据
        initial_data = {
            "timestamp": int(time.time()),
            "data": data_generator.generate_traffic_trend_data()
        }
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "trend_data")

@app.websocket("/ws/prediction_data")
async def websocket_prediction_data(websocket: WebSocket):
    await manager.connect(websocket, "prediction_data")
    try:
        # 发送初始数据
        initial_data = {
            "timestamp": int(time.time()),
            "data": data_generator.generate_prediction_data()
        }
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "prediction_data")

@app.websocket("/ws/hotspots_data")
async def websocket_hotspots_data(websocket: WebSocket):
    await manager.connect(websocket, "hotspots_data")
    try:
        # 发送初始数据
        initial_data = {
            "timestamp": int(time.time()),
            "data": data_generator.generate_hotspots_data()
        }
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "hotspots_data")

@app.websocket("/ws/all_data")
async def websocket_all_data(websocket: WebSocket):
    await manager.connect(websocket, "all_data")
    try:
        # 发送初始数据
        initial_data = data_generator.update_all_data()
        await websocket.send_json(initial_data)
        
        # 保持连接
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "all_data")

# HTTP路由，用于获取初始数据
@app.get("/get_road_flow")
async def get_road_flow():
    try:
        return data_generator.generate_flow_geojson()
    except Exception as e:
        logging.error(f"获取道路流量数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取道路流量数据失败")

@app.get("/get_traffic_events")
async def get_traffic_events():
    try:
        return data_generator.generate_events_geojson()
    except Exception as e:
        logging.error(f"获取交通事件数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取交通事件数据失败")

@app.get("/get_district_data")
async def get_district_data():
    try:
        return data_generator.generate_district_geojson()
    except Exception as e:
        logging.error(f"获取区域数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取区域数据失败")

@app.get("/get_statistics")
async def get_statistics():
    try:
        return data_generator.generate_traffic_statistics()
    except Exception as e:
        logging.error(f"获取统计数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")

@app.get("/get_trend_data")
async def get_trend_data():
    try:
        return data_generator.generate_traffic_trend_data()
    except Exception as e:
        logging.error(f"获取趋势数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取趋势数据失败")

@app.get("/get_prediction_data")
async def get_prediction_data():
    try:
        return data_generator.generate_prediction_data()
    except Exception as e:
        logging.error(f"获取预测数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取预测数据失败")

@app.get("/get_hotspots_data")
async def get_hotspots_data():
    try:
        return data_generator.generate_hotspots_data()
    except Exception as e:
        logging.error(f"获取热点数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取热点数据失败")

@app.get("/get_all_data")
async def get_all_data():
    try:
        return data_generator.update_all_data()
    except Exception as e:
        logging.error(f"获取所有数据时出错: {e}")
        raise HTTPException(status_code=500, detail="获取所有数据失败")

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": int(time.time()), "is_updating": is_updating, "update_interval": update_interval}

# 在应用启动时自动开始数据更新任务
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化工作"""
    global is_updating
    
    # 自动启动数据更新任务
    if not is_updating:
        is_updating = True
        asyncio.create_task(periodic_data_update())
        logging.info(f"应用启动时自动开始数据更新任务，间隔：{update_interval}秒")

@app.on_event("shutdown") 
async def shutdown_event():
    """应用关闭时的清理工作"""
    global is_updating
    
    # 停止数据更新任务
    is_updating = False
    logging.info("应用关闭，停止数据更新任务")