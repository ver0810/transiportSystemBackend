import asyncio
import pandas as pd
import logging
import time
from services.websocket.manager import manager
from services.road.simulatieFlow import simulate_flow
from services.road.geoservice import generate_road_with_flow
import random

logger = logging.getLogger(__name__)

# 全局变量，存储任务状态
flow_update_task = None
is_running = False

async def update_flow_data(interval_seconds: int = 5):
    """
    定时更新流量数据并通过 WebSocket 广播
    
    Args:
        interval_seconds: 更新间隔时间（秒）
    """
    global is_running
    is_running = True
    
    try:
        while is_running:
            start_time = time.time()
            logger.info(f"Updating flow data at {time.strftime('%H:%M:%S')}")
            
            try:
                # 获取原始数据
                road_speed = pd.read_csv('public/road_speed.csv')
                
                # 如果没有 FLOW 列，先计算它
                if 'FLOW' not in road_speed.columns:
                    road_speed['FLOW'] = road_speed['GOLEN'] / road_speed['GOTIME']
                
                # 模拟新的流量数据
                updated_road_speed = simulate_flow(road_speed)
                
                # 获取完整的道路网络数据（包含新的流量）
                # 直接传递数据，避免文件 I/O 操作
                updated_geo_data = generate_road_with_flow(updated_road_speed)
                
                # 转换为可序列化的格式
                geo_data_dict = updated_geo_data.__geo_interface__
                
                # 添加时间戳
                message = {
                    "type": "flow_update",
                    "timestamp": time.time(),
                    "data": geo_data_dict
                }
                
                # 广播到所有客户端
                await manager.broadcast(message)
                logger.info(f"Flow data broadcast to {len(manager.active_connections)} clients")
                    
            except Exception as e:
                logger.error(f"Error updating flow data: {e}")
            
            # 计算实际需要睡眠的时间
            elapsed = time.time() - start_time
            sleep_time = max(0, interval_seconds - elapsed)
            
            await asyncio.sleep(sleep_time)
    
    finally:
        is_running = False
        logger.info("更新流量数据任务结束")


def start_flow_updates(interval_seconds: int = 5):
    """启动流量数据更新任务"""
    global flow_update_task, is_running
    
    if flow_update_task is not None and not flow_update_task.done():
        logger.warning("流量更新任务已经在运行")
        return
    
    logger.info(f"流量更新任务已经运行 {interval_seconds} 秒")
    flow_update_task = asyncio.create_task(update_flow_data(interval_seconds))
    return flow_update_task


def stop_flow_updates():
    """停止流量数据更新任务"""
    global flow_update_task, is_running
    
    if flow_update_task is None or flow_update_task.done():
        logger.warning("No flow update task is running")
        return
    
    logger.info("Stopping flow update task")
    is_running = False
    # 不要取消任务，让它自然结束
    return flow_update_task