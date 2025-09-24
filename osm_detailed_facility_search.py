#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenStreetMap详细设施搜索工具
搜索指定坐标周围的设施并输出最详细的信息
基于Overpass API
"""

import requests
import json
import sys
import time
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class OSMDetailedFacilitySearcher:
    """OpenStreetMap详细设施搜索工具"""
    
    def __init__(self):
        """初始化OSM搜索器"""
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        
        # 定义要搜索的设施类型及其OSM标签
        self.facility_types = {
            # 水体设施
            '水库': {
                'queries': [
                    'way[landuse=reservoir]',
                    'way[natural=water][water=reservoir]',
                    'relation[landuse=reservoir]',
                    'relation[natural=water][water=reservoir]'
                ],
                'color': '#0066CC',
                'icon': '🏞️',
                'category': '水体设施'
            },
            '河流': {
                'queries': [
                    'way[waterway=river]',
                    'way[waterway=stream]',
                    'relation[waterway=river]',
                    'way[waterway=canal]'
                ],
                'color': '#0088FF',
                'icon': '🏞️',
                'category': '水体设施'
            },
            '湖泊': {
                'queries': [
                    'way[natural=water][water=lake]',
                    'way[natural=water][!water]',
                    'relation[natural=water][water=lake]',
                    'relation[natural=water][!water]'
                ],
                'color': '#0099FF',
                'icon': '🏞️',
                'category': '水体设施'
            },
            
            # 污水处理设施
            '污水处理设施': {
                'queries': [
                    'way[man_made=wastewater_plant]',
                    'way[man_made=sewage_disposal]',
                    'node[man_made=wastewater_plant]',
                    'relation[man_made=wastewater_plant]'
                ],
                'color': '#8B4513',
                'icon': '🏭',
                'category': '环保设施'
            },
            
            # 绿地和公园
            '公园': {
                'queries': [
                    'way[leisure=park]',
                    'way[boundary=national_park]',
                    'relation[leisure=park]',
                    'relation[boundary=national_park]',
                    'way[leisure=nature_reserve]'
                ],
                'color': '#00AA00',
                'icon': '🌳',
                'category': '绿地设施'
            },
            '绿地': {
                'queries': [
                    'way[landuse=grass]',
                    'way[leisure=garden]',
                    'way[landuse=meadow]',
                    'way[natural=grassland]',
                    'way[leisure=common]'
                ],
                'color': '#90EE90',
                'icon': '🌱',
                'category': '绿地设施'
            },
            '林地': {
                'queries': [
                    'way[natural=wood]',
                    'way[landuse=forest]',
                    'relation[natural=wood]',
                    'relation[landuse=forest]',
                    'way[natural=scrub]'
                ],
                'color': '#228B22',
                'icon': '🌲',
                'category': '绿地设施'
            },
            
            # 居住区域
            '居民区': {
                'queries': [
                    'way[landuse=residential]',
                    'way[place=neighbourhood]',
                    'node[place=village]',
                    'node[place=hamlet]',
                    'relation[landuse=residential]',
                    'node[place=suburb]'
                ],
                'color': '#FFD700',
                'icon': '🏘️',
                'category': '居住设施'
            },
            
            # 公共交通设施
            '公共交通设施': {
                'queries': [
                    'node[amenity=bus_station]',
                    'node[highway=bus_stop]',
                    'node[railway=station]',
                    'node[railway=halt]',
                    'way[amenity=bus_station]',
                    'way[public_transport=platform]',
                    'node[public_transport=stop_position]'
                ],
                'color': '#FF6600',
                'icon': '🚌',
                'category': '交通设施'
            },
            
            # 农贸市场
            '农贸市场': {
                'queries': [
                    'node[amenity=marketplace]',
                    'way[amenity=marketplace]',
                    'node[shop=farm]',
                    'way[shop=farm]',
                    'way[landuse=commercial][commercial=market]'
                ],
                'color': '#FF4500',
                'icon': '🛒',
                'category': '商业设施'
            },
            
            # 牲畜养殖设施
            '牲畜养殖设施': {
                'queries': [
                    'way[landuse=farmyard]',
                    'way[building=farm_auxiliary]',
                    'way[building=cowshed]',
                    'way[building=stable]',
                    'node[amenity=animal_shelter]',
                    'way[building=barn]'
                ],
                'color': '#D2691E',
                'icon': '🐄',
                'category': '农业设施'
            }
        }
        
        # 中文标签翻译字典
        self.tag_translations = {
            # 基础标签
            'name': '名称',
            'name:zh': '中文名称',
            'name:en': '英文名称',
            'ref': '编号',
            'description': '描述',
            'operator': '运营商',
            'owner': '所有者',
            'contact:phone': '联系电话',
            'contact:website': '网站',
            'opening_hours': '开放时间',
            
            # 地理标签
            'natural': '自然地物',
            'landuse': '土地利用',
            'leisure': '休闲设施',
            'amenity': '便民设施',
            'man_made': '人造设施',
            'waterway': '水道',
            'building': '建筑物',
            'highway': '道路',
            'railway': '铁路',
            'shop': '商店',
            'place': '地点',
            'boundary': '边界',
            'public_transport': '公共交通',
            
            # 具体值翻译
            'water': '水体类型',
            'lake': '湖泊',
            'river': '河流',
            'reservoir': '水库',
            'pond': '池塘',
            'stream': '溪流',
            'canal': '运河',
            
            'park': '公园',
            'garden': '花园',
            'nature_reserve': '自然保护区',
            'national_park': '国家公园',
            'common': '公共绿地',
            
            'residential': '居住区',
            'commercial': '商业区',
            'industrial': '工业区',
            'farmyard': '农场',
            'forest': '森林',
            'grass': '草地',
            'meadow': '草甸',
            
            'bus_station': '公交车站',
            'bus_stop': '公交站点',
            'railway_station': '火车站',
            'subway_entrance': '地铁入口',
            
            'wastewater_plant': '污水处理厂',
            'sewage_disposal': '污水处理',
            
            'marketplace': '市场',
            'farm': '农场',
            
            'village': '村庄',
            'hamlet': '小村',
            'suburb': '郊区',
            'neighbourhood': '街区'
        }
    
    def search_facilities_around_point(self, lat: float, lng: float, radius: int = 1000) -> Dict:
        """
        搜索指定坐标周围的设施
        
        Args:
            lat: 纬度
            lng: 经度  
            radius: 搜索半径（米），默认1000米
            
        Returns:
            包含所有设施详细信息的字典
        """
        results = {}
        search_center = (lat, lng)
        
        print(f"🔍 详细搜索坐标 ({lat:.6f}, {lng:.6f}) 周围 {radius}米 范围内的设施...")
        print("=" * 80)
        
        for facility_type, config in self.facility_types.items():
            print(f"\n{config['icon']} 正在搜索 {facility_type} ({config['category']})...")
            
            facilities = self._search_single_facility_type(lat, lng, radius, facility_type, config, search_center)
            
            if facilities:
                results[facility_type] = facilities
                print(f"   ✅ 找到 {len(facilities)} 个{facility_type}")
            else:
                print(f"   ❌ 未找到{facility_type}")
                
            # 避免请求过于频繁
            time.sleep(0.3)
        
        return results
    
    def _search_single_facility_type(self, lat: float, lng: float, radius: int, 
                                   facility_type: str, config: Dict, search_center: Tuple[float, float]) -> List[Dict]:
        """搜索单一类型的设施"""
        all_facilities = []
        
        for query_template in config['queries']:
            try:
                # 构建更详细的Overpass查询，包含几何信息
                overpass_query = f"""
                [out:json][timeout:45];
                (
                  {query_template}(around:{radius},{lat},{lng});
                );
                out center meta geom;
                """
                
                response = requests.post(
                    self.overpass_url,
                    data={'data': overpass_query},
                    timeout=45
                )
                
                if response.status_code == 200:
                    data = response.json()
                    elements = data.get('elements', [])
                    
                    for element in elements:
                        facility_info = self._parse_element_detailed(element, facility_type, config, search_center)
                        if facility_info:
                            all_facilities.append(facility_info)
                            
                else:
                    print(f"   ⚠️  查询失败: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  网络请求异常: {e}")
            except Exception as e:
                print(f"   ⚠️  查询异常: {e}")
        
        # 去重并按距离排序
        unique_facilities = {}
        for facility in all_facilities:
            facility_id = facility['osm_id']
            if facility_id not in unique_facilities:
                unique_facilities[facility_id] = facility
        
        # 按距离排序
        sorted_facilities = sorted(unique_facilities.values(), key=lambda x: x['distance'])
        return sorted_facilities
    
    def _parse_element_detailed(self, element: Dict, facility_type: str, config: Dict, search_center: Tuple[float, float]) -> Optional[Dict]:
        """详细解析OSM元素"""
        try:
            # 获取坐标
            if 'lat' in element and 'lon' in element:
                lat, lng = element['lat'], element['lon']
            elif 'center' in element:
                lat, lng = element['center']['lat'], element['center']['lon']
            else:
                return None
            
            # 计算距离
            distance = self._calculate_distance(search_center[0], search_center[1], lat, lng)
            
            # 获取标签
            tags = element.get('tags', {})
            
            # 获取名称（多种语言）
            names = {}
            name_keys = ['name', 'name:zh', 'name:en', 'name:zh-Hans', 'name:zh-Hant']
            for key in name_keys:
                if key in tags:
                    names[key] = tags[key]
            
            primary_name = (tags.get('name:zh') or 
                           tags.get('name') or 
                           tags.get('ref') or
                           f"{facility_type}_{element['id']}")
            
            # 获取几何信息
            geometry_info = self._extract_geometry_info(element)
            
            # 获取联系信息
            contact_info = self._extract_contact_info(tags)
            
            # 获取时间信息
            time_info = self._extract_time_info(tags)
            
            # 获取详细属性
            detailed_attributes = self._extract_detailed_attributes(tags, facility_type)
            
            # 翻译标签
            translated_tags = self._translate_tags(tags)
            
            return {
                # 基本信息
                'osm_id': f"{element['type']}_{element['id']}",
                'osm_type': element['type'],
                'osm_internal_id': element['id'],
                'facility_type': facility_type,
                'category': config['category'],
                'icon': config['icon'],
                'color': config['color'],
                
                # 名称信息
                'primary_name': primary_name,
                'names': names,
                
                # 位置信息
                'coordinates': {
                    'lat': lat,
                    'lng': lng,
                    'formatted': f"{lat:.6f}, {lng:.6f}"
                },
                'distance': distance,
                'distance_formatted': f"{distance:.0f}米" if distance < 1000 else f"{distance/1000:.1f}公里",
                
                # 几何信息
                'geometry': geometry_info,
                
                # 联系信息
                'contact': contact_info,
                
                # 时间信息
                'time_info': time_info,
                
                # 详细属性
                'attributes': detailed_attributes,
                
                # 原始OSM标签
                'osm_tags': tags,
                'translated_tags': translated_tags,
                
                # 元数据
                'last_modified': element.get('timestamp', '未知'),
                'version': element.get('version', '未知'),
                'changeset': element.get('changeset', '未知')
            }
            
        except Exception as e:
            print(f"   ⚠️  解析元素失败: {e}")
            return None
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算两点间距离（米）"""
        R = 6371000  # 地球半径（米）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _extract_geometry_info(self, element: Dict) -> Dict:
        """提取几何信息"""
        geometry_info = {
            'type': element['type'],
            'has_geometry': 'geometry' in element
        }
        
        if 'geometry' in element:
            geometry = element['geometry']
            if geometry:
                geometry_info['point_count'] = len(geometry)
                
                # 计算边界框
                lats = [point['lat'] for point in geometry if 'lat' in point]
                lngs = [point['lon'] for point in geometry if 'lon' in point]
                
                if lats and lngs:
                    geometry_info['bounds'] = {
                        'north': max(lats),
                        'south': min(lats),
                        'east': max(lngs),
                        'west': min(lngs)
                    }
                    
                    # 估算面积（对于way和relation）
                    if element['type'] in ['way', 'relation'] and len(geometry) > 2:
                        area = self._calculate_polygon_area(geometry)
                        geometry_info['estimated_area'] = area
                        geometry_info['area_formatted'] = self._format_area(area)
        
        return geometry_info
    
    def _calculate_polygon_area(self, geometry: List[Dict]) -> float:
        """计算多边形面积（平方米）"""
        if len(geometry) < 3:
            return 0
        
        # 使用Shoelace公式计算面积
        area = 0
        n = len(geometry)
        
        for i in range(n):
            j = (i + 1) % n
            lat1, lng1 = geometry[i]['lat'], geometry[i]['lon']
            lat2, lng2 = geometry[j]['lat'], geometry[j]['lon']
            
            # 转换为墨卡托投影坐标进行面积计算
            x1, y1 = self._lat_lng_to_meters(lat1, lng1)
            x2, y2 = self._lat_lng_to_meters(lat2, lng2)
            
            area += x1 * y2 - x2 * y1
        
        return abs(area) / 2
    
    def _lat_lng_to_meters(self, lat: float, lng: float) -> Tuple[float, float]:
        """将经纬度转换为墨卡托投影米制坐标"""
        x = lng * 111320 * math.cos(math.radians(lat))
        y = lat * 110540
        return x, y
    
    def _format_area(self, area: float) -> str:
        """格式化面积显示"""
        if area < 1000:
            return f"{area:.0f}平方米"
        elif area < 1000000:
            return f"{area/1000:.1f}公顷"
        else:
            return f"{area/1000000:.2f}平方公里"
    
    def _extract_contact_info(self, tags: Dict) -> Dict:
        """提取联系信息"""
        contact_keys = [
            'phone', 'contact:phone', 'telephone',
            'website', 'contact:website', 'url',
            'email', 'contact:email',
            'facebook', 'contact:facebook',
            'addr:full', 'addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode'
        ]
        
        contact_info = {}
        for key in contact_keys:
            if key in tags:
                contact_info[key] = tags[key]
        
        # 构建完整地址
        addr_parts = []
        addr_keys = ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode']
        for key in addr_keys:
            if key in tags:
                addr_parts.append(tags[key])
        
        if addr_parts:
            contact_info['formatted_address'] = ' '.join(addr_parts)
        elif 'addr:full' in tags:
            contact_info['formatted_address'] = tags['addr:full']
        
        return contact_info
    
    def _extract_time_info(self, tags: Dict) -> Dict:
        """提取时间相关信息"""
        time_keys = [
            'opening_hours', 'service_times', 'operating_hours',
            'seasonal', 'access_times'
        ]
        
        time_info = {}
        for key in time_keys:
            if key in tags:
                time_info[key] = tags[key]
        
        return time_info
    
    def _extract_detailed_attributes(self, tags: Dict, facility_type: str) -> Dict:
        """提取详细属性信息"""
        attributes = {}
        
        # 通用属性
        general_keys = [
            'access', 'fee', 'wheelchair', 'barrier', 'surface',
            'capacity', 'levels', 'height', 'width', 'length',
            'material', 'condition', 'usage', 'status'
        ]
        
        for key in general_keys:
            if key in tags:
                attributes[key] = tags[key]
        
        # 特定设施类型的属性
        if facility_type in ['公园', '绿地', '林地']:
            nature_keys = ['trees', 'leaf_type', 'leaf_cycle', 'genus', 'species']
            for key in nature_keys:
                if key in tags:
                    attributes[key] = tags[key]
        
        elif facility_type in ['河流', '湖泊', '水库']:
            water_keys = ['depth', 'width', 'intermittent', 'salt', 'tidal']
            for key in water_keys:
                if key in tags:
                    attributes[key] = tags[key]
        
        elif facility_type == '公共交通设施':
            transport_keys = ['route', 'service', 'frequency', 'network', 'line']
            for key in transport_keys:
                if key in tags:
                    attributes[key] = tags[key]
        
        return attributes
    
    def _translate_tags(self, tags: Dict) -> Dict:
        """翻译OSM标签为中文"""
        translated = {}
        
        for key, value in tags.items():
            # 翻译键名
            translated_key = self.tag_translations.get(key, key)
            
            # 翻译值
            translated_value = self.tag_translations.get(value, value)
            
            translated[translated_key] = translated_value
        
        return translated
    
    def print_detailed_results(self, results: Dict, search_center: Tuple[float, float]):
        """详细打印搜索结果"""
        print("\n" + "=" * 80)
        print("🏞️ 详细搜索结果")
        print("=" * 80)
        
        if not results:
            print("❌ 未找到任何设施")
            return
        
        total_count = sum(len(facilities) for facilities in results.values())
        print(f"✅ 搜索中心: ({search_center[0]:.6f}, {search_center[1]:.6f})")
        print(f"📊 总共找到 {total_count} 个设施，分为 {len(results)} 个类别")
        print()
        
        # 按类别显示
        for facility_type, facilities in results.items():
            if not facilities:
                continue
                
            config = self.facility_types[facility_type]
            print(f"{config['icon']} {facility_type} ({config['category']}) - {len(facilities)}个")
            print("=" * 80)
            
            for i, facility in enumerate(facilities, 1):
                self._print_single_facility(facility, i)
                print("-" * 80)
    
    def _print_single_facility(self, facility: Dict, index: int):
        """打印单个设施的详细信息"""
        print(f"📍 {index}. {facility['primary_name']}")
        print(f"   🏷️  类型: {facility['facility_type']} ({facility['category']})")
        print(f"   📍 坐标: {facility['coordinates']['formatted']}")
        print(f"   📏 距离: {facility['distance_formatted']}")
        print(f"   🆔 OSM: {facility['osm_type']}/{facility['osm_internal_id']}")
        
        # 多语言名称
        if len(facility['names']) > 1:
            print(f"   🌐 名称信息:")
            for name_type, name_value in facility['names'].items():
                print(f"      {name_type}: {name_value}")
        
        # 几何信息
        geometry = facility['geometry']
        if geometry['has_geometry']:
            print(f"   📐 几何信息:")
            print(f"      类型: {geometry['type']}")
            if 'point_count' in geometry:
                print(f"      节点数: {geometry['point_count']}")
            if 'estimated_area' in geometry:
                print(f"      估算面积: {geometry['area_formatted']}")
            if 'bounds' in geometry:
                bounds = geometry['bounds']
                print(f"      边界: N{bounds['north']:.6f} S{bounds['south']:.6f} E{bounds['east']:.6f} W{bounds['west']:.6f}")
        
        # 联系信息
        if facility['contact']:
            print(f"   📞 联系信息:")
            for contact_type, contact_value in facility['contact'].items():
                if contact_type == 'formatted_address':
                    print(f"      地址: {contact_value}")
                elif 'phone' in contact_type:
                    print(f"      电话: {contact_value}")
                elif 'website' in contact_type or contact_type == 'url':
                    print(f"      网站: {contact_value}")
                elif 'email' in contact_type:
                    print(f"      邮箱: {contact_value}")
        
        # 时间信息
        if facility['time_info']:
            print(f"   ⏰ 时间信息:")
            for time_type, time_value in facility['time_info'].items():
                if time_type == 'opening_hours':
                    print(f"      开放时间: {time_value}")
                else:
                    print(f"      {time_type}: {time_value}")
        
        # 详细属性
        if facility['attributes']:
            print(f"   🏷️  详细属性:")
            for attr_key, attr_value in facility['attributes'].items():
                print(f"      {attr_key}: {attr_value}")
        
        # 翻译后的标签（只显示重要的）
        important_translated_tags = {}
        for key, value in facility['translated_tags'].items():
            if key in ['名称', '土地利用', '自然地物', '便民设施', '人造设施', '水道', '建筑物', '休闲设施']:
                important_translated_tags[key] = value
        
        if important_translated_tags:
            print(f"   🏷️  主要标签:")
            for tag_key, tag_value in important_translated_tags.items():
                print(f"      {tag_key}: {tag_value}")
        
        # 元数据
        print(f"   📊 数据信息:")
        print(f"      最后修改: {facility['last_modified']}")
        print(f"      版本: {facility['version']}")
        print(f"      变更集: {facility['changeset']}")
    
    def export_detailed_results(self, results: Dict, search_center: Tuple[float, float], filename: str = None):
        """导出详细结果到JSON文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"osm_detailed_facilities_{timestamp}.json"
        
        export_data = {
            'search_info': {
                'search_time': datetime.now().isoformat(),
                'search_center': {
                    'lat': search_center[0],
                    'lng': search_center[1]
                },
                'total_facilities': sum(len(facilities) for facilities in results.values()),
                'facility_types': len(results),
                'categories': list(set(config['category'] for config in self.facility_types.values()))
            },
            'statistics': {
                'by_type': {facility_type: len(facilities) for facility_type, facilities in results.items()},
                'by_category': self._get_category_statistics(results)
            },
            'results': results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 详细结果已导出到: {filename}")
            print(f"📊 文件大小: {self._get_file_size(filename)}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")
    
    def _get_category_statistics(self, results: Dict) -> Dict:
        """获取分类统计"""
        category_stats = {}
        for facility_type, facilities in results.items():
            category = self.facility_types[facility_type]['category']
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += len(facilities)
        return category_stats
    
    def _get_file_size(self, filename: str) -> str:
        """获取文件大小"""
        try:
            import os
            size = os.path.getsize(filename)
            if size < 1024:
                return f"{size}B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f}KB"
            else:
                return f"{size/(1024*1024):.2f}MB"
        except:
            return "未知"

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法:")
        print("  python osm_detailed_facility_search.py <纬度> <经度> [搜索半径(米)]")
        print()
        print("参数说明:")
        print("  纬度: -90 到 90 之间的数值")
        print("  经度: -180 到 180 之间的数值")
        print("  搜索半径: 默认1000米，建议不超过3000米")
        print()
        print("示例:")
        print("  python osm_detailed_facility_search.py 39.9042 116.4074")
        print("  python osm_detailed_facility_search.py 39.9042 116.4074 1500")
        print()
        print("🔍 支持搜索的设施类型:")
        searcher = OSMDetailedFacilitySearcher()
        categories = {}
        for facility_type, config in searcher.facility_types.items():
            category = config['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(f"{config['icon']} {facility_type}")
        
        for category, facilities in categories.items():
            print(f"  📂 {category}:")
            for facility in facilities:
                print(f"     {facility}")
        return
    
    try:
        lat = float(sys.argv[1])
        lng = float(sys.argv[2])
        radius = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
        
        if not (-90 <= lat <= 90):
            print("错误: 纬度必须在-90到90之间")
            return
        if not (-180 <= lng <= 180):
            print("错误: 经度必须在-180到180之间")
            return
        if not (100 <= radius <= 5000):
            print("错误: 搜索半径建议在100到5000米之间")
            return
        
        # 创建搜索器
        searcher = OSMDetailedFacilitySearcher()
        search_center = (lat, lng)
        
        # 执行搜索
        print(f"🚀 开始详细搜索...")
        start_time = time.time()
        
        results = searcher.search_facilities_around_point(lat, lng, radius)
        
        end_time = time.time()
        search_duration = end_time - start_time
        
        # 显示结果
        searcher.print_detailed_results(results, search_center)
        
        # 显示搜索统计
        print("\n" + "=" * 80)
        print("📊 搜索统计")
        print("=" * 80)
        print(f"⏱️  搜索耗时: {search_duration:.2f}秒")
        print(f"🎯 搜索半径: {radius}米")
        
        if results:
            category_stats = searcher._get_category_statistics(results)
            print(f"📈 分类统计:")
            for category, count in category_stats.items():
                print(f"   {category}: {count}个")
            
            # 导出结果
            searcher.export_detailed_results(results, search_center)
        else:
            print("💡 建议:")
            print("   1. 尝试增大搜索半径")
            print("   2. 更换搜索坐标")
            print("   3. 该区域可能OSM数据较少")
        
    except ValueError:
        print("错误: 坐标格式不正确，请输入有效的数字")
    except KeyboardInterrupt:
        print("\n用户中断搜索")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 