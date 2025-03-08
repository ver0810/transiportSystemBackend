import random
import time
import datetime
import json
import math
from typing import List, Dict, Any

class TrafficDataGenerator:
    def __init__(self, road_network_file: str, district_file: str):
        """
        初始化交通数据生成器
        
        Args:
            road_network_file: 道路网络GeoJSON文件路径
            district_file: 行政区域GeoJSON文件路径
        """
        # 加载道路网络数据
        with open(road_network_file, 'r', encoding='utf-8-sig') as f:
            self.road_network = json.load(f)
            
        # 加载行政区域数据
        with open(district_file, 'r', encoding='utf-8-sig') as f:
            self.districts = json.load(f)
            
        # 初始化交通事件列表
        self.traffic_events = []
        self.event_id_counter = 1
        
        # 交通事件类型
        self.event_types = ["accident", "construction", "congestion", "weather"]
        
        # 位置描述模板
        self.location_templates = {
            "福田区": ["福田中心区", "华强北", "车公庙", "福田口岸", "莲花山"],
            "南山区": ["南山中心区", "科技园", "蛇口", "前海", "大学城"],
            "罗湖区": ["罗湖口岸", "东门", "笋岗", "清水河", "黄贝岭"],
            "宝安区": ["宝安中心区", "西乡", "福永", "沙井", "松岗"],
            "龙岗区": ["龙岗中心城", "坂田", "布吉", "平湖", "横岗"]
        }
        
        # 道路名称模板
        self.road_name_templates = [
            "深南大道", "北环大道", "南坪快速", "滨海大道", "龙岗大道",
            "梅观高速", "广深高速", "机荷高速", "南光高速", "水官高速"
        ]
        
        # 初始化道路流量数据
        self.road_flow_data = self._initialize_road_flow()
        
        # 初始化区域交通数据
        self.district_data = self._initialize_district_data()
        
        # 初始化一些交通事件
        self._initialize_traffic_events()
    
    def _initialize_road_flow(self) -> Dict[str, Dict]:
        """初始化道路流量数据"""
        road_flow = {}
        
        for feature in self.road_network["features"]:
            road_id = feature["properties"].get("id", str(random.randint(10000, 99999)))
            name = feature["properties"].get("name", random.choice(self.road_name_templates) if self.road_name_templates else "默认道路名称")
            
            # 根据道路等级设置基础流量和速度
            road_level = feature["properties"].get("level", random.randint(1, 5))
            base_flow = (6 - road_level) * 500 + random.randint(-200, 200)
            base_speed = (6 - road_level) * 10 + random.randint(5, 15)
            
            # 计算拥堵等级
            congestion_level = self._calculate_congestion_level(base_flow, base_speed)
            
            road_flow[road_id] = {
                "id": road_id,
                "name": name,
                "flow": base_flow,
                "speed": base_speed,
                "congestion_level": congestion_level,
                "geometry": feature["geometry"]
            }
        
        return road_flow
    
    def _initialize_district_data(self) -> Dict[str, Dict]:
        """初始化区域交通数据"""
        district_data = {}
        
        for feature in self.districts["features"]:
            district_id = feature["properties"].get("id", str(random.randint(1000, 9999)))
            name = feature["properties"].get("name", "未知区域")
            
            # 生成随机拥堵指数和流量值
            congestion_index = round(5.0 + random.random() * 4.0, 1)
            flow_value = random.randint(60, 95)
            trend = "up" if random.random() > 0.5 else "down"
            
            district_data[district_id] = {
                "id": district_id,
                "name": name,
                "congestion_index": congestion_index,
                "flow_value": flow_value,
                "trend": trend,
                "geometry": feature["geometry"]
            }
        
        return district_data
    
    def _initialize_traffic_events(self):
        """初始化一些交通事件"""
        # 生成5-10个初始交通事件
        num_events = random.randint(5, 10)
        
        for _ in range(num_events):
            self._generate_random_event()
    
    def _calculate_congestion_level(self, flow: int, speed: float) -> int:
        """根据流量和速度计算拥堵等级"""
        # 简单算法：流量越大，速度越低，拥堵等级越高
        if speed > 50:
            return 1  # 畅通
        elif speed > 30:
            return 2  # 轻度拥堵
        elif speed > 15:
            return 3  # 中度拥堵
        else:
            return 4  # 严重拥堵
    
    def _generate_random_event(self) -> Dict:
        """生成随机交通事件"""
        event_type = random.choice(self.event_types)
        
        # 随机选择一个区域和位置
        district = random.choice(list(self.location_templates.keys()))
        location_prefix = random.choice(self.location_templates[district])
        
        # 随机选择一条道路
        road = random.choice(self.road_name_templates)
        location = f"{district}{location_prefix}{road}"
        
        # 随机坐标 (深圳市大致范围)
        lng = 113.8 + random.random() * 0.5
        lat = 22.5 + random.random() * 0.3
        coordinates = [lng, lat]
        
        # 生成时间 (最近2小时内)
        minutes_ago = random.randint(0, 120)
        event_time = (datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)).strftime("%H:%M")
        
        # 根据事件类型设置状态和严重程度
        if event_type == "accident":
            status = random.choice(["处理中", "已清理"]) if random.random() > 0.7 else "处理中"
            severity = random.choice(["严重", "中度", "轻微"])
            description = random.choice([
                "多车相撞，交通严重拥堵，请绕行",
                "车辆碰撞，部分车道关闭",
                "轻微剐蹭，通行缓慢",
                "车辆故障，占用应急车道"
            ])
        elif event_type == "construction":
            status = "进行中"
            severity = random.choice(["中度", "轻微"])
            description = random.choice([
                "道路施工，部分车道关闭，通行缓慢",
                "路面维修，请减速慢行",
                "架设天桥，临时封闭部分车道",
                "管道施工，车辆绕行"
            ])
        elif event_type == "congestion":
            status = random.choice(["持续中", "已缓解"]) if random.random() > 0.7 else "持续中"
            severity = random.choice(["严重", "中度", "轻微"])
            description = random.choice([
                "交通拥堵，车辆行驶缓慢",
                "高峰期拥堵，请耐心等待",
                "车流量大，通行缓慢",
                "临近路口拥堵，请提前规划路线"
            ])
        else:  # weather
            status = "持续中"
            severity = random.choice(["严重", "中度", "轻微"])
            description = random.choice([
                "降雨天气，道路湿滑，请谨慎驾驶",
                "大雾天气，能见度低，请减速慢行",
                "强风天气，高架桥限速通行",
                "雷雨天气，部分路段积水"
            ])
        
        event = {
            "id": self.event_id_counter,
            "type": event_type,
            "location": location,
            "coordinates": coordinates,
            "time": event_time,
            "status": status,
            "severity": severity,
            "description": description
        }
        
        self.traffic_events.append(event)
        self.event_id_counter += 1
        
        return event
    
    def update_road_flow_data(self):
        """更新道路流量数据"""
        # 获取当前小时
        current_hour = datetime.datetime.now().hour
        
        # 根据时间段调整流量
        time_factor = 1.0
        if 7 <= current_hour <= 9:  # 早高峰
            time_factor = 1.5
        elif 17 <= current_hour <= 19:  # 晚高峰
            time_factor = 1.8
        elif 23 <= current_hour or current_hour <= 5:  # 深夜
            time_factor = 0.3
        elif 10 <= current_hour <= 15:  # 工作时间
            time_factor = 0.8
        
        for road_id, road_data in self.road_flow_data.items():
            # 添加随机波动
            flow_change = random.uniform(-0.15, 0.15)
            speed_change = random.uniform(-0.1, 0.1)
            
            # 更新流量和速度
            new_flow = int(road_data["flow"] * (1 + flow_change) * time_factor)
            
            # 流量与速度成反比
            speed_factor = 1.0 - (new_flow / 5000) * 0.5  # 流量越大，速度越低
            speed_factor = max(0.3, min(1.2, speed_factor))  # 限制在0.3-1.2之间
            
            new_speed = road_data["speed"] * (1 + speed_change) * speed_factor
            new_speed = max(5, min(120, new_speed))  # 限制速度范围
            
            # 更新拥堵等级
            new_congestion_level = self._calculate_congestion_level(new_flow, new_speed)
            
            # 更新数据
            self.road_flow_data[road_id]["flow"] = new_flow
            self.road_flow_data[road_id]["speed"] = round(new_speed, 1)
            self.road_flow_data[road_id]["congestion_level"] = new_congestion_level
    
    def update_district_data(self):
        """更新区域交通数据"""
        for district_id, district in self.district_data.items():
            # 添加随机波动
            congestion_change = random.uniform(-0.3, 0.3)
            flow_change = random.randint(-5, 5)
            
            # 更新拥堵指数
            new_congestion = district["congestion_index"] + congestion_change
            new_congestion = max(5.0, min(9.0, new_congestion))  # 限制在5.0-9.0之间
            
            # 更新流量值
            new_flow = district["flow_value"] + flow_change
            new_flow = max(50, min(100, new_flow))  # 限制在50-100之间
            
            # 更新趋势
            if district["congestion_index"] < new_congestion:
                trend = "up"
            else:
                trend = "down"
            
            # 更新数据
            self.district_data[district_id]["congestion_index"] = round(new_congestion, 1)
            self.district_data[district_id]["flow_value"] = new_flow
            self.district_data[district_id]["trend"] = trend
    
    def update_traffic_events(self):
        """更新交通事件"""
        # 更新现有事件状态
        for event in self.traffic_events[:]:
            # 随机决定是否更新状态
            if random.random() > 0.8:
                if event["type"] == "accident":
                    if event["status"] == "处理中" and random.random() > 0.7:
                        event["status"] = "已清理"
                elif event["type"] == "congestion":
                    if event["status"] == "持续中" and random.random() > 0.6:
                        event["status"] = "已缓解"
                elif event["type"] == "weather":
                    if random.random() > 0.9:  # 天气变化较慢
                        event["status"] = "已缓解"
            
            # 随机移除已清理或已缓解的事件
            if (event["status"] == "已清理" or event["status"] == "已缓解") and random.random() > 0.7:
                self.traffic_events.remove(event)
        
        # 随机生成新事件
        if random.random() > 0.8 and len(self.traffic_events) < 15:
            self._generate_random_event()
    
    def generate_flow_geojson(self) -> Dict:
        """生成道路流量GeoJSON数据"""
        features = []
        
        for road_id, road_data in self.road_flow_data.items():
            feature = {
                "type": "Feature",
                "properties": {
                    "id": road_id,
                    "name": road_data["name"],
                    "FLOW": road_data["flow"],
                    "SPEED": road_data["speed"],
                    "CONGESTION": road_data["congestion_level"]
                },
                "geometry": road_data["geometry"]
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def generate_events_geojson(self) -> Dict:
        """生成交通事件GeoJSON数据"""
        features = []
        
        for event in self.traffic_events:
            feature = {
                "type": "Feature",
                "properties": {
                    "id": event["id"],
                    "type": event["type"],
                    "location": event["location"],
                    "time": event["time"],
                    "status": event["status"],
                    "severity": event["severity"],
                    "description": event["description"]
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": event["coordinates"]
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def generate_district_geojson(self) -> Dict:
        """生成区域交通GeoJSON数据"""
        features = []
        
        for district_id, district in self.district_data.items():
            feature = {
                "type": "Feature",
                "properties": {
                    "id": district_id,
                    "name": district["name"],
                    "congestion_index": district["congestion_index"],
                    "flow_value": district["flow_value"],
                    "trend": district["trend"]
                },
                "geometry": district["geometry"]
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def generate_traffic_statistics(self) -> Dict:
        """生成交通统计数据"""
        # 计算总车辆数
        total_vehicles = sum(road["flow"] for road in self.road_flow_data.values())
        
        # 计算平均车速，避免除零风险
        speeds = [road["speed"] for road in self.road_flow_data.values()]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        
        # 计算高峰流量
        peak_hour_flow = max((road["flow"] for road in self.road_flow_data.values()), default=0)
        
        # 计算平均拥堵指数，避免除零风险
        congestion_indices = [district["congestion_index"] for district in self.district_data.values()]
        avg_congestion = sum(congestion_indices) / len(congestion_indices) if congestion_indices else 0
        
        # 生成区域数据
        district_data = []
        for district in self.district_data.values():
            district_data.append({
                "name": district["name"],
                "value": district["flow_value"],
                "fill": self._get_color_for_congestion(district["congestion_index"])
            })
        
        # 生成与昨日和上周的比较数据
        comparison_yesterday = round(random.uniform(-8.0, 8.0), 1)
        comparison_last_week = round(random.uniform(-8.0, 8.0), 1)
        
        return {
            "totalVehicles": total_vehicles,
            "peakHourFlow": peak_hour_flow,
            "averageSpeed": round(avg_speed, 1),
            "congestionIndex": round(avg_congestion, 1),
            "trafficEvents": len(self.traffic_events),
            "comparisonYesterday": comparison_yesterday,
            "comparisonLastWeek": comparison_last_week,
            "districtData": district_data
        }
    
    def generate_traffic_trend_data(self) -> Dict:
        """生成交通趋势数据"""
        current_hour = datetime.datetime.now().hour
        
        # 生成24小时数据
        hours_data = []
        for i in range(24):
            hour = (current_hour - 23 + i) % 24
            
            # 基础流量
            base_flow = 1000
            
            # 早高峰 (7-9点)
            if hour >= 7 and hour <= 9:
                base_flow = 2500 + random.random() * 500
            # 晚高峰 (17-19点)
            elif hour >= 17 and hour <= 19:
                base_flow = 2800 + random.random() * 500
            # 中午时段 (12-14点)
            elif hour >= 12 and hour <= 14:
                base_flow = 1800 + random.random() * 300
            # 深夜时段 (0-5点)
            elif hour >= 0 and hour <= 5:
                base_flow = 500 + random.random() * 200
            # 其他时段
            else:
                base_flow = 1200 + random.random() * 300
            
            hours_data.append({
                "hour": f"{hour}:00",
                "主干道流量": int(base_flow),
                "次干道流量": int(base_flow * 0.6),
                "支路流量": int(base_flow * 0.3)
            })
        
        return {
            "trendData": hours_data
        }
    
    def generate_prediction_data(self) -> Dict:
        """生成交通预测数据"""
        current_hour = datetime.datetime.now().hour
        
        # 生成未来24小时预测数据
        prediction_data = []
        for i in range(24):
            hour = (current_hour + i) % 24
            
            # 基础流量
            base_flow = 60
            
            # 早高峰 (7-9点)
            if hour >= 7 and hour <= 9:
                base_flow = 85 + random.random() * 10
            # 晚高峰 (17-19点)
            elif hour >= 17 and hour <= 19:
                base_flow = 90 + random.random() * 10
            # 中午时段 (12-14点)
            elif hour >= 12 and hour <= 14:
                base_flow = 70 + random.random() * 10
            # 深夜时段 (0-5点)
            elif hour >= 0 and hour <= 5:
                base_flow = 30 + random.random() * 10
            # 其他时段
            else:
                base_flow = 50 + random.random() * 15
            
            # 添加随机波动
            random_factor = random.random() * 5
            
            prediction_data.append({
                "hour": f"{hour}:00",
                "预测流量": int(base_flow + random_factor),
                "预测拥堵指数": round((base_flow + random_factor) / 20 + 3, 1)
            })
        
        return {
            "predictionData": prediction_data
        }
    
    def generate_hotspots_data(self) -> Dict:
        """生成热点区域数据"""
        hotspots = []
        
        # 使用区域数据生成热点
        for district_id, district in self.district_data.items():
            # 为每个区域生成1-2个热点
            num_hotspots = random.randint(1, 2)
            
            for i in range(num_hotspots):
                if district["name"] in self.location_templates:
                    location_prefix = random.choice(self.location_templates[district["name"]])
                else:
                    location_prefix = "中心区"
                
                congestion_level = district["congestion_index"] + random.uniform(-0.5, 0.5)
                congestion_level = max(5.0, min(9.0, congestion_level))
                
                status = "轻度拥堵"
                if congestion_level >= 8.0:
                    status = "严重拥堵"
                elif congestion_level >= 7.0:
                    status = "中度拥堵"
                
                trend = "up" if random.random() > 0.5 else "down"
                
                hotspot = {
                    "id": len(hotspots) + 1,
                    "name": f"{district['name']}{location_prefix}",
                    "congestionLevel": round(congestion_level, 1),
                    "trend": trend,
                    "status": status
                }
                
                hotspots.append(hotspot)
        
        return {
            "hotspots": hotspots
        }
    
    def _get_color_for_congestion(self, congestion_index: float) -> str:
        """根据拥堵指数获取颜色"""
        if congestion_index >= 8.0:
            return "#F44336"  # 红色
        elif congestion_index >= 7.0:
            return "#FF9800"  # 橙色
        elif congestion_index >= 6.0:
            return "#FFC107"  # 黄色
        else:
            return "#4CAF50"  # 绿色
    
    def update_all_data(self) -> Dict:
        """更新所有数据并返回完整数据包"""
        # 更新各类数据
        self.update_road_flow_data()
        self.update_district_data()
        self.update_traffic_events()
        
        # 生成完整数据包
        return {
            "timestamp": int(time.time()),
            "flowData": self.generate_flow_geojson(),
            "eventsData": self.generate_events_geojson(),
            "districtData": self.generate_district_geojson(),
            "statistics": self.generate_traffic_statistics(),
            "trendData": self.generate_traffic_trend_data(),
            "predictionData": self.generate_prediction_data(),
            "hotspotsData": self.generate_hotspots_data()
        }

""" 测试 """
# road_network_file = "/home/ancheng/Code/transiportVisualSystemProject/backend/public/road_network/road_network.geojson"
# distriction_file = "/home/ancheng/Code/transiportVisualSystemProject/backend/public/distriction/440300.json"
# trafficGreateror = TrafficDataGenerator(road_network_file, distriction_file)

# data = trafficGreateror.update_all_data()
# with open('flowData.json', 'w', encoding='utf-8') as f:
#     json.dump(data['flowData'], f, ensure_ascii=False, indent=4)

# with open('eventsData.json', 'w', encoding='utf-8') as f:
#     json.dump(data['eventsData'], f, ensure_ascii=False, indent=4)

# with open('districtData.json', 'w', encoding='utf-8') as f:
#     json.dump(data['districtData'], f, ensure_ascii=False, indent=4)

# with open('statistics.json', 'w', encoding='utf-8') as f:
#     json.dump(data['statistics'], f, ensure_ascii=False, indent=4)

#     json.dump(data['trendData'], f, ensure_ascii=False, indent=4)

# with open('predictionData.json', 'w', encoding='utf-8') as f:
#     json.dump(data['predictionData'], f, ensure_ascii=False, indent=4)

# with open('hotspotsData.json', 'w', encoding='utf-8') as f:
#     json.dump(data['hotspotsData'], f, ensure_ascii=False, indent=4)
