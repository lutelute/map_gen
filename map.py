import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

def get_japan_map():
    """日本の地図データを取得"""
    # Natural Earth データから日本の境界データを取得
    url = "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        japan_data = response.json()
        return japan_data
    except requests.RequestException as e:
        print(f"データ取得エラー: {e}")
        return None

def plot_japan_map(geojson_data):
    """日本地図を描画"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    patches = []
    
    for feature in geojson_data['features']:
        geometry = feature['geometry']
        
        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]
            polygon = Polygon(coords, closed=True)
            patches.append(polygon)
        elif geometry['type'] == 'MultiPolygon':
            for polygon_coords in geometry['coordinates']:
                coords = polygon_coords[0]
                polygon = Polygon(coords, closed=True)
                patches.append(polygon)
    
    p = PatchCollection(patches, facecolor='lightblue', edgecolor='black', linewidth=0.5)
    ax.add_collection(p)
    
    ax.set_xlim(129, 146)
    ax.set_ylim(30, 46)
    ax.set_aspect('equal')
    ax.set_title('日本地図', fontsize=16, fontweight='bold')
    ax.set_xlabel('経度')
    ax.set_ylabel('緯度')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("日本地図データを取得中...")
    japan_geojson = get_japan_map()
    
    if japan_geojson:
        print("地図を描画中...")
        plot_japan_map(japan_geojson)
    else:
        print("地図データの取得に失敗しました。")