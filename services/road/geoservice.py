from geopandas import GeoDataFrame
import osmnx as ox
import pandas as pd
from pyogrio import read_info


# 从网络获取道路网络
def get_road_network_from_osmnx(place_name="Futian, Shenzhen, China"):
    G = ox.graph_from_place(place_name, network_type="drive")
    edges = ox.graph_to_gdfs(G, nodes=False)
    return edges

# 从本地获取道路网络
def get_road_network_from_location():
    G = ox.load_graphml('public/road_network/Shenzhen.graphml')
    edges = ox.graph_to_gdfs(G, nodes=False)
    return edges

# 提取道路网络
def extract_road_network(road_info, road_network):
    new_road_mask = merge_road_network(road_info, road_network)
    new_road = new_road_mask[['osmid', 'name', 'geometry', 'length', 'lanes']]
    return new_road


# 根据road_info中name字段合并道路
def merge_road_network(road_info, edges):
    new_road_mask = edges["name"].isin(road_info["ROADSECT_NAME"])
    new_road = edges[new_road_mask]
    return new_road

# 为路网添加ROADSECT_ID
def add_roadsect_id(road_info, road_network):
    # 创建一个字典，存储道路名称与 ROADSECT_ID 的映射
    road_to_sect_id = {}

    # 遍历道路段数据，构建映射
    for _, row in road_info.iterrows():
        road_to_sect_id[row["ROADSECT_FROM"]] = row["ROADSECT_ID"]
        road_to_sect_id[row["ROADSECT_TO"]] = row["ROADSECT_ID"]

    print(len(road_to_sect_id))
    # 为路网数据添加 ROADSECT_ID
    road_network["ROADSECT_ID"] = road_network["name"].map(road_to_sect_id)
    road_network = road_network.dropna(subset=["ROADSECT_ID"])
    road_network["ROADSECT_ID"] = road_network["ROADSECT_ID"].astype(int)
    return road_network


# 为路网添加FLOW
def add_flow(road_speed, road_network):
    road_speed['FLOW'] = road_speed['GOLEN'] / road_speed['GOTIME']
    merge_datasets = pd.merge(
        road_network, road_speed[["ROADSECT_ID", "FLOW"]], on="ROADSECT_ID", how="left"
    )
    return merge_datasets


def generate_road_with_flow(road_speed_data=None):
    road_network = get_road_network_from_location()
    road_info = pd.read_csv('public/road_info.csv')
    
    # 允许传入 road_speed 数据
    if road_speed_data is None:
        road_speed = pd.read_csv('public/road_speed.csv')
    else:
        road_speed = road_speed_data
    
    new_network = extract_road_network(road_info, road_network)
    new_network = add_roadsect_id(road_info, new_network)
    new_network = add_flow(road_speed, new_network)
    
    return new_network
