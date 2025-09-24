# 天气与环境参数综合服务 - API文档

## 概述

本服务提供全球任意坐标点的实时天气数据和14个关键环境参数。它整合了Open-Meteo天气API和Google Earth Engine的多源卫星数据集，为环境监测、农业、科研等领域提供全面的数据支持。

**服务地址**: `http://localhost:8081`

---

## 核心功能

- **实时天气**: 获取当前温度、湿度、气压、风速等信息。
- **环境参数**: 获取植被指数（NDVI, EVI, SAVI）、叶面积指数（LAI）、地表温度（LST）、反照率（Albedo）等14个关键参数。
- **高分辨率数据**: 结合Sentinel-2（10米分辨率）和MODIS（500米-1公里分辨率）数据。
- **多功能API**: 提供多个端点以满足不同需求，从简单查询到综合数据获取。

---

## 主要API端点

### 1. 获取14个环境参数

这是获取植被和环境参数的核心端点。

- **URL**: `/api/environmental_parameters`
- **方法**: `POST`
- **描述**: 输入经纬度坐标，获取过去30天内最新的14个环境参数。

#### 请求体 (JSON)
```json
{
  "latitude": 39.9042,
  "longitude": 116.4074,
  "days_back": 30
}
```
- **参数说明**:
  - `latitude` (float, 必选): 纬度 (-90 to 90)
  - `longitude` (float, 必选): 经度 (-180 to 180)
  - `days_back` (int, 可选, 默认: 30): 查询过去的天数范围

#### 示例请求 (`curl`)
```bash
curl -X POST http://localhost:8081/api/environmental_parameters \
-H "Content-Type: application/json" \
-d '{
  "latitude": 39.9042,
  "longitude": 116.4074
}'
```

#### 成功响应 (JSON)
```json
{
  "status": "success",
  "location": { "latitude": 39.9042, "longitude": 116.4074 },
  "summary": {
    "total_parameters": 14,
    "available_parameters": 12,
    "success_rate": "85.7%",
    "missing_parameters": ["LWNR (净长波辐射)", "NR (净辐射)"]
  },
  "target_parameters": {
    "LAI": 0.87,
    "FAPAR": 0.75,
    "FVC": 0.65,
    "Albedo": 0.15,
    "BBE": 0.98,
    "DSR": 250.5,
    "PAR": 120.3,
    "LST": { "day": 25.4, "night": 15.2 },
    "ET": 3.4,
    "GPP": 1.2,
    "SCE": 0,
    "AGB": 1500.5,
    "LWNR": null,
    "NR": null
  },
  "parameter_descriptions": {
      "LAI": "叶面积指数 (m²/m²)",
      "FAPAR": "光合有效辐射吸收率 (0-1)",
       ...
  },
  "query_time": "2025-01-20 10:30:00"
}
```

---

### 2. 获取天气和植被综合数据

- **URL**: `/api/all`
- **方法**: `POST`
- **描述**: 一次性获取天气和所有环境参数的详细原始数据。

#### 请求体 (JSON)
```json
{
  "latitude": 39.9042,
  "longitude": 116.4074
}
```

#### 示例请求 (`curl`)
```bash
curl -X POST http://localhost:8081/api/all \
-H "Content-Type: application/json" \
-d '{"latitude": 39.9042, "longitude": 116.4074}'
```

#### 成功响应 (JSON)
```json
{
  "status": "success",
  "location": { "latitude": 39.9042, "longitude": 116.4074 },
  "weather": {
    "current": {
      "temperature": 22.5,
      "humidity": 65,
      "pressure": 1012.5,
      "description": "晴朗",
      ...
    }
  },
  "vegetation": {
    "sentinel2_data": {
        "NDVI": 0.8,
        ...
    },
    "modis_data": {
        "LAI": 0.87,
        ...
    },
    "estimated_values": {
        "FVC": 0.65,
        ...
    },
    ...
  },
  "query_time": "2025-01-20 10:30:00"
}
```

---

### 3. 其他API端点

- **`/api/weather` (POST)**: 仅获取天气数据。
- **`/api/vegetation` (POST)**: 仅获取植被参数的详细数据。
- **`/api/simple` (GET)**: 简单测试接口，`?lat=39.9&lon=116.4`。
- **`/api/status` (GET)**: 检查API和依赖服务的状态。
- **`/health` (GET)**: 健康检查端点，用于负载均衡和监控。

---

## 错误处理

API使用标准的HTTP状态码来指示请求的结果。

- **400 Bad Request**: 请求参数无效（如纬度超出范围）。
- **500 Internal Server Error**: 服务器内部错误，通常是由于GEE或天气API连接问题。

#### 错误响应示例
```json
{
  "error": "纬度必须在-90到90之间"
}
```

---
*文档版本: 1.0*  
*最后更新: 2025-01-20* 