from fastapi import WebSocket
from typing import List, Dict
import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_data = None  # 存储最后一次发送的数据
        self.connection_count = 0  # 添加连接计数器
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"服务已连接, 总连接次数 {self.connection_count}")
        
        # 如果有最新数据，立即发送给新连接的客户端
        if self.last_data:
            await self.send_personal_message(self.last_data, websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"已断开连接, 总连接次数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送个人信息错误: {e}")
            # 如果发送失败，可能客户端已断开
            if websocket in self.active_connections:
                self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        # 存储最后发送的数据
        self.last_data = message
        
        # 创建断开连接的列表
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播信息错误: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        for connection in disconnected:
            if connection in self.active_connections:
                self.disconnect(connection)
    
    async def heartbeat(self):
        """发送心跳以保持连接"""
        while True:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json({"type": "heartbeat", "timestamp": time.time()})
                except Exception:
                    disconnected.append(connection)
            
            # 断开失败的连接
            for connection in disconnected:
                self.disconnect(connection)
                
            await asyncio.sleep(30)  # 30秒一次心跳


# 全局连接管理器实例
manager = ConnectionManager()