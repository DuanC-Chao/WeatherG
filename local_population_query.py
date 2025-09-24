#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地人口密度数据查询工具
直接读取本地WorldPop GeoTIFF文件，提取指定坐标的人口密度数据

功能：
- 读取本地GeoTIFF文件
- 输入经纬度坐标，直接提取人口密度
- 支持多年份文件批量查询
- 提供周边区域统计分析

使用前准备：
1. 从 https://data.worldpop.org/GIS/Population/Global_2000_2020/ 下载所需年份的中国数据
2. 将文件放在本脚本同目录下，或指定文件路径

文件命名格式：chn_ppp_YYYY.tif (如：chn_ppp_2020.tif)

作者: WeatherG项目组
"""

import rasterio
import os
import sys
import json
import glob
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

class LocalPopulationQuery:
    """本地人口密度数据查询器"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.available_files = self._scan_files()
        print(f"📁 数据目录: {os.path.abspath(data_dir)}")
        print(f"📊 发现 {len(self.available_files)} 个人口数据文件")
        
    def _scan_files(self) -> Dict[int, str]:
        """扫描可用的人口数据文件"""
        files = {}
        
        # 扫描标准命名格式的文件
        pattern = os.path.join(self.data_dir, "chn_ppp_*.tif")
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            try:
                # 从文件名提取年份
                year_str = filename.split('_')[-1].replace('.tif', '')
                year = int(year_str)
                if 2000 <= year <= 2020:
                    files[year] = filepath
                    print(f"  ✅ {year}年: {filename}")
            except ValueError:
                continue
        
        # 如果没找到标准格式，列出所有tif文件供用户参考
        if not files:
            tif_files = glob.glob(os.path.join(self.data_dir, "*.tif"))
            if tif_files:
                print("📋 发现以下TIF文件，请检查是否为WorldPop数据:")
                for f in tif_files:
                    print(f"  📄 {os.path.basename(f)}")
        
        return files
    
    def list_available_years(self) -> List[int]:
        """列出可用的年份"""
        return sorted(self.available_files.keys())
    
    def query_single_coordinate(self, filepath: str, latitude: float, longitude: float) -> Dict[str, Any]:
        """查询单个坐标的人口密度"""
        try:
            with rasterio.open(filepath) as src:
                # 获取文件基本信息
                bounds = src.bounds
                crs = src.crs
                transform = src.transform
                
                print(f"📊 文件信息:")
                print(f"• 文件: {os.path.basename(filepath)}")
                print(f"• 坐标系统: {crs}")
                print(f"• 数据范围: {bounds}")
                print(f"• 分辨率: {transform[0]:.6f}° × {abs(transform[4]):.6f}°")
                print(f"• 数据大小: {src.width} × {src.height} 像素")
                
                # 检查坐标是否在范围内
                if not (bounds.left <= longitude <= bounds.right and 
                       bounds.bottom <= latitude <= bounds.top):
                    return {
                        'error': '坐标超出数据范围',
                        'coordinate': (latitude, longitude),
                        'data_bounds': {
                            'left': bounds.left, 'right': bounds.right,
                            'bottom': bounds.bottom, 'top': bounds.top
                        }
                    }
                
                # 将地理坐标转换为像素坐标
                row, col = src.index(longitude, latitude)
                
                # 确保像素坐标在有效范围内
                if not (0 <= row < src.height and 0 <= col < src.width):
                    return {
                        'error': '坐标转换后超出像素范围',
                        'coordinate': (latitude, longitude),
                        'pixel_coordinate': (row, col)
                    }
                
                # 读取该位置的像素值
                population_density = src.read(1)[row, col]
                
                # 处理NoData值
                if src.nodata is not None and population_density == src.nodata:
                    population_density = 0.0
                
                # 计算周围区域的统计信息（5x5窗口）
                window_size = 2
                row_start = max(0, row - window_size)
                row_end = min(src.height, row + window_size + 1)
                col_start = max(0, col - window_size)
                col_end = min(src.width, col + window_size + 1)
                
                window_data = src.read(1)[row_start:row_end, col_start:col_end]
                
                # 过滤NoData值
                if src.nodata is not None:
                    valid_data = window_data[window_data != src.nodata]
                else:
                    valid_data = window_data.flatten()
                
                # 计算像素实际面积（平方公里）
                # WorldPop数据大约是30弧秒分辨率
                pixel_area_km2 = abs(transform[0] * transform[4]) * (111.32 ** 2)
                
                # 计算不同半径范围内的统计
                radius_stats = self._calculate_radius_stats(src, row, col, [1, 3, 5])
                
                return {
                    'coordinate': {
                        'latitude': latitude,
                        'longitude': longitude,
                        'pixel_row': int(row),
                        'pixel_col': int(col)
                    },
                    'population_data': {
                        'density_per_km2': float(population_density),
                        'total_population_in_pixel': float(population_density * pixel_area_km2),
                        'pixel_area_km2': pixel_area_km2
                    },
                    'surrounding_stats': {
                        'window_size': f"{window_size*2+1}×{window_size*2+1}像素",
                        'mean_density': float(np.mean(valid_data)) if len(valid_data) > 0 else 0.0,
                        'max_density': float(np.max(valid_data)) if len(valid_data) > 0 else 0.0,
                        'min_density': float(np.min(valid_data)) if len(valid_data) > 0 else 0.0,
                        'std_density': float(np.std(valid_data)) if len(valid_data) > 0 else 0.0,
                        'median_density': float(np.median(valid_data)) if len(valid_data) > 0 else 0.0,
                        'sample_count': len(valid_data)
                    },
                    'radius_analysis': radius_stats,
                    'data_info': {
                        'filepath': filepath,
                        'crs': str(crs),
                        'bounds': {
                            'left': bounds.left, 'bottom': bounds.bottom,
                            'right': bounds.right, 'top': bounds.top
                        },
                        'resolution_degrees': {
                            'x': transform[0], 'y': abs(transform[4])
                        },
                        'file_size_mb': os.path.getsize(filepath) / (1024 * 1024)
                    }
                }
                
        except Exception as e:
            return {
                'error': f'数据读取失败: {e}',
                'coordinate': (latitude, longitude),
                'filepath': filepath
            }
    
    def _calculate_radius_stats(self, src, center_row: int, center_col: int, radii: List[int]) -> Dict[str, Any]:
        """计算不同半径范围内的统计信息"""
        stats = {}
        
        for radius in radii:
            row_start = max(0, center_row - radius)
            row_end = min(src.height, center_row + radius + 1)
            col_start = max(0, center_col - radius)
            col_end = min(src.width, center_col + radius + 1)
            
            window_data = src.read(1)[row_start:row_end, col_start:col_end]
            
            # 过滤NoData值
            if src.nodata is not None:
                valid_data = window_data[window_data != src.nodata]
            else:
                valid_data = window_data.flatten()
            
            if len(valid_data) > 0:
                stats[f"radius_{radius}"] = {
                    'mean_density': float(np.mean(valid_data)),
                    'total_population': float(np.sum(valid_data)),
                    'max_density': float(np.max(valid_data)),
                    'pixel_count': len(valid_data),
                    'area_km2': len(valid_data) * abs(src.transform[0] * src.transform[4]) * (111.32 ** 2)
                }
            else:
                stats[f"radius_{radius}"] = {
                    'mean_density': 0.0, 'total_population': 0.0,
                    'max_density': 0.0, 'pixel_count': 0, 'area_km2': 0.0
                }
        
        return stats
    
    def query_multiple_years(self, latitude: float, longitude: float, years: List[int] = None) -> Dict[str, Any]:
        """查询多个年份的人口数据"""
        if years is None:
            years = self.list_available_years()
        
        if not years:
            return {'error': '没有可用的数据文件'}
        
        print(f"🎯 批量查询人口密度数据")
        print(f"📍 坐标: ({latitude}, {longitude})")
        print(f"📅 年份: {', '.join(map(str, years))}")
        print("=" * 60)
        
        results = {}
        successful_years = []
        failed_years = []
        
        for year in sorted(years):
            if year not in self.available_files:
                results[str(year)] = {
                    'year': year,
                    'error': f'{year}年数据文件不存在'
                }
                failed_years.append(year)
                print(f"❌ {year}年: 文件不存在")
                continue
            
            filepath = self.available_files[year]
            result = self.query_single_coordinate(filepath, latitude, longitude)
            result['year'] = year
            results[str(year)] = result
            
            if 'error' in result:
                failed_years.append(year)
                print(f"❌ {year}年: {result['error']}")
            else:
                successful_years.append(year)
                density = result['population_data']['density_per_km2']
                total_pop = result['population_data']['total_population_in_pixel']
                print(f"✅ {year}年: {density:.2f} 人/km² (该像素总人口: {total_pop:.0f})")
        
        # 生成汇总信息
        summary = {
            'query_info': {
                'coordinate': {'latitude': latitude, 'longitude': longitude},
                'requested_years': years,
                'successful_years': successful_years,
                'failed_years': failed_years,
                'success_rate': len(successful_years) / len(years) * 100 if years else 0
            },
            'yearly_data': results
        }
        
        return summary
    
    def display_results(self, result: Dict[str, Any]):
        """显示查询结果"""
        if 'yearly_data' in result:
            # 多年份结果
            self._display_multi_year_results(result)
        else:
            # 单年份结果
            self._display_single_year_result(result)
    
    def _display_single_year_result(self, result: Dict[str, Any]):
        """显示单年份结果"""
        if 'error' in result:
            print(f"❌ 查询失败: {result['error']}")
            return
        
        print(f"\n📊 {result['year']}年人口密度数据")
        print("=" * 60)
        
        coord = result['coordinate']
        pop_data = result['population_data']
        stats = result['surrounding_stats']
        radius_stats = result['radius_analysis']
        
        print(f"📍 查询坐标: ({coord['latitude']}, {coord['longitude']})")
        print(f"🎯 像素位置: 第{coord['pixel_row']}行, 第{coord['pixel_col']}列")
        
        print(f"\n👥 人口密度信息:")
        print(f"• 人口密度: {pop_data['density_per_km2']:.2f} 人/平方公里")
        print(f"• 该像素总人口: {pop_data['total_population_in_pixel']:.0f} 人")
        print(f"• 像素面积: {pop_data['pixel_area_km2']:.4f} 平方公里")
        
        print(f"\n🌐 周边区域统计 ({stats['window_size']}):")
        print(f"• 平均密度: {stats['mean_density']:.2f} 人/平方公里")
        print(f"• 中位数密度: {stats['median_density']:.2f} 人/平方公里")
        print(f"• 最高密度: {stats['max_density']:.2f} 人/平方公里")
        print(f"• 最低密度: {stats['min_density']:.2f} 人/平方公里")
        print(f"• 标准差: {stats['std_density']:.2f}")
        
        print(f"\n📐 不同半径范围分析:")
        for radius_key, radius_data in radius_stats.items():
            radius = radius_key.split('_')[1]
            print(f"• {radius}像素半径 (~{int(radius)*1:.1f}km): "
                  f"平均{radius_data['mean_density']:.1f}人/km², "
                  f"总人口{radius_data['total_population']:.0f}人, "
                  f"面积{radius_data['area_km2']:.1f}km²")
    
    def _display_multi_year_results(self, result: Dict[str, Any]):
        """显示多年份结果"""
        print(f"\n📊 多年份人口密度数据汇总")
        print("=" * 70)
        
        info = result['query_info']
        print(f"📍 查询坐标: ({info['coordinate']['latitude']}, {info['coordinate']['longitude']})")
        print(f"✅ 成功查询: {len(info['successful_years'])} 年")
        print(f"❌ 查询失败: {len(info['failed_years'])} 年")
        print(f"📈 成功率: {info['success_rate']:.1f}%")
        
        print(f"\n📋 历年数据对比:")
        print("-" * 70)
        print(f"{'年份':<6} {'人口密度':<12} {'像素人口':<10} {'周边平均':<12} {'状态':<8}")
        print("-" * 70)
        
        # 收集成功的数据用于趋势分析
        trend_data = []
        
        for year_str in sorted(result['yearly_data'].keys()):
            year_data = result['yearly_data'][year_str]
            year = year_data['year']
            
            if 'error' in year_data:
                print(f"{year:<6} {'N/A':<12} {'N/A':<10} {'N/A':<12} {'失败':<8}")
            else:
                density = year_data['population_data']['density_per_km2']
                total_pop = year_data['population_data']['total_population_in_pixel']
                avg_density = year_data['surrounding_stats']['mean_density']
                
                print(f"{year:<6} {density:<12.1f} {total_pop:<10.0f} {avg_density:<12.1f} {'成功':<8}")
                trend_data.append((year, density))
        
        # 趋势分析
        if len(trend_data) >= 2:
            trend_data.sort()
            first_year, first_density = trend_data[0]
            last_year, last_density = trend_data[-1]
            
            change = last_density - first_density
            change_rate = (change / first_density * 100) if first_density > 0 else 0
            
            print(f"\n📈 人口密度变化趋势:")
            print(f"• {first_year}年: {first_density:.1f} 人/平方公里")
            print(f"• {last_year}年: {last_density:.1f} 人/平方公里")
            print(f"• 绝对变化: {change:+.1f} 人/平方公里")
            print(f"• 相对变化: {change_rate:+.1f}%")
            
            # 年均变化率
            years_span = last_year - first_year
            if years_span > 0:
                annual_rate = ((last_density / first_density) ** (1/years_span) - 1) * 100 if first_density > 0 else 0
                print(f"• 年均增长率: {annual_rate:+.2f}%")
    
    def export_results(self, result: Dict[str, Any], filename: str = None):
        """导出查询结果"""
        if not filename:
            if 'yearly_data' in result:
                coord = result['query_info']['coordinate']
                lat, lon = coord['latitude'], coord['longitude']
                filename = f"population_multi_{lat}_{lon}.json"
            else:
                coord = result['coordinate']
                lat, lon = coord['latitude'], coord['longitude']
                year = result['year']
                filename = f"population_{year}_{lat}_{lon}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📁 结果已导出到: {filename}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")

