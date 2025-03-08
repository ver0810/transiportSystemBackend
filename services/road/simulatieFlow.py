import pandas as pd
import numpy as np
from sklearn.neighbors import KernelDensity


def simulate_flow(data: pd.DataFrame):
    """
    根据道路速度数据生成合成数据
    Note: data 必须包含 'FLOW' 列
    """
    # 删除缺失值
    data = data.dropna(subset=["FLOW"])
    X = data[["FLOW"]].values

    # 对数值列进行核密度估计
    kde = KernelDensity(kernel="gaussian", bandwidth=0.5)
    kde.fit(X)

    # 生成新的 FLOW 数据
    n_samples = len(data)  # 保持与原始数据相同的行数
    new_flows = kde.sample(n_samples=n_samples).flatten()

    # 创建新的数据集，复制原始数据的所有列
    new_dataset = data.copy()

    # 更新 FLOW 列
    new_dataset["FLOW"] = new_flows
    
    return new_dataset
