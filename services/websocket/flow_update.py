import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 用于控制更新任务的变量
_update_task: Optional[asyncio.Task] = None
_is_running = False
_update_interval = 5  # 默认60秒

async def _update_loop():
    """后台更新循环"""
    global _is_running
    
    logger.info(f"流量更新任务已启动，间隔: {_update_interval}秒")
    
    while _is_running:
        try:
            # 这里只记录日志，实际更新由main.py中的periodic_data_update处理
            logger.debug(f"服务更新间隔为: {_update_interval}秒")
            await asyncio.sleep(_update_interval)
            
        except Exception as e:
            logger.error(f"更新循环出错: {e}")
            await asyncio.sleep(5)  # 出错后等待5秒

def start_flow_updates(interval_seconds: int = 60):
    """启动流量更新任务"""
    global _update_task, _is_running, _update_interval
    
    if _is_running:
        logger.info(f"更新任务已在运行中，更新间隔: {interval_seconds}秒")
        _update_interval = interval_seconds
        return
    
    _update_interval = interval_seconds
    _is_running = True
    _update_task = asyncio.create_task(_update_loop())
    
    logger.info(f"流量更新任务已启动，间隔: {interval_seconds}秒")

def stop_flow_updates():
    """停止流量更新任务"""
    global _update_task, _is_running
    
    if not _is_running:
        logger.info("流量更新任务未运行")
        return
    
    _is_running = False
    if _update_task:
        _update_task.cancel()
        _update_task = None
    
    logger.info("流量更新任务已停止")

def get_update_status():
    """获取更新任务状态"""
    return {
        "is_running": _is_running,
        "interval": _update_interval
    }