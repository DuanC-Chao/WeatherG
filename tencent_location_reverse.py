#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯地图SDK坐标逆编码测试脚本
坐标 -> 建筑名称、片区名称、城市名称
"""

import requests
import json
import sys
from typing import Dict, Optional

class TencentMapReverseGeocoder:
    """腾讯地图逆地址编码工具类"""
    
    def __init__(self, api_key: str):
        """
        初始化腾讯地图逆编码器
        
        Args:
            api_key: 腾讯地图API密钥
        """
        self.api_key = api_key
        self.base_url = "https://apis.map.qq.com/ws/geocoder/v1/"
    
    def reverse_geocode(self, lat: float, lng: float, get_poi: bool = True) -> Optional[Dict]:
        """
        坐标逆编码获取地址信息
        
        Args:
            lat: 纬度
            lng: 经度
            get_poi: 是否获取周边POI信息
        
        Returns:
            解析后的地址信息字典，失败返回None
        """
        try:
            # 构建请求参数
            params = {
                'location': f"{lat},{lng}",
                'key': self.api_key,
                'get_poi': 1 if get_poi else 0,
                'poi_options': 'address_format=short;radius=1000;page_size=10;policy=1'
            }
            
            # 发送请求
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 0:
                    return data
                else:
                    print(f"腾讯地图API错误: {data.get('message', '未知错误')}")
                    return None
            else:
                print(f"HTTP请求失败: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求异常: {e}")
            return None
        except Exception as e:
            print(f"逆编码失败: {e}")
            return None
    
    def parse_location_info(self, geocode_result: Dict) -> Dict:
        """
        解析地址信息，提取关键信息
        
        Args:
            geocode_result: 腾讯地图API返回的结果
        
        Returns:
            解析后的位置信息
        """
        if not geocode_result or geocode_result.get('status') != 0:
            return {}
        
        result = geocode_result.get('result', {})
        
        # 基本地址信息
        address = result.get('address', '')
        address_component = result.get('address_component', {})
        
        # 地址描述
        formatted_addresses = result.get('formatted_addresses', {})
        
        # 行政区划信息
        ad_info = result.get('ad_info', {})
        
        # 地址参考信息
        address_reference = result.get('address_reference', {})
        
        # POI信息
        pois = result.get('pois', [])
        
        location_info = {
            # 基础地址信息
            'address': address,
            'province': address_component.get('province', ''),
            'city': address_component.get('city', ''),
            'district': address_component.get('district', ''),
            'street': address_component.get('street', ''),
            'street_number': address_component.get('street_number', ''),
            
            # 格式化地址
            'recommend_address': formatted_addresses.get('recommend', ''),
            'rough_address': formatted_addresses.get('rough', ''),
            
            # 行政区划
            'adcode': ad_info.get('adcode', ''),
            'nation': ad_info.get('nation', ''),
            
            # 地址参考
            'famous_area': self._extract_reference_info(address_reference.get('famous_area')),
            'landmark_l1': self._extract_reference_info(address_reference.get('landmark_l1')),
            'landmark_l2': self._extract_reference_info(address_reference.get('landmark_l2')),
            'town': self._extract_reference_info(address_reference.get('town')),
            
            # POI信息（最近的几个）
            'nearby_pois': self._extract_poi_info(pois[:20])
        }
        
        return location_info
    
    def _extract_reference_info(self, reference_obj) -> Dict:
        """提取参考位置信息"""
        if not reference_obj:
            return {}
        
        return {
            'title': reference_obj.get('title', ''),
            'distance': reference_obj.get('_distance', 0),
            'direction': reference_obj.get('_dir_desc', '')
        }
    
    def _extract_poi_info(self, pois) -> list:
        """提取POI信息"""
        poi_list = []
        for poi in pois:
            poi_info = {
                'title': poi.get('title', ''),
                'address': poi.get('address', ''),
                'category': poi.get('category', ''),
                'distance': poi.get('_distance', 0)
            }
            poi_list.append(poi_info)
        return poi_list

def print_location_details(location_info: Dict):
    """
    打印位置详细信息
    """
    print("地址逆编码结果:")
    print("=" * 60)
    
    # 基础信息
    print(f"完整地址: {location_info.get('address', '未知')}")
    print(f"推荐地址: {location_info.get('recommend_address', '未知')}")
    print(f"粗略地址: {location_info.get('rough_address', '未知')}")
    
    # 行政区划
    print(f"\n行政区划:")
    print(f"  国家: {location_info.get('nation', '未知')}")
    print(f"  省份: {location_info.get('province', '未知')}")
    print(f"  城市: {location_info.get('city', '未知')}")
    print(f"  区县: {location_info.get('district', '未知')}")
    print(f"  街道: {location_info.get('street', '未知')}")
    print(f"  门牌号: {location_info.get('street_number', '未知')}")
    print(f"  行政代码: {location_info.get('adcode', '未知')}")
    
    # 地标信息
    print(f"\n地标参考:")
    famous_area = location_info.get('famous_area', {})
    if famous_area.get('title'):
        print(f"  知名区域: {famous_area['title']} (距离: {famous_area.get('distance', 0)}米, 方位: {famous_area.get('direction', '')})")
    
    landmark_l1 = location_info.get('landmark_l1', {})
    if landmark_l1.get('title'):
        print(f"  一级地标: {landmark_l1['title']} (距离: {landmark_l1.get('distance', 0)}米, 方位: {landmark_l1.get('direction', '')})")
    
    landmark_l2 = location_info.get('landmark_l2', {})
    if landmark_l2.get('title'):
        print(f"  二级地标: {landmark_l2['title']} (距离: {landmark_l2.get('distance', 0)}米, 方位: {landmark_l2.get('direction', '')})")
    
    town = location_info.get('town', {})
    if town.get('title'):
        print(f"  乡镇街道: {town['title']} (距离: {town.get('distance', 0)}米, 方位: {town.get('direction', '')})")
    
    # 附近POI
    nearby_pois = location_info.get('nearby_pois', [])
    if nearby_pois:
        print(f"\n附近建筑/POI (前20个):")
        for i, poi in enumerate(nearby_pois, 1):
            print(f"  {i}. {poi['title']}")
            print(f"     类别: {poi['category']}")
            print(f"     地址: {poi['address']}")
            print(f"     距离: {poi['distance']}米")
            print()

def test_coordinates():
    """测试几个坐标点"""
    test_locations = [
        (39.9042, 116.4074, "北京天安门"),
        (31.2304, 121.4737, "上海外滩"),
        (22.5431, 114.0579, "深圳市中心"),
        (39.0968, -120.0324, "太浩湖"),
        (25.0330, 121.5654, "台北101")
    ]
    
    return test_locations

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python tencent_location_reverse.py <API_KEY> [纬度] [经度]")
        print("  python tencent_location_reverse.py <API_KEY> test")
        print()
        print("参数说明:")
        print("  API_KEY: 腾讯地图API密钥")
        print("  纬度: -90 到 90 之间的数值")
        print("  经度: -180 到 180 之间的数值")
        print("  test: 运行预设测试点")
        print()
        print("获取API密钥:")
        print("  1. 访问 https://lbs.qq.com/")
        print("  2. 注册并登录腾讯位置服务")
        print("  3. 创建应用并获取Key")
        print()
        print("示例:")
        print("  python tencent_location_reverse.py YOUR_API_KEY 39.9042 116.4074")
        print("  python tencent_location_reverse.py YOUR_API_KEY test")
        return
    
    api_key = sys.argv[1]
    
    if not api_key:
        print("错误: 请提供有效的API密钥")
        return
    
    # 创建逆编码器
    geocoder = TencentMapReverseGeocoder(api_key)
    
    if len(sys.argv) >= 4:
        # 单个坐标测试
        try:
            lat = float(sys.argv[2])
            lng = float(sys.argv[3])
            
            if not (-90 <= lat <= 90):
                print("错误: 纬度必须在-90到90之间")
                return
            if not (-180 <= lng <= 180):
                print("错误: 经度必须在-180到180之间")
                return
            
            print(f"查询坐标: ({lat}, {lng})")
            print("=" * 60)
            
            # 执行逆编码
            result = geocoder.reverse_geocode(lat, lng)
            
            if result:
                location_info = geocoder.parse_location_info(result)
                print_location_details(location_info)
            else:
                print("逆编码失败!")
                
        except ValueError:
            print("错误: 坐标格式不正确，请输入有效的数字")
        except Exception as e:
            print(f"发生错误: {e}")
    
    elif len(sys.argv) == 3 and sys.argv[2].lower() == 'test':
        # 批量测试模式
        test_locations = test_coordinates()
        
        print("批量测试模式")
        print("=" * 60)
        
        for lat, lng, name in test_locations:
            print(f"\n🔍 测试点: {name} ({lat}, {lng})")
            print("-" * 40)
            
            result = geocoder.reverse_geocode(lat, lng)
            
            if result:
                location_info = geocoder.parse_location_info(result)
                
                # 简化输出，只显示关键信息
                print(f"完整地址: {location_info.get('address', '未知')}")
                print(f"行政区划: {location_info.get('province', '')} > {location_info.get('city', '')} > {location_info.get('district', '')}")
                
                # 显示最近的建筑
                pois = location_info.get('nearby_pois', [])
                if pois:
                    print(f"最近建筑: {pois[0]['title']} ({pois[0]['distance']}米)")
                
                # 显示地标
                landmark = location_info.get('landmark_l1', {}) or location_info.get('famous_area', {})
                if landmark.get('title'):
                    print(f"地标参考: {landmark['title']}")
            else:
                print("❌ 逆编码失败")
            
            print()
    
    else:
        print("参数不足，请指定坐标或使用 'test' 参数进行批量测试")

if __name__ == "__main__":
    main() 