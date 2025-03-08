from os import name
from venv import create
from weakref import ref
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):

    __tablename__ = "users"  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(min_length=3, max_length=20)
    hashedPassword: str

class RoadNetwork(SQLModel, table=True):
    __tablename__ = "roads"  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    geometry: str  # WKT 格式
    created_at: str


# 道路流量数据模型
class RoadFlowData:
    def __init__(self, road_id, name, coordinates, flow, speed, congestion_level):
        self.road_id = road_id  # 道路ID
        self.name = name  # 道路名称
        self.coordinates = coordinates  # 道路坐标点列表 [[lng1, lat1], [lng2, lat2], ...]
        self.flow = flow  # 交通流量
        self.speed = speed  # 平均车速
        self.congestion_level = congestion_level  # 拥堵等级 (1-4: 畅通、轻度拥堵、中度拥堵、严重拥堵)

# 交通事件数据模型
class TrafficEvent:
    def __init__(self, event_id, event_type, location, coordinates, time, status, severity, description):
        self.event_id = event_id  # 事件ID
        self.event_type = event_type  # 事件类型 (accident, construction, congestion, weather)
        self.location = location  # 位置描述
        self.coordinates = coordinates  # 事件坐标 [lng, lat]
        self.time = time  # 事件发生时间
        self.status = status  # 事件状态
        self.severity = severity  # 严重程度
        self.description = description  # 事件描述

# 区域交通数据模型
class DistrictTrafficData:
    def __init__(self, district_id, name, boundary, congestion_index, flow_value, trend):
        self.district_id = district_id  # 区域ID
        self.name = name  # 区域名称
        self.boundary = boundary  # 区域边界坐标
        self.congestion_index = congestion_index  # 拥堵指数
        self.flow_value = flow_value  # 流量值
        self.trend = trend  # 趋势 (up/down)