#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气和植被参数命令行查询工具
支持获取天气数据和14个环境参数
"""

import requests
import sys
import json
from datetime import datetime

def get_weather_and_vegetation_data(lat, lon, days_back=30):
    """
    获取天气和植被数据
    """
    try:
        print(f"正在查询坐标 ({lat}, {lon}) 的数据...")
        print(f"植被数据回溯天数: {days_back}")
        
        # 调用综合数据API
        url = "http://localhost:8081/api/all"
        payload = {
            "latitude": lat,
            "longitude": lon,
            "days_back": days_back
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return data
            else:
                print(f"API返回错误: {data.get('error', '未知错误')}")
                return None
        else:
            print(f"HTTP错误 {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("连接失败: 请确保后端服务已启动")
        print("启动命令: cd src && python weather_vegetation_service.py")
        return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def get_14_environmental_parameters(lat, lon, days_back=30):
    """
    获取14个环境参数
    """
    try:
        url = "http://localhost:8081/api/environmental_parameters"
        payload = {
            "latitude": lat,
            "longitude": lon,
            "days_back": days_back
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return data
            else:
                print(f"环境参数API返回错误: {data.get('error', '未知错误')}")
                return None
        else:
            print(f"环境参数HTTP错误 {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"环境参数请求失败: {e}")
        return None

def print_weather_info(weather_data):
    """
    打印天气信息
    """
    if 'error' in weather_data:
        print(f"天气数据错误: {weather_data['error']}")
        return
    
    current = weather_data.get('current', {})
    location = weather_data.get('location', {})
    
    print("\n天气信息:")
    print("----------------------------------------")
    print(f"温度: {current.get('temperature', 'N/A')}°C")
    print(f"湿度: {current.get('humidity', 'N/A')}%")
    print(f"气压: {current.get('pressure', 'N/A')} hPa")
    print(f"风速: {current.get('wind_speed', 'N/A')} m/s")
    
    if current.get('wind_direction'):
        print(f"风向: {current.get('wind_direction', 'N/A')}°")
    
    print(f"天气: {current.get('description', 'N/A')}")
    
    if current.get('note'):
        print(f"说明: {current.get('note')}")
    
    if location.get('name'):
        print(f"\n位置: {location.get('name')}, {location.get('country', 'Unknown')}")
    
    if location.get('timezone'):
        print(f"时区: {location.get('timezone')}")

def print_traditional_vegetation_info(vegetation_data):
    """
    打印传统植被参数信息（保留原有功能）
    """
    if 'error' in vegetation_data:
        print(f"植被数据错误: {vegetation_data['error']}")
        return
    
    print("\n传统植被参数:")
    print("----------------------------------------")
    
    # Sentinel-2 数据
    sentinel2_data = vegetation_data.get('sentinel2_data', {})
    if sentinel2_data:
        print("Sentinel-2 数据:")
        if 'NDVI' in sentinel2_data:
            print(f"   NDVI (植被指数): {sentinel2_data['NDVI']}")
        if 'EVI' in sentinel2_data:
            print(f"   EVI (增强植被指数): {sentinel2_data['EVI']}")
        if 'SAVI' in sentinel2_data:
            print(f"   SAVI (土壤调节植被指数): {sentinel2_data['SAVI']}")
    
    # MODIS 数据指标解释
    modis_descriptions = {
        'LAI': 'LAI (叶面积指数)',
        'FAPAR': 'FAPAR (光合有效辐射吸收率)',
        'Albedo': 'Albedo (宽带反照率)',
        'DSR': 'DSR (向下短波辐射)',
        'PAR': 'PAR (光合有效辐射)',
        'LST_Day': 'LST_Day (白天地表温度)',
        'LST_Night': 'LST_Night (夜间地表温度)',
        'ET': 'ET (蒸散发)',
        'GPP': 'GPP (总初级生产力)',
        'Snow_Cover': 'Snow_Cover (积雪覆盖)'
    }
    
    # MODIS 数据
    modis_data = vegetation_data.get('modis_data', {})
    if modis_data:
        print("MODIS 数据:")
        for key, value in modis_data.items():
            description = modis_descriptions.get(key, key)
            print(f"   {description}: {value}")
    
    # 估算值指标解释
    estimated_descriptions = {
        'FVC': 'FVC (植被覆盖度)',
        'BBE': 'BBE (宽带发射率)',
        'AGB': 'AGB (地上生物量)'
    }
    
    # 估算值
    estimated_values = vegetation_data.get('estimated_values', {})
    if estimated_values:
        print("估算参数:")
        for key, value in estimated_values.items():
            description = estimated_descriptions.get(key, key)
            print(f"   {description}: {value}")
    
    # 数据完整性
    success_rate = vegetation_data.get('success_rate', 0)
    print(f"\n数据获取成功率: {success_rate}%")

def print_14_environmental_parameters(env_data):
    """
    打印14个环境参数
    """
    if not env_data:
        print("无法获取14个环境参数数据")
        return
    
    print("\n14个环境参数详情:")
    print("=" * 80)
    
    # 参数概要
    summary = env_data.get('summary', {})
    print(f"获取概要: {summary.get('available_parameters', 0)}/{summary.get('total_parameters', 14)} 参数")
    print(f"成功率: {summary.get('success_rate', '0%')}")
    
    print("\n" + "-" * 80)
    
    # 详细参数
    parameters = env_data.get('target_parameters', {})
    param_descriptions = {
        'LAI': ('叶面积指数', 'm²/m²', '单位地面上叶片总面积'),
        'FAPAR': ('光合有效辐射吸收率', '无量纲', '植被吸收的光能比例'),
        'FVC': ('植被覆盖度', '%', '地面植被覆盖百分比'),
        'Albedo': ('宽带反照率', '无量纲', '地表反射辐射比例'),
        'BBE': ('宽带发射率', '无量纲', '地表发射长波辐射能力'),
        'DSR': ('向下短波辐射', 'W/m²', '太阳辐射到达地表能量'),
        'PAR': ('光合有效辐射', 'μmol/(m²·s)', '植物光合作用可用光能'),
        'LST': ('地表温度', '°C', '地表热红外温度'),
        'ET': ('蒸散发', 'mm/day', '水分蒸发和植物蒸腾'),
        'GPP': ('总初级生产力', 'g C/m²/day', '植被碳固定速率'),
        'SCE': ('积雪覆盖范围', '%', '地表积雪覆盖比例'),
        'AGB': ('地上生物量', 'Mg/ha', '地上部分植被重量'),
        'LWNR': ('净长波辐射', 'W/m²', '净长波辐射通量'),
        'NR': ('净辐射', 'W/m²', '净辐射通量')
    }
    
    for i, (param, value) in enumerate(parameters.items(), 1):
        chinese_name, unit, description = param_descriptions.get(param, (param, '未知', '无描述'))
        
        print(f"{i:2d}. {param} - {chinese_name}")
        print(f"    描述: {description}")
        print(f"    单位: {unit}")
        
        if param == 'LST' and isinstance(value, dict):
            # 地表温度特殊处理
            day_temp = value.get('day')
            night_temp = value.get('night')
            
            if day_temp is not None:
                print(f"    白天温度: {day_temp:.2f} {unit}")
            else:
                print(f"    白天温度: 无数据")
                
            if night_temp is not None:
                print(f"    夜间温度: {night_temp:.2f} {unit}")
            else:
                print(f"    夜间温度: 无数据")
                
        elif value is not None:
            if isinstance(value, (int, float)):
                print(f"    数值: {value:.4f}")
            else:
                print(f"    数值: {value}")
        else:
            print(f"    状态: 无数据 (该区域可能无有效数据)")
        
        print()
    
    # 数据源信息
    sources = env_data.get('data_sources', {})
    if sources:
        print("数据源:")
        for source, description in sources.items():
            print(f"   {source}: {description}")

def print_analysis_summary(weather_data, vegetation_data, env_data):
    """
    打印分析总结
    """
    print("\n综合分析总结:")
    print("=" * 60)
    
    # 天气状况
    if weather_data and 'current' in weather_data:
        current = weather_data['current']
        temp = current.get('temperature', 'N/A')
        humidity = current.get('humidity', 'N/A')
        weather_desc = current.get('description', 'N/A')
        print(f"天气状况: {weather_desc}, {temp}°C, 湿度{humidity}%")
    
    # 植被健康度评估
    if vegetation_data and 'sentinel2_data' in vegetation_data:
        ndvi = vegetation_data['sentinel2_data'].get('NDVI')
        if ndvi is not None:
            if ndvi > 0.6:
                health = "优秀 (茂密植被)"
            elif ndvi > 0.3:
                health = "良好 (中等植被)"
            elif ndvi > 0.1:
                health = "一般 (稀疏植被)"
            else:
                health = "较差 (裸地或无植被)"
            print(f"植被健康度: {health} (NDVI: {ndvi:.3f})")
    
    # 环境参数可用性
    if env_data and 'summary' in env_data:
        summary = env_data['summary']
        available = summary.get('available_parameters', 0)
        total = summary.get('total_parameters', 14)
        success_rate = summary.get('success_rate', '0%')
        print(f"环境参数: {available}/{total} 可用 (成功率: {success_rate})")
    
    # 数据质量评估
    quality_score = 0
    if weather_data and 'current' in weather_data:
        quality_score += 1
    if vegetation_data and vegetation_data.get('success_rate', 0) > 50:
        quality_score += 1
    if env_data and env_data.get('summary', {}).get('available_parameters', 0) > 8:
        quality_score += 1
    
    quality_levels = ["数据不足", "数据一般", "数据良好", "数据优秀"]
    print(f"整体数据质量: {quality_levels[min(quality_score, 3)]}")

def format_header(lat, lon, days_back):
    """
    格式化输出头部
    """
    print("=" * 80)
    print("WeatherG - 天气和环境参数综合查询系统")
    print("=" * 80)
    print(f"查询坐标: ({lat}, {lon})")
    print(f"植被数据回溯: {days_back} 天")
    print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def main():
    """
    主函数
    """
    if len(sys.argv) < 3:
        print("用法: python weather_cli.py <纬度> <经度> [回溯天数]")
        print()
        print("参数说明:")
        print("  纬度: -90 到 90 之间的数值")
        print("  经度: -180 到 180 之间的数值")
        print("  回溯天数: 可选，植被数据回溯天数 (默认30天)")
        print()
        print("示例:")
        print("  python weather_cli.py 39.9042 116.4074        # 北京，默认30天")
        print("  python weather_cli.py 31.2304 121.4737 7      # 上海，回溯7天")
        print("  python weather_cli.py 22.5431 114.0579 15     # 深圳，回溯15天")
        print()
        print("功能特性:")
        print("  实时天气数据 (Open-Meteo免费API)")
        print("  传统植被参数 (NDVI, EVI, SAVI等)")
        print("  14个环境参数 (LAI, FAPAR, LST, ET, GPP等)")
        print("  多源卫星数据 (Sentinel-2, MODIS)")
        print("  综合数据分析和评估")
        return
    
    try:
        # 解析命令行参数
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        days_back = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        
        # 验证坐标范围
        if not (-90 <= lat <= 90):
            print("错误: 纬度必须在-90到90之间")
            return
        if not (-180 <= lon <= 180):
            print("错误: 经度必须在-180到180之间")
            return
        if days_back < 1 or days_back > 365:
            print("错误: 回溯天数必须在1到365之间")
            return
        
        # 格式化输出头部
        format_header(lat, lon, days_back)
        
        # 获取综合数据
        comprehensive_data = get_weather_and_vegetation_data(lat, lon, days_back)
        
        if comprehensive_data:
            weather_data = comprehensive_data.get('weather', {})
            vegetation_data = comprehensive_data.get('vegetation', {})
            
            # 打印天气信息
            print_weather_info(weather_data)
            
            # 打印传统植被参数
            print_traditional_vegetation_info(vegetation_data)
            
            # 获取并打印14个环境参数
            env_params_data = get_14_environmental_parameters(lat, lon, days_back)
            if env_params_data:
                print_14_environmental_parameters(env_params_data)
            
            # 打印综合分析
            print_analysis_summary(weather_data, vegetation_data, env_params_data)
            
            print("\n" + "=" * 80)
            print("查询完成!")
            print("提示: 部分参数可能因数据源覆盖范围或时间限制而无数据")
            print("详细API文档: http://localhost:8081/api/status")
            print("=" * 80)
        
        else:
            print("\n数据获取失败!")
            print("请检查:")
            print("1. 后端服务是否已启动: cd src && python weather_vegetation_service.py")
            print("2. Google Earth Engine认证是否正确")
            print("3. 网络连接是否正常")
            print("4. 坐标是否有效")
    
    except ValueError:
        print("错误: 坐标格式不正确，请输入有效的数字")
        print("示例: python weather_cli.py 39.9042 116.4074 30")
    except KeyboardInterrupt:
        print("\n\n用户中断查询")
    except Exception as e:
        print(f"未知错误: {e}")

if __name__ == "__main__":
    main() 