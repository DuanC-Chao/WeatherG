# WeatherG - 天气和植被参数综合查询系统

🌍 一个基于Google Earth Engine和天气API的综合环境数据查询系统，通过经纬度坐标获取指定位置的天气信息和植被参数。

## 🚀 功能特性

### 🌤️ 天气数据
- **当前天气**: 温度、湿度、气压、风速、天气状况
- **天气描述**: 智能天气代码转换为中文描述
- **地理信息**: 自动时区检测、全球坐标支持
- **数据源**: Open-Meteo免费API（无需密钥）

### 🌱 14个环境参数支持
#### ✅ 直接支持 (12/14)
1. **LAI** - 叶面积指数 (Leaf Area Index) - `MODIS/061/MCD15A3H`
2. **FAPAR** - 光合有效辐射吸收率 (Fraction of Absorbed PAR) - `MODIS/061/MCD15A3H`
3. **FVC** - 植被覆盖度 (Fractional Vegetation Coverage) - 基于NDVI计算
4. **Albedo** - 宽带反照率 (Broadband Albedo) - `MODIS/061/MCD43A3`
5. **BBE** - 宽带发射率 (Broadband Emissivity) - 基于LAI和NDVI估算
6. **DSR** - 向下短波辐射 (Downward Shortwave Radiation) - `ECMWF/ERA5_LAND/HOURLY`
7. **PAR** - 光合有效辐射 (Photosynthetically Active Radiation) - 基于DSR计算
8. **LST** - 地表温度 (Land Surface Temperature) - `MODIS/061/MOD11A1`（日/夜）
9. **ET** - 蒸散发 (Evapotranspiration) - `MODIS/061/MOD16A2`
10. **GPP** - 总初级生产力 (Gross Primary Production) - `MODIS/061/MOD17A2H`
11. **SCE** - 积雪覆盖范围 (Snow Cover Extent) - `MODIS/061/MOD10A1`
12. **AGB** - 地上生物量 (Aboveground Biomass) - 基于NDVI和气候估算

#### ❌ 需要复杂计算 (2/14)
13. **LWNR** - 净长波辐射 (Net Long-wave Radiation) - 需要辐射平衡模型
14. **NR** - 净辐射 (Net Radiation) - 需要能量平衡方程

### 🛰️ 数据源
- **Sentinel-2**: 10米高分辨率光学卫星数据
- **MODIS**: 500米-1km中分辨率多光谱数据
- **ERA5**: 全球再分析气象数据
- **Open-Meteo**: 免费实时天气数据（无需API密钥）

## 📁 项目结构

```
WeatherG/
├── src/                              # 源代码目录
│   └── weather_vegetation_service.py  # 后端服务主程序
├── weather_cli.py                    # 命令行前端工具
├── README.md                         # 项目说明文档
├── requirements.txt                  # Python依赖包
└── .venv/                           # Python虚拟环境 (自动生成)
```

## 🔧 安装和配置

### 1. 环境要求
- Python 3.11+
- Google Earth Engine账号 (免费注册)
- ✅ 天气数据：使用Open-Meteo免费API，无需配置

### 2. 克隆项目
```bash
git clone <repository_url>
cd WeatherG
```

### 3. 创建虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

### 4. 安装依赖包
```bash
pip install -r requirements.txt
```

### 5. Google Earth Engine配置
```bash
# 认证GEE账号
earthengine authenticate

# 测试连接
python -c "import ee; ee.Initialize(project='your-project-id'); print('GEE配置成功!')"
```

### 6. 天气API配置 ✅ 无需配置！

**🎉 好消息！** 本项目现在使用**Open-Meteo免费天气API**：
- ✅ 完全免费，无调用次数限制
- ✅ 无需注册或API密钥
- ✅ 基于欧洲中期天气预报中心数据
- ✅ 全球覆盖，数据质量高

**不需要任何天气API配置即可使用！**

## 🎯 使用方法

### 方式1: 命令行工具 (推荐)

#### 启动后端服务
```bash
# 在终端1中启动后端
cd src
python weather_vegetation_service.py
```

#### 使用命令行查询
```bash
# 在终端2中使用命令行工具
python weather_cli.py <纬度> <经度> [回溯天数]
```

#### 示例
```bash
# 查询北京天气和植被 (默认30天)
python weather_cli.py 39.9042 116.4074

# 查询上海天气和植被 (回溯7天)
python weather_cli.py 31.2304 121.4737 7

# 查询广州天气和植被 (回溯15天)
python weather_cli.py 23.1291 113.2644 15
```

