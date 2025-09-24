#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气和植被参数综合服务
通过经纬度坐标获取：
1. 天气数据：当前天气、预报、历史天气
2. 植被参数：NDVI、LAI、FAPAR、FVC、Albedo、BBE等
使用OpenWeatherMap API和Google Earth Engine API
"""

import ee
import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import math

# 初始化Google Earth Engine
ee.Initialize(project='groovy-root-462406-i4')

app = Flask(__name__)

# Open-Meteo API配置（完全免费，无需API密钥）
WEATHER_API_KEY = None  # Open-Meteo不需要API密钥
WEATHER_BASE_URL = "https://api.open-meteo.com/v1"

def get_weather_data(lat, lon):
    """
    获取天气数据 - 使用Open-Meteo免费API
    
    参数:
    - lat: 纬度
    - lon: 经度
    
    返回:
    - 包含天气信息的字典
    """
    try:
        # 使用Open-Meteo API获取当前天气
        current_url = f"{WEATHER_BASE_URL}/forecast"
        current_params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,weather_code',
            'timezone': 'auto',
            'forecast_days': 1
        }
        
        current_response = requests.get(current_url, params=current_params, timeout=10)
        
        if current_response.status_code == 200:
            data = current_response.json()
            current = data['current']
            
            # 天气代码转换为描述
            weather_descriptions = {
                0: '晴朗', 1: '主要晴朗', 2: '部分多云', 3: '阴天',
                45: '雾', 48: '霜雾', 51: '小雨', 53: '中雨', 55: '大雨',
                56: '冻小雨', 57: '冻中雨', 61: '小雨', 63: '中雨', 65: '大雨',
                66: '冻雨', 67: '强冻雨', 71: '小雪', 73: '中雪', 75: '大雪',
                77: '雪粒', 80: '小阵雨', 81: '中阵雨', 82: '大阵雨',
                85: '小阵雪', 86: '大阵雪', 95: '雷暴', 96: '小冰雹雷暴', 99: '大冰雹雷暴'
            }
            
            weather_code = current.get('weather_code', 0)
            weather_desc = weather_descriptions.get(weather_code, '未知天气')
            
            return {
                'current': {
                    'temperature': round(current.get('temperature_2m', 0), 1),
                    'humidity': current.get('relative_humidity_2m', 0),
                    'pressure': round(current.get('pressure_msl', 0), 1),
                    'description': weather_desc,
                    'wind_speed': round(current.get('wind_speed_10m', 0), 1),
                    'wind_direction': current.get('wind_direction_10m', 0),
                    'weather_code': weather_code,
                    'note': '数据来源：Open-Meteo (免费天气API)'
                },
                'location': {
                    'name': f'坐标点 ({lat}, {lon})',
                    'country': '全球',
                    'timezone': data.get('timezone', 'UTC')
                }
            }
        else:
            return {'error': f'天气API请求失败: {current_response.status_code}'}
            
    except Exception as e:
        return {'error': f'天气数据获取失败: {str(e)}'}

def get_vegetation_data(lat, lon, days_back=30):
    """
    获取植被和环境参数数据（扩展版）
    
    支持的参数：
    1. LAI (叶面积指数) ✓
    2. FAPAR (光合有效辐射吸收率) ✓
    3. FVC (植被覆盖度) ✓ (计算得出)
    4. Albedo (宽带反照率) ✓
    5. BBE (宽带发射率) ✓
    6. DSR (向下短波辐射) ✓
    7. PAR (光合有效辐射) ✓
    8. LST (地表温度) ✓
    9. ET (蒸散发) ✓
    10. GPP (总初级生产力) ✓
    11. SCE (积雪覆盖范围) ✓
    12. AGB (地上生物量) ✓ (粗略估算)
    13. LWNR (净长波辐射) ✗ (需要复杂计算)
    14. NR (净辐射) ✗ (需要复杂计算)
    """
    
    try:
        # 创建点几何和时间范围
        point = ee.Geometry.Point([lon, lat])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        print(f"🌱 正在获取植被参数数据 ({start_str} 至 {end_str})...")
        
        # 初始化结果字典
        vegetation_data = {
            'coordinates': {'latitude': lat, 'longitude': lon},
            'date_range': {'start': start_str, 'end': end_str},
            'data_source': '多源卫星数据集',
            'sentinel2_data': {},
            'modis_data': {},
            'estimated_values': {},
            'data_quality': 'mixed'
        }
        
        # === 1-3. Sentinel-2 数据：LAI, FAPAR, FVC ===
        try:
            s2_sr = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                     .filterBounds(point)
                     .filterDate(start_str, end_str)
                     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                     .sort('system:time_start', False))
            
            if s2_sr.size().getInfo() > 0:
                s2_image = s2_sr.first()
                
                # 计算植被指数
                def calculate_ndvi(image):
                    return image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                
                def calculate_evi(image):
                    evi = image.expression(
                        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                        {
                            'NIR': image.select('B8'),
                            'RED': image.select('B4'),
                            'BLUE': image.select('B2')
                        }
                    ).rename('EVI')
                    return evi
                
                def calculate_savi(image):
                    savi = image.expression(
                        '((NIR - RED) / (NIR + RED + 0.5)) * 1.5',
                        {
                            'NIR': image.select('B8'),
                            'RED': image.select('B4')
                        }
                    ).rename('SAVI')
                    return savi
                
                # 计算指数
                ndvi = calculate_ndvi(s2_image)
                evi = calculate_evi(s2_image)
                savi = calculate_savi(s2_image)
                
                # 采样数据
                ndvi_sample = ndvi.sample(point, 10).first()
                evi_sample = evi.sample(point, 10).first()
                savi_sample = savi.sample(point, 10).first()
                
                ndvi_val = ndvi_sample.get('NDVI').getInfo() if ndvi_sample.get('NDVI') else None
                evi_val = evi_sample.get('EVI').getInfo() if evi_sample.get('EVI') else None
                savi_val = savi_sample.get('SAVI').getInfo() if savi_sample.get('SAVI') else None
                
                if ndvi_val is not None:
                    vegetation_data['sentinel2_data']['NDVI'] = round(float(ndvi_val), 4)
                    # 使用NDVI估算FVC
                    if ndvi_val > 0:
                        fvc = ((ndvi_val - 0.05) / (0.95 - 0.05)) ** 2
                        vegetation_data['estimated_values']['FVC'] = round(max(0, min(1, fvc)), 4)
                
                if evi_val is not None:
                    vegetation_data['sentinel2_data']['EVI'] = round(float(evi_val), 4)
                
                if savi_val is not None:
                    vegetation_data['sentinel2_data']['SAVI'] = round(float(savi_val), 4)
                
                print(f"✅ Sentinel-2 数据获取成功")
        
        except Exception as e:
            print(f"⚠️  Sentinel-2 数据获取失败: {str(e)}")
        
        # === 4-5. MODIS LAI/FAPAR ===
        try:
            modis_lai = (ee.ImageCollection('MODIS/061/MCD15A3H')
                         .filterBounds(point)
                         .filterDate(start_str, end_str)
                         .sort('system:time_start', False))
            
            if modis_lai.size().getInfo() > 0:
                lai_image = modis_lai.first()
                
                # 使用缓冲区采样提高成功率
                lai_region = lai_image.select('Lai').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(250),  # 250米缓冲区
                    scale=500,
                    maxPixels=1e9
                )
                
                fpar_region = lai_image.select('Fpar').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(250),
                    scale=500,
                    maxPixels=1e9
                )
                
                lai_val = lai_region.get('Lai').getInfo()
                fpar_val = fpar_region.get('Fpar').getInfo()
                
                if lai_val is not None and lai_val != 0:
                    # MODIS LAI缩放因子是0.1
                    vegetation_data['modis_data']['LAI'] = round(float(lai_val) * 0.1, 3)
                
                if fpar_val is not None and fpar_val != 0:
                    # MODIS FPAR缩放因子是0.01
                    vegetation_data['modis_data']['FAPAR'] = round(float(fpar_val) * 0.01, 3)
                
                print(f"✅ MODIS LAI/FAPAR数据获取成功")
        
        except Exception as e:
            print(f"⚠️  MODIS LAI/FAPAR数据获取失败: {str(e)}")
        
        # === 6. Albedo (反照率) ===
        try:
            modis_albedo = (ee.ImageCollection('MODIS/061/MCD43A3')
                           .filterBounds(point)
                           .filterDate(start_str, end_str)
                           .sort('system:time_start', False))
            
            if modis_albedo.size().getInfo() > 0:
                albedo_image = modis_albedo.first()
                
                # 获取shortwave白天反照率
                albedo_region = albedo_image.select('Albedo_WSA_shortwave').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(250),
                    scale=500,
                    maxPixels=1e9
                )
                
                albedo_val = albedo_region.get('Albedo_WSA_shortwave').getInfo()
                if albedo_val is not None:
                    # MODIS反照率缩放因子是0.001
                    vegetation_data['modis_data']['Albedo'] = round(float(albedo_val) * 0.001, 4)
                
                print(f"✅ MODIS Albedo数据获取成功")
        
        except Exception as e:
            print(f"⚠️  MODIS Albedo数据获取失败: {str(e)}")
        
        # === 7-8. DSR和PAR (辐射数据) ===
        try:
            # MCD18A1: 向下短波辐射
            modis_dsr = (ee.ImageCollection('MODIS/061/MCD18A1')
                        .filterBounds(point)
                        .filterDate(start_str, end_str)
                        .sort('system:time_start', False))
            
            if modis_dsr.size().getInfo() > 0:
                dsr_image = modis_dsr.first()
                
                dsr_region = dsr_image.select('DSR').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(500),
                    scale=1000,
                    maxPixels=1e9
                )
                
                dsr_val = dsr_region.get('DSR').getInfo()
                if dsr_val is not None:
                    vegetation_data['modis_data']['DSR'] = round(float(dsr_val), 2)
            
            # MCD18C2: 光合有效辐射 
            modis_par = (ee.ImageCollection('MODIS/061/MCD18C2')
                        .filterBounds(point)
                        .filterDate(start_str, end_str)
                        .sort('system:time_start', False))
            
            if modis_par.size().getInfo() > 0:
                par_image = modis_par.first()
                
                par_region = par_image.select('PAR').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(2500),  # PAR是0.05度分辨率
                    scale=5600,
                    maxPixels=1e9
                )
                
                par_val = par_region.get('PAR').getInfo()
                if par_val is not None:
                    vegetation_data['modis_data']['PAR'] = round(float(par_val), 2)
            
            print(f"✅ MODIS辐射数据获取成功")
        
        except Exception as e:
            print(f"⚠️  MODIS辐射数据获取失败: {str(e)}")
        
        # === 9. LST (地表温度) ===
        try:
            modis_lst = (ee.ImageCollection('MODIS/061/MOD11A1')
                        .filterBounds(point)
                        .filterDate(start_str, end_str)
                        .sort('system:time_start', False))
            
            if modis_lst.size().getInfo() > 0:
                lst_image = modis_lst.first()
                
                lst_day_region = lst_image.select('LST_Day_1km').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(500),
                    scale=1000,
                    maxPixels=1e9
                )
                
                lst_night_region = lst_image.select('LST_Night_1km').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(500),
                    scale=1000,
                    maxPixels=1e9
                )
                
                lst_day_val = lst_day_region.get('LST_Day_1km').getInfo()
                lst_night_val = lst_night_region.get('LST_Night_1km').getInfo()
                
                if lst_day_val is not None:
                    # MODIS LST缩放因子是0.02，单位是开尔文
                    lst_celsius = float(lst_day_val) * 0.02 - 273.15
                    vegetation_data['modis_data']['LST_Day'] = round(lst_celsius, 2)
                
                if lst_night_val is not None:
                    lst_celsius = float(lst_night_val) * 0.02 - 273.15
                    vegetation_data['modis_data']['LST_Night'] = round(lst_celsius, 2)
                
                print(f"✅ MODIS LST数据获取成功")
        
        except Exception as e:
            print(f"⚠️  MODIS LST数据获取失败: {str(e)}")
        
        # === 10. ET (蒸散发) ===
        try:
            modis_et = (ee.ImageCollection('MODIS/061/MOD16A2')
                       .filterBounds(point)
                       .filterDate(start_str, end_str)
                       .sort('system:time_start', False))
            
            if modis_et.size().getInfo() > 0:
                et_image = modis_et.first()
                
                et_region = et_image.select('ET').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(250),
                    scale=500,
                    maxPixels=1e9
                )
                
                et_val = et_region.get('ET').getInfo()
                if et_val is not None:
                    # MODIS ET缩放因子是0.1，单位是kg/m²/8day
                    vegetation_data['modis_data']['ET'] = round(float(et_val) * 0.1, 2)
                
                print(f"✅ MODIS ET数据获取成功")
        
        except Exception as e:
            print(f"⚠️  MODIS ET数据获取失败: {str(e)}")
        
        # === 11. GPP (总初级生产力) ===
        try:
            modis_gpp = (ee.ImageCollection('MODIS/061/MOD17A2H')
                        .filterBounds(point)
                        .filterDate(start_str, end_str)
                        .sort('system:time_start', False))
            
            if modis_gpp.size().getInfo() > 0:
                gpp_image = modis_gpp.first()
                
                gpp_region = gpp_image.select('Gpp').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(250),
                    scale=500,
                    maxPixels=1e9
                )
                
                gpp_val = gpp_region.get('Gpp').getInfo()
                if gpp_val is not None:
                    # MODIS GPP缩放因子是0.0001，单位是kg C/m²/8day
                    vegetation_data['modis_data']['GPP'] = round(float(gpp_val) * 0.0001, 4)
                
                print(f"✅ MODIS GPP数据获取成功")
        
        except Exception as e:
            print(f"⚠️  MODIS GPP数据获取失败: {str(e)}")
        
        # === 12. SCE (积雪覆盖) ===
        try:
            modis_snow = (ee.ImageCollection('MODIS/061/MOD10A1')
                         .filterBounds(point)
                         .filterDate(start_str, end_str)
                         .sort('system:time_start', False))
            
            if modis_snow.size().getInfo() > 0:
                snow_image = modis_snow.first()
                
                snow_region = snow_image.select('NDSI_Snow_Cover').reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=point.buffer(250),
                    scale=500,
                    maxPixels=1e9
                )
                
                snow_val = snow_region.get('NDSI_Snow_Cover').getInfo()
                if snow_val is not None:
                    vegetation_data['modis_data']['Snow_Cover'] = int(snow_val)
                
                print(f"✅ MODIS积雪数据获取成功")
        
        except Exception as e:
            print(f"⚠️  MODIS积雪数据获取失败: {str(e)}")
        
        # === 13. BBE (宽带发射率) 和 AGB (生物量估算) ===
        try:
            # 使用NDVI估算宽带发射率
            if 'NDVI' in vegetation_data['sentinel2_data']:
                ndvi = vegetation_data['sentinel2_data']['NDVI']
                if ndvi > 0.2:
                    # 植被区域发射率估算
                    bbe = 0.004 * ndvi + 0.986
                else:
                    # 裸土区域发射率
                    bbe = 0.95
                vegetation_data['estimated_values']['BBE'] = round(bbe, 4)
            
            # 使用LAI和NDVI估算地上生物量
            if 'LAI' in vegetation_data['modis_data'] and 'NDVI' in vegetation_data['sentinel2_data']:
                lai = vegetation_data['modis_data']['LAI']
                ndvi = vegetation_data['sentinel2_data']['NDVI']
                # 简化的生物量估算模型 (仅供参考)
                agb = (lai * 2.5 + ndvi * 10) * 1000  # 估算值，单位 g/m²
                vegetation_data['estimated_values']['AGB'] = round(max(0, agb), 2)
            
            print(f"✅ 估算参数计算完成")
        
        except Exception as e:
            print(f"⚠️  估算参数计算失败: {str(e)}")
        
        # 计算数据完整性
        total_params = 14
        available_params = 0
        
        available_params += len(vegetation_data['sentinel2_data'])
        available_params += len(vegetation_data['modis_data'])
        available_params += len(vegetation_data['estimated_values'])
        
        vegetation_data['data_completeness'] = f"{available_params}/{total_params}"
        vegetation_data['success_rate'] = round(available_params / total_params * 100, 1)
        
        # 添加参数说明
        vegetation_data['parameter_descriptions'] = {
            'LAI': '叶面积指数 (m²/m²)',
            'FAPAR': '光合有效辐射吸收率 (0-1)',
            'FVC': '植被覆盖度 (0-1)',
            'Albedo': '宽带反照率 (0-1)',
            'BBE': '宽带发射率 (0-1)',
            'DSR': '向下短波辐射 (W/m²)',
            'PAR': '光合有效辐射 (W/m²)',
            'LST_Day': '白天地表温度 (°C)',
            'LST_Night': '夜间地表温度 (°C)',
            'ET': '蒸散发 (kg/m²/8day)',
            'GPP': '总初级生产力 (kg C/m²/8day)',
            'Snow_Cover': '积雪覆盖 (0-100%)',
            'AGB': '地上生物量估算 (g/m²)',
            'NDVI': '归一化植被指数 (-1 to 1)',
            'EVI': '增强植被指数 (-1 to 1)',
            'SAVI': '土壤调节植被指数 (-1 to 1)'
        }
        
        print(f"✅ 植被参数数据获取完成 - 成功率: {vegetation_data['success_rate']}%")
        return vegetation_data
        
    except Exception as e:
        print(f"❌ 植被数据获取错误: {str(e)}")
        return {
            'error': f'植被数据获取失败: {str(e)}',
            'coordinates': {'latitude': lat, 'longitude': lon},
            'success': False
        }

# ========== API 端点 ==========

@app.route('/api/all', methods=['POST'])
def get_all_data():
    """获取综合环境数据（天气+植被）"""
    try:
        data = request.json
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        days_back = int(data.get('days_back', 30))
        
        # 验证坐标范围
        if not (-90 <= lat <= 90):
            return jsonify({'error': '纬度必须在-90到90之间'}), 400
        if not (-180 <= lon <= 180):
            return jsonify({'error': '经度必须在-180到180之间'}), 400
        
        # 并行获取天气和植被数据
        weather_data = get_weather_data(lat, lon)
        vegetation_data = get_vegetation_data(lat, lon, days_back)
        
        return jsonify({
            'status': 'success',
            'location': {'latitude': lat, 'longitude': lon},
            'weather': weather_data,
            'vegetation': vegetation_data,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': f'数据获取失败: {str(e)}'}), 500

@app.route('/api/environmental_parameters', methods=['POST'])
def get_environmental_parameters():
    """获取全部14个环境参数的专用端点"""
    try:
        data = request.json
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        days_back = int(data.get('days_back', 30))
        
        # 验证坐标范围
        if not (-90 <= lat <= 90):
            return jsonify({'error': '纬度必须在-90到90之间'}), 400
        if not (-180 <= lon <= 180):
            return jsonify({'error': '经度必须在-180到180之间'}), 400
        
        # 获取全部环境参数
        vegetation_data = get_vegetation_data(lat, lon, days_back)
        
        # 重新组织输出，突出显示14个目标参数
        target_parameters = {}
        
        # 从各个数据源中提取目标参数
        all_data = {**vegetation_data.get('modis_data', {}), 
                   **vegetation_data.get('sentinel2_data', {}),
                   **vegetation_data.get('estimated_values', {})}
        
        # 映射到14个目标参数
        parameter_mapping = {
            'LAI': all_data.get('LAI'),
            'FAPAR': all_data.get('FAPAR'), 
            'FVC': all_data.get('FVC'),
            'Albedo': all_data.get('Albedo'),
            'BBE': all_data.get('BBE'),
            'DSR': all_data.get('DSR'),
            'PAR': all_data.get('PAR'),
            'LST': {
                'day': all_data.get('LST_Day'),
                'night': all_data.get('LST_Night')
            },
            'ET': all_data.get('ET'),
            'GPP': all_data.get('GPP'),
            'SCE': all_data.get('Snow_Cover'),
            'AGB': all_data.get('AGB'),
            'LWNR': None,  # 需要复杂计算
            'NR': None     # 需要复杂计算
        }
        
        # 统计可用参数
        available_count = 0
        for key, value in parameter_mapping.items():
            if key == 'LST':
                if value['day'] is not None or value['night'] is not None:
                    available_count += 1
            elif value is not None:
                available_count += 1
        
        return jsonify({
            'status': 'success',
            'location': {'latitude': lat, 'longitude': lon},
            'summary': {
                'total_parameters': 14,
                'available_parameters': available_count,
                'success_rate': f"{round(available_count/14*100, 1)}%",
                'missing_parameters': ['LWNR (净长波辐射)', 'NR (净辐射)'] if available_count < 14 else []
            },
            'target_parameters': parameter_mapping,
            'parameter_descriptions': vegetation_data.get('parameter_descriptions', {}),
            'data_sources': {
                'sentinel2': '10米高分辨率光学数据',
                'modis': '500米-1km多源卫星数据',
                'estimated': '基于算法估算'
            },
            'raw_data': vegetation_data,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': f'环境参数获取失败: {str(e)}'}), 500

@app.route('/api/weather', methods=['POST'])
def get_weather_only():
    """仅获取天气数据"""
    try:
        data = request.json
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        
        # 验证坐标范围
        if not (-90 <= lat <= 90):
            return jsonify({'error': '纬度必须在-90到90之间'}), 400
        if not (-180 <= lon <= 180):
            return jsonify({'error': '经度必须在-180到180之间'}), 400
        
        weather_data = get_weather_data(lat, lon)
        
        return jsonify({
            'status': 'success',
            'location': {'latitude': lat, 'longitude': lon},
            'weather': weather_data,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': f'天气数据获取失败: {str(e)}'}), 500

@app.route('/api/vegetation', methods=['POST'])
def get_vegetation_only():
    """仅获取植被参数"""
    try:
        data = request.json
        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        days_back = int(data.get('days_back', 30))
        
        # 验证坐标范围
        if not (-90 <= lat <= 90):
            return jsonify({'error': '纬度必须在-90到90之间'}), 400
        if not (-180 <= lon <= 180):
            return jsonify({'error': '经度必须在-180到180之间'}), 400
        
        vegetation_data = get_vegetation_data(lat, lon, days_back)
        
        return jsonify({
            'status': 'success',
            'location': {'latitude': lat, 'longitude': lon},
            'vegetation': vegetation_data,
            'query_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': f'植被数据获取失败: {str(e)}'}), 500

@app.route('/api/simple', methods=['GET'])
def get_simple_data():
    """简单的GET接口，用于快速测试"""
    try:
        lat = float(request.args.get('lat', 39.9042))
        lon = float(request.args.get('lon', 116.4074))
        
        weather_data = get_weather_data(lat, lon)
        
        return jsonify({
            'status': 'success',
            'location': f"{lat}, {lon}",
            'weather': weather_data.get('current', {}),
            'note': '这是简化的测试接口，完整数据请使用POST /api/all'
        })
        
    except Exception as e:
        return jsonify({'error': f'简单查询失败: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def get_api_status():
    """API状态检查"""
    try:
        # 测试GEE连接
        test_point = ee.Geometry.Point([116.4074, 39.9042])
        test_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').limit(1)
        test_size = test_collection.size().getInfo()
        
        return jsonify({
            'status': 'operational',
            'services': {
                'google_earth_engine': 'connected' if test_size >= 0 else 'error',
                'weather_api': 'operational',
                'vegetation_analysis': 'operational'
            },
            'available_endpoints': [
                '/api/all - 获取所有数据',
                '/api/environmental_parameters - 获取14个环境参数',
                '/api/weather - 仅天气数据',
                '/api/vegetation - 仅植被数据',
                '/api/simple - 简单测试接口',
                '/api/status - 服务状态'
            ],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

# ========== 健康检查 ==========
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ========== 主程序入口 ==========
if __name__ == '__main__':
    print("🌟 启动天气植被参数综合服务...")
    print("📊 支持的功能:")
    print("   - 天气数据 (Open-Meteo免费API)")
    print("   - 14个环境参数 (Google Earth Engine)")
    print("   - 多源卫星数据整合")
    print(f"🚀 服务运行在: http://localhost:8081")
    print("🔍 API端点:")
    print("   POST /api/environmental_parameters - 获取全部14个环境参数")
    print("   POST /api/all - 获取天气+植被综合数据")
    print("   POST /api/weather - 仅天气数据")
    print("   POST /api/vegetation - 仅植被数据")
    print("   GET  /api/simple - 简单测试接口")
    print("   GET  /api/status - 服务状态检查")
    
    app.run(host='0.0.0.0', port=8081, debug=True) 