def main():
    """主函数"""
    print("🏠 本地WorldPop人口密度查询工具")
    print("=" * 50)
    
    # 检查命令行参数中的数据目录
    data_dir = "."
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        data_dir = sys.argv[1]
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # 移除数据目录参数
    
    # 初始化查询器
    query_tool = LocalPopulationQuery(data_dir)
    
    if not query_tool.available_files:
        print("\n❌ 未找到WorldPop数据文件")
        print("📋 使用说明:")
        print("1. 下载WorldPop中国数据: https://data.worldpop.org/GIS/Population/Global_2000_2020/")
        print("2. 将文件命名为: chn_ppp_YYYY.tif (如: chn_ppp_2020.tif)")
        print("3. 将文件放在脚本同目录下")
        print("4. 重新运行脚本")
        return
    
    print(f"📅 可用年份: {', '.join(map(str, query_tool.list_available_years()))}")
    
    # 检查命令行参数
    if len(sys.argv) >= 3:
        try:
            lat = float(sys.argv[1])
            lon = float(sys.argv[2])
            
            if len(sys.argv) >= 4:
                # 指定年份
                year = int(sys.argv[3])
                if year in query_tool.available_files:
                    filepath = query_tool.available_files[year]
                    result = query_tool.query_single_coordinate(filepath, lat, lon)
                    result['year'] = year
                    query_tool.display_results(result)
                else:
                    print(f"❌ {year}年数据文件不存在")
            else:
                # 查询所有可用年份
                result = query_tool.query_multiple_years(lat, lon)
                query_tool.display_results(result)
                
                # 询问是否导出
                export = input("\n💾 是否导出结果? (y/n): ").lower()
                if export == 'y':
                    query_tool.export_results(result)
                    
        except ValueError:
            print("❌ 坐标格式错误")
            print("使用方法: python local_population_query.py 纬度 经度 [年份]")
            print("示例: python local_population_query.py 39.9042 116.4074 2020")
    else:
        # 交互式输入
        print("\n请输入查询坐标:")
        try:
            lat = float(input("纬度 (例如: 39.9042): "))
            lon = float(input("经度 (例如: 116.4074): "))
            
            available_years = query_tool.list_available_years()
            mode = input(f"查询模式 [1]指定年份 [2]所有年份 (默认所有): ").strip()
            
            if mode == '1':
                print(f"可用年份: {', '.join(map(str, available_years))}")
                year = int(input("选择年份: "))
                if year in query_tool.available_files:
                    filepath = query_tool.available_files[year]
                    result = query_tool.query_single_coordinate(filepath, lat, lon)
                    result['year'] = year
                    query_tool.display_results(result)
                else:
                    print(f"❌ {year}年数据文件不存在")
            else:
                result = query_tool.query_multiple_years(lat, lon)
                query_tool.display_results(result)
                
        except (ValueError, KeyboardInterrupt):
            print("❌ 输入错误或用户取消")

if __name__ == "__main__":
    main() 