#### 常用城市坐标
| 城市 | 纬度 | 经度 | 命令示例 |
|------|------|------|----------|
| 北京 | 39.9042 | 116.4074 | `python weather_cli.py 39.9042 116.4074` |
| 上海 | 31.2304 | 121.4737 | `python weather_cli.py 31.2304 121.4737` |
| 广州 | 23.1291 | 113.2644 | `python weather_cli.py 23.1291 113.2644` |
| 深圳 | 22.5431 | 114.0579 | `python weather_cli.py 22.5431 114.0579` |
| 成都 | 30.5728 | 104.0668 | `python weather_cli.py 30.5728 104.0668` |
| 杭州 | 30.2741 | 120.1551 | `python weather_cli.py 30.2741 120.1551` |

### 方式2: HTTP API接口

#### 启动服务
```bash
cd src
python weather_vegetation_service.py
```
服务将在 `http://localhost:8080` 启动

#### API端点

**1. 获取所有数据 (天气+植被)**
```bash
# GET方式 (简单)
curl "http://localhost:8080/api/simple?lat=39.9042&lon=116.4074&days=30"

# POST方式 (完整)
curl -X POST http://localhost:8080/api/all \
  -H "Content-Type: application/json" \
  -d '{"latitude": 39.9042, "longitude": 116.4074, "days_back": 30}'
```

**2. 只获取天气数据**
```bash
curl -X POST http://localhost:8080/api/weather \
  -H "Content-Type: application/json" \
  -d '{"latitude": 39.9042, "longitude": 116.4074}'
```

**3. 只获取植被数据**
```bash
curl -X POST http://localhost:8080/api/vegetation \
  -H "Content-Type: application/json" \
  -d '{"latitude": 39.9042, "longitude": 116.4074, "days_back": 30}'
```

**4. 服务状态检查**
```bash
curl http://localhost:8080/api/status
```

**5. API文档**
```bash
curl http://localhost:8080/
```

## 📊 输出示例

### 命令行输出
```
============================================================
📍 坐标 (39.9042, 116.4074) 的环境数据
============================================================
⏰ 查询时间: 2025-06-09 14:35:20

🌤️  天气信息:
----------------------------------------
🌡️  温度: 25.0°C
💧 湿度: 65%
🎯 气压: 1013 hPa
💨 风速: 3.5 m/s
👁️  能见度: N/A km
☀️  天气: 晴朗
ℹ️  说明: 演示数据 - 请配置OpenWeatherMap API密钥获取真实数据

📍 位置: 坐标点 (39.9042, 116.4074), Unknown

🌱 植被参数:
----------------------------------------
🛰️  Sentinel-2 数据 (2025-06-07):
   • NDVI (植被指数): 0.0757
   • EVI (增强植被指数): 0.4895
   • SAVI (土壤调节植被指数): 0.1135
   • FVC (植被覆盖度): 0.0008
   • 分辨率: 10m
   • 云覆盖: 13.7%

📊 分析结果:
   • BBE (宽带发射率): 0.95
   • 植被状态: 很差 (无植被或裸地)
   • 详细描述: NDVI: 0.0757 (植被指数) | EVI: 0.4895 (增强植被指数) | FVC: 0.0008 (植被覆盖度)

🔍 查询信息:
   • 查询时间: 2025-06-09 14:35:20
   • 数据时间范围: 2025-05-10 to 2025-06-09

============================================================
✅ 查询完成!
```

### JSON API输出
```json
{
  "success": true,
  "coordinates": {
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "weather": {
    "current": {
      "temperature": 25.0,
      "humidity": 65,
      "pressure": 1013,
      "description": "晴朗",
      "wind_speed": 3.5
    },
    "location": {
      "name": "坐标点 (39.9042, 116.4074)",
      "country": "Unknown"
    }
  },
  "vegetation": {
    "sentinel2": {
      "NDVI": 0.0757,
      "EVI": 0.4895,
      "SAVI": 0.1135,
      "FVC": 0.0008,
      "date": "2025-06-07",
      "resolution": "10m",
      "cloud_cover": "13.7%"
    },
    "derived": {
      "BBE": 0.95,
      "vegetation_status": "很差 (无植被或裸地)"
    }
  },
  "timestamp": "2025-06-09 14:35:20"
}
```

## 🔍 参数说明

### 环境参数详解
| 参数 | 中文名称 | 单位 | 数据源 | 说明 |
|------|----------|------|--------|------|
| LAI | 叶面积指数 | m²/m² | MODIS | 单位地面上叶片总面积 |
| FAPAR | 光合有效辐射吸收率 | 无量纲 | MODIS | 植被吸收的光能比例 |
| FVC | 植被覆盖度 | % | 计算 | 地面植被覆盖百分比 |
| Albedo | 宽带反照率 | 无量纲 | MODIS | 地表反射辐射比例 |
| BBE | 宽带发射率 | 无量纲 | 估算 | 地表发射长波辐射能力 |
| DSR | 向下短波辐射 | W/m² | ERA5 | 太阳辐射到达地表能量 |
| PAR | 光合有效辐射 | μmol/(m²·s) | 计算 | 植物光合作用可用光能 |
| LST | 地表温度 | °C | MODIS | 地表热红外温度（日/夜） |
| ET | 蒸散发 | mm/day | MODIS | 水分蒸发和植物蒸腾 |
| GPP | 总初级生产力 | g C/m²/day | MODIS | 植被碳固定速率 |
| SCE | 积雪覆盖范围 | % | MODIS | 地表积雪覆盖比例 |
| AGB | 地上生物量 | Mg/ha | 估算 | 地上部分植被重量 |

### 数据质量说明
- **高精度**: Sentinel-2数据（10米分辨率）- 适合局部分析
- **中等精度**: MODIS数据（500米-1km）- 适合区域监测  
- **估算值**: 基于多参数算法估算 - 供参考使用
- **时效性**: 大部分数据有1-3天延迟，历史数据完整

## 🛠️ 故障排除

### 常见问题

#### 1. GEE认证失败
```bash
# 重新认证
earthengine authenticate --force

# 检查项目ID
python -c "import ee; ee.Initialize(project='your-project-id')"
```

#### 2. 服务连接失败
```bash
# 检查服务状态
curl http://localhost:8080/api/status

# 重启服务
cd src
python weather_vegetation_service.py
```

#### 3. 植被数据为空
可能原因：
- 查询区域在海洋上
- 云覆盖太厚
- 时间范围内无卫星数据
- 可以尝试增加回溯天数

#### 4. 天气数据显示演示数据
需要配置OpenWeatherMap API密钥：
1. 访问 [OpenWeatherMap](https://openweathermap.org/api) 注册账号
2. 获取免费API密钥
3. 在 `src/weather_vegetation_service.py` 中配置

## 🧰 开发信息

### 技术栈
- **后端**: Python Flask
- **数据处理**: Google Earth Engine Python API
- **天气API**: OpenWeatherMap
- **卫星数据**: Sentinel-2, MODIS
- **前端**: 命令行工具

### 项目依赖
```
earthengine-api>=0.1.384
flask>=3.1.1
requests>=2.32.3
```

### 扩展开发
如需添加新功能，可以参考以下结构：
1. 在 `src/weather_vegetation_service.py` 中添加新的数据处理函数
2. 添加对应的API端点
3. 在 `weather_cli.py` 中添加显示逻辑

## 📝 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建GitHub Issue
- 发送邮件到项目维护者

---

🌍 **WeatherG** - 让环境数据查询变得简单高效！

## 🚀 快速开始

### 5.1 命令行测试（推荐）
```bash
# 测试天气+植被综合数据
python weather_cli.py 39.9042 116.4074

# 专门测试14个环境参数
python test_14_parameters.py 39.9042 116.4074

# 指定回溯天数
python test_14_parameters.py 22.32 114.04 60
```

### 5.2 API端点使用

#### 🎯 获取14个环境参数（专用端点）
```bash
curl -X POST http://localhost:8081/api/environmental_parameters \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 39.9042,
    "longitude": 116.4074,
    "days_back": 30
  }'
```

**响应格式**：
```json
{
  "status": "success",
  "summary": {
    "total_parameters": 14,
    "available_parameters": 12,
    "success_rate": "85.7%",
    "missing_parameters": ["LWNR (净长波辐射)", "NR (净辐射)"]
  },
  "target_parameters": {
    "LAI": 2.5,
    "FAPAR": 0.85,
    "FVC": 75.2,
    "Albedo": 0.15,
    "BBE": 0.97,
    "DSR": 185.5,
    "PAR": 89.2,
    "LST": {"day": 28.5, "night": 15.2},
    "ET": 3.2,
    "GPP": 8.5,
    "SCE": 0.0,
    "AGB": 120.5,
    "LWNR": null,
    "NR": null
  }
}
```

#### 🌍 获取综合数据
```bash
curl -X POST http://localhost:8081/api/all \
  -H "Content-Type: application/json" \
  -d '{"latitude": 39.9042, "longitude": 116.4074}'
```

#### 🌤️ 仅获取天气数据
```bash
curl -X POST http://localhost:8081/api/weather \
  -H "Content-Type: application/json" \
  -d '{"latitude": 39.9042, "longitude": 116.4074}'
```

#### 🌱 仅获取植被数据
```bash
curl -X POST http://localhost:8081/api/vegetation \
  -H "Content-Type: application/json" \
  -d '{"latitude": 39.9042, "longitude": 116.4074, "days_back": 30}'
``` 