#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本電力グリッド可視化ツール (Enhanced Version)

このモジュールは日本の電力システムを可視化するための包括的なツールです。
9つの電力会社の位置、発電能力、相互接続を地図上に表示し、
ネットワーク理論に基づいたインピーダンス行列も生成します。

主な機能:
- 日本地図の取得と表示
- 電力会社の位置と発電能力の可視化
- 電力会社間の接続関係の表示
- CSVファイルによる設定の管理
- ネットワーク分析とインピーダンス計算
- カスタマイズ可能な表示オプション

作成者: Claude AI Assistant
作成日: 2025年
ライセンス: MIT License
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import requests
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon

# ========================================
# ログ設定
# ========================================

def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """
    ログシステムの初期化
    
    Args:
        log_level (str): ログレベル ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    
    Returns:
        logging.Logger: 設定されたロガー
    """
    # ログレベルの変換
    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    # ロガーの設定
    logger = logging.getLogger(__name__)
    logger.setLevel(level_mapping.get(log_level.upper(), logging.INFO))
    
    # ハンドラーが既に存在する場合は削除
    if logger.handlers:
        logger.handlers.clear()
    
    # フォーマッターの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # コンソールハンドラーの追加
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# ========================================
# 設定管理クラス
# ========================================

class PowerGridConfig:
    """
    電力グリッド可視化の設定を管理するクラス
    
    このクラスは表示オプション、色設定、サイズ設定など
    すべてのカスタマイズ可能なパラメータを管理します。
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        設定の初期化
        
        Args:
            config_file (Optional[str]): 設定ファイルのパス（JSON形式）
        """
        # デフォルト設定の定義
        self.default_config = {
            # 表示設定
            'display': {
                'figure_size': (14, 10),           # 図のサイズ (幅, 高さ)
                'title': '日本電力グリッド接続図',    # グラフのタイトル
                'show_grid': True,                 # グリッド線の表示
                'grid_alpha': 0.3,                # グリッド線の透明度
                'font_size_title': 16,            # タイトルのフォントサイズ
                'font_size_label': 12,            # ラベルのフォントサイズ
                'font_size_annotation': 9         # 注釈のフォントサイズ
            },
            # 地図設定
            'map': {
                'face_color': 'lightgray',         # 地図の塗りつぶし色
                'edge_color': 'none',              # 県境線の色
                'line_width': 0,                   # 県境線の太さ
                'alpha': 0.7,                      # 地図の透明度
                'show_boundaries': False           # 県境線の表示/非表示
            },
            # 円（電力会社）設定
            'circles': {
                'base_size': 800,                  # 基本サイズ
                'size_factor': 10,                 # サイズ計算の基準値（GW）
                'color': 'red',                    # 円の色
                'alpha': 1.0,                      # 透明度
                'edge_color': 'black',             # 輪郭線の色
                'edge_width': 2,                   # 輪郭線の太さ
                'show_capacity': True              # 発電能力の表示
            },
            # 接続線設定
            'connections': {
                'color': 'blue',                   # 接続線の色
                'width': 2,                        # 線の太さ
                'alpha': 0.7,                      # 透明度
                'style': '-'                       # 線のスタイル
            },
            # 地図範囲設定
            'bounds': {
                'lon_min': 129,                    # 経度の最小値
                'lon_max': 146,                    # 経度の最大値
                'lat_min': 30,                     # 緯度の最小値
                'lat_max': 46                      # 緯度の最大値
            },
            # データ設定
            'data': {
                'capacity_csv': 'power_capacity.csv',    # 発電能力CSVファイル
                'connections_csv': 'connections.csv',    # 接続関係CSVファイル
                'map_data_url': 'https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson'
            }
        }
        
        # 設定の読み込み
        self.config = self.default_config.copy()
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def load_config(self, config_file: str) -> None:
        """
        設定ファイルから設定を読み込み
        
        Args:
            config_file (str): 設定ファイルのパス
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 深いマージ（ネストした辞書も含む）
            self._deep_merge(self.config, user_config)
            
        except Exception as e:
            logging.warning(f"設定ファイルの読み込みに失敗: {e}")
            logging.info("デフォルト設定を使用します")
    
    def _deep_merge(self, base_dict: dict, update_dict: dict) -> None:
        """
        辞書の深いマージ
        
        Args:
            base_dict (dict): ベースとなる辞書
            update_dict (dict): 更新する辞書
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key_path: str, default=None):
        """
        ドット記法で設定値を取得
        
        Args:
            key_path (str): 設定のキーパス（例: 'display.figure_size'）
            default: デフォルト値
        
        Returns:
            設定値またはデフォルト値
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def save_config(self, config_file: str) -> None:
        """
        現在の設定をファイルに保存
        
        Args:
            config_file (str): 保存先のファイルパス
        """
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logging.info(f"設定を保存しました: {config_file}")
        except Exception as e:
            logging.error(f"設定の保存に失敗: {e}")

# ========================================
# データ取得・管理クラス
# ========================================

class DataManager:
    """
    地図データとCSVデータの取得・管理を行うクラス
    
    このクラスは外部APIからの地図データ取得、CSVファイルの読み込み、
    データの検証などを担当します。
    """
    
    def __init__(self, config: PowerGridConfig, logger: logging.Logger):
        """
        データマネージャーの初期化
        
        Args:
            config (PowerGridConfig): 設定オブジェクト
            logger (logging.Logger): ロガー
        """
        self.config = config
        self.logger = logger
        self.session = requests.Session()  # HTTP接続の再利用
        
        # タイムアウトとリトライの設定
        self.session.timeout = 30
        self.max_retries = 3
    
    def get_japan_map(self) -> Optional[dict]:
        """
        日本の地図データをGeoJSON形式で取得
        
        Returns:
            Optional[dict]: 地図データ（GeoJSON形式）、失敗時はNone
        """
        url = self.config.get('data.map_data_url')
        self.logger.info(f"地図データを取得中: {url}")
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()  # HTTPエラーの場合は例外を発生
                
                japan_data = response.json()
                
                # データの基本的な検証
                if not self._validate_geojson(japan_data):
                    raise ValueError("取得したGeoJSONデータが無効です")
                
                self.logger.info("地図データの取得が完了しました")
                return japan_data
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"タイムアウト (試行 {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    self.logger.error("地図データの取得がタイムアウトしました")
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"地図データ取得エラー: {e}")
                break
                
            except (ValueError, json.JSONDecodeError) as e:
                self.logger.error(f"地図データの解析エラー: {e}")
                break
        
        return None
    
    def _validate_geojson(self, geojson_data: dict) -> bool:
        """
        GeoJSONデータの基本検証
        
        Args:
            geojson_data (dict): 検証するGeoJSONデータ
        
        Returns:
            bool: 有効な場合True
        """
        try:
            # 基本構造の確認
            if 'type' not in geojson_data or geojson_data['type'] != 'FeatureCollection':
                return False
            
            if 'features' not in geojson_data or not isinstance(geojson_data['features'], list):
                return False
            
            # フィーチャーの確認
            for feature in geojson_data['features']:
                if 'geometry' not in feature or 'type' not in feature['geometry']:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def load_power_capacity(self, csv_file: str) -> Dict[str, float]:
        """
        CSVファイルから発電能力データを読み込み
        
        Args:
            csv_file (str): CSVファイルのパス
        
        Returns:
            Dict[str, float]: 電力会社名をキー、発電能力を値とする辞書
        """
        self.logger.info(f"発電能力データを読み込み中: {csv_file}")
        
        # デフォルトデータ（実際の概算値）
        default_data = {
            '北海道': 8.5, '東北': 17.2, '東京': 52.8, '中部': 32.1,
            '北陸': 7.3, '関西': 33.5, '中国': 12.8, '四国': 6.7, '九州': 18.9
        }
        
        try:
            # ファイルの存在確認
            if not os.path.exists(csv_file):
                self.logger.warning(f"CSVファイルが見つかりません: {csv_file}")
                self.logger.info("デフォルトの発電能力データを使用します")
                return default_data
            
            # CSVファイルの読み込み
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # データの検証
            required_columns = ['電力会社', '発電能力_GW']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"必要な列が見つかりません: {required_columns}")
            
            # 辞書への変換
            power_capacity = {}
            for _, row in df.iterrows():
                company = str(row['電力会社']).strip()
                try:
                    capacity = float(row['発電能力_GW'])
                    if capacity < 0:
                        self.logger.warning(f"負の発電能力が検出されました: {company} = {capacity}")
                        capacity = 0
                    power_capacity[company] = capacity
                except (ValueError, TypeError):
                    self.logger.warning(f"無効な発電能力データ: {company} = {row['発電能力_GW']}")
            
            self.logger.info(f"発電能力データを読み込みました: {len(power_capacity)}社")
            return power_capacity
            
        except Exception as e:
            self.logger.error(f"CSVファイル読み込みエラー: {e}")
            self.logger.info("デフォルトの発電能力データを使用します")
            return default_data
    
    def load_connections(self, csv_file: str) -> List[Tuple[str, str]]:
        """
        CSVファイルから接続関係データを読み込み
        
        Args:
            csv_file (str): CSVファイルのパス
        
        Returns:
            List[Tuple[str, str]]: 接続関係のタプルのリスト
        """
        self.logger.info(f"接続関係データを読み込み中: {csv_file}")
        
        # デフォルトの接続関係
        default_connections = [
            ('北海道', '東北'), ('東北', '東京'), ('東京', '中部'),
            ('中部', '北陸'), ('中部', '関西'), ('北陸', '関西'),
            ('関西', '中国'), ('関西', '四国'), ('中国', '九州')
        ]
        
        try:
            # ファイルの存在確認
            if not os.path.exists(csv_file):
                self.logger.warning(f"CSVファイルが見つかりません: {csv_file}")
                self.logger.info("デフォルトの接続関係データを使用します")
                return default_connections
            
            # CSVファイルの読み込み
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # データの検証
            required_columns = ['電力会社1', '電力会社2']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"必要な列が見つかりません: {required_columns}")
            
            # 接続関係の構築
            connections = []
            for _, row in df.iterrows():
                company1 = str(row['電力会社1']).strip()
                company2 = str(row['電力会社2']).strip()
                
                # 有効性の確認
                if company1 and company2 and company1 != company2:
                    connections.append((company1, company2))
                else:
                    self.logger.warning(f"無効な接続関係: {company1} - {company2}")
            
            self.logger.info(f"接続関係データを読み込みました: {len(connections)}接続")
            return connections
            
        except Exception as e:
            self.logger.error(f"CSVファイル読み込みエラー: {e}")
            self.logger.info("デフォルトの接続関係データを使用します")
            return default_connections

# ========================================
# メイン電力グリッドクラス
# ========================================

class PowerGridEnhanced:
    """
    高機能日本電力グリッド可視化クラス
    
    このクラスは電力システムの完全な可視化と分析機能を提供します。
    ネットワーク理論、グラフ理論、統計分析を含む包括的な機能を持ちます。
    """
    
    def __init__(self, 
                 config: Optional[PowerGridConfig] = None,
                 capacity_csv: Optional[str] = None,
                 connections_csv: Optional[str] = None,
                 log_level: str = 'INFO'):
        """
        電力グリッドシステムの初期化
        
        Args:
            config (Optional[PowerGridConfig]): 設定オブジェクト
            capacity_csv (Optional[str]): 発電能力CSVファイルパス
            connections_csv (Optional[str]): 接続関係CSVファイルパス
            log_level (str): ログレベル
        """
        # ログシステムの初期化
        self.logger = setup_logging(log_level)
        self.logger.info("電力グリッドシステムを初期化中...")
        
        # 設定の初期化
        self.config = config or PowerGridConfig()
        
        # CSVファイルパスの設定（引数が指定された場合は優先）
        self.capacity_csv = capacity_csv or self.config.get('data.capacity_csv')
        self.connections_csv = connections_csv or self.config.get('data.connections_csv')
        
        # データマネージャーの初期化
        self.data_manager = DataManager(self.config, self.logger)
        
        # 電力会社の位置座標の定義（緯度、経度）
        # これらの座標は各電力会社の主要な発電・送電エリアの中心を表す
        self.power_companies = {
            '北海道': (43.2, 141.5),    # 札幌周辺
            '東北': (38.5, 140.5),      # 仙台周辺
            '東京': (35.7, 139.7),      # 東京都心
            '中部': (35.2, 137.0),      # 名古屋周辺
            '北陸': (36.8, 137.2),      # 富山周辺
            '関西': (34.7, 135.5),      # 大阪周辺
            '中国': (34.4, 132.5),      # 広島周辺
            '四国': (33.8, 133.5),      # 高松周辺
            '九州': (33.0, 130.5)       # 福岡周辺
        }\n        \n        # データの読み込み\n        self._load_data()\n        \n        # ネットワークグラフの構築\n        self._build_network()\n        \n        # インピーダンス行列の計算\n        self._calculate_impedance_matrix()\n        \n        self.logger.info(\"電力グリッドシステムの初期化が完了しました\")\n    \n    def _load_data(self) -> None:\n        \"\"\"\n        全データの読み込み処理\n        \"\"\"\n        # 発電能力データの読み込み\n        self.power_capacity = self.data_manager.load_power_capacity(self.capacity_csv)\n        \n        # 接続関係データの読み込み\n        self.connections = self.data_manager.load_connections(self.connections_csv)\n        \n        # データの整合性確認\n        self._validate_data()\n    \n    def _validate_data(self) -> None:\n        \"\"\"\n        読み込んだデータの整合性を確認\n        \"\"\"\n        # 発電能力データの確認\n        missing_companies = set(self.power_companies.keys()) - set(self.power_capacity.keys())\n        if missing_companies:\n            self.logger.warning(f\"発電能力データが不足: {missing_companies}\")\n            # 不足分をデフォルト値で補完\n            for company in missing_companies:\n                self.power_capacity[company] = 10.0  # デフォルト値\n        \n        # 接続関係の確認\n        valid_connections = []\n        for company1, company2 in self.connections:\n            if company1 in self.power_companies and company2 in self.power_companies:\n                valid_connections.append((company1, company2))\n            else:\n                self.logger.warning(f\"無効な接続関係を除外: {company1} - {company2}\")\n        \n        self.connections = valid_connections\n        self.logger.info(f\"有効な接続関係: {len(self.connections)}件\")\n    \n    def _build_network(self) -> None:\n        \"\"\"\n        NetworkXグラフの構築とネットワーク分析\n        \"\"\"\n        self.logger.info(\"ネットワークグラフを構築中...\")\n        \n        # グラフの作成\n        self.graph = nx.Graph()\n        \n        # ノード（電力会社）の追加\n        for company, capacity in self.power_capacity.items():\n            # ノードに属性を追加\n            self.graph.add_node(company, \n                              capacity=capacity,\n                              position=self.power_companies.get(company))\n        \n        # エッジ（接続関係）の追加\n        for company1, company2 in self.connections:\n            # エッジに重み（距離）を追加\n            if company1 in self.power_companies and company2 in self.power_companies:\n                pos1 = self.power_companies[company1]\n                pos2 = self.power_companies[company2]\n                # 地理的距離の計算（簡易版）\n                distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)\n                self.graph.add_edge(company1, company2, weight=distance)\n        \n        # ネットワーク統計の計算\n        self._calculate_network_statistics()\n    \n    def _calculate_network_statistics(self) -> None:\n        \"\"\"\n        ネットワークの統計情報を計算\n        \"\"\"\n        self.network_stats = {\n            'node_count': self.graph.number_of_nodes(),\n            'edge_count': self.graph.number_of_edges(),\n            'density': nx.density(self.graph),\n            'is_connected': nx.is_connected(self.graph),\n            'diameter': nx.diameter(self.graph) if nx.is_connected(self.graph) else None,\n            'average_clustering': nx.average_clustering(self.graph),\n            'average_shortest_path': nx.average_shortest_path_length(self.graph) if nx.is_connected(self.graph) else None\n        }\n        \n        self.logger.debug(f\"ネットワーク統計: {self.network_stats}\")\n    \n    def _calculate_impedance_matrix(self) -> None:\n        \"\"\"\n        インピーダンス行列の計算\n        \n        実際の電力システムでは、インピーダンスは送電線の抵抗、\n        リアクタンス、距離などに基づいて計算されます。\n        ここでは簡略化されたモデルを使用します。\n        \"\"\"\n        self.logger.info(\"インピーダンス行列を計算中...\")\n        \n        companies = list(self.power_companies.keys())\n        n = len(companies)\n        self.impedance_matrix = np.zeros((n, n))\n        \n        # 再現性のための乱数シードの設定\n        np.random.seed(42)\n        \n        for i, company1 in enumerate(companies):\n            for j, company2 in enumerate(companies):\n                if i == j:\n                    # 自己インピーダンス（発電能力に反比例）\n                    capacity = self.power_capacity.get(company1, 10)\n                    # 大きな発電能力ほど低いインピーダンス\n                    self.impedance_matrix[i][j] = np.random.uniform(0.1, 0.3) * (10 / capacity)\n                    \n                elif self.graph.has_edge(company1, company2):\n                    # 相互インピーダンス（距離に比例）\n                    edge_data = self.graph.get_edge_data(company1, company2)\n                    distance = edge_data.get('weight', 1.0)\n                    \n                    # 距離ベースのインピーダンス計算\n                    base_impedance = np.random.uniform(0.05, 0.15)\n                    distance_factor = distance / 10.0  # 正規化\n                    impedance = base_impedance * (1 + distance_factor)\n                    \n                    # 対称行列として設定\n                    self.impedance_matrix[i][j] = impedance\n                    self.impedance_matrix[j][i] = impedance\n                else:\n                    # 直接接続されていない場合は無限大（実際は0で表現）\n                    self.impedance_matrix[i][j] = 0\n        \n        self.company_names = companies\n        self.logger.info(\"インピーダンス行列の計算が完了しました\")\n    \n    def get_circle_size(self, company: str) -> float:\n        \"\"\"\n        発電能力に基づいて円のサイズを計算\n        \n        Args:\n            company (str): 電力会社名\n        \n        Returns:\n            float: 円のサイズ\n        \"\"\"\n        capacity = self.power_capacity.get(company, 10)\n        base_size = self.config.get('circles.base_size')\n        size_factor = self.config.get('circles.size_factor')\n        \n        # 発電能力に比例したサイズ計算\n        # 最小サイズを保証（10%）\n        min_ratio = 0.1\n        size_ratio = max(capacity / size_factor, min_ratio)\n        \n        return base_size * size_ratio\n    \n    def plot_power_grid_map(self, \n                           geojson_data: dict, \n                           save_path: Optional[str] = None,\n                           show_plot: bool = True) -> None:\n        \"\"\"\n        日本地図に電力グリッドを描画\n        \n        Args:\n            geojson_data (dict): 地図データ（GeoJSON形式）\n            save_path (Optional[str]): 画像の保存パス\n            show_plot (bool): プロットの表示フラグ\n        \"\"\"\n        self.logger.info(\"電力グリッド地図を描画中...\")\n        \n        # 図の初期化\n        fig_size = self.config.get('display.figure_size')\n        fig, ax = plt.subplots(1, 1, figsize=fig_size)\n        \n        # 日本地図の描画\n        self._draw_japan_map(ax, geojson_data)\n        \n        # 接続線の描画（下層）\n        self._draw_connections(ax)\n        \n        # 電力会社の円の描画（上層）\n        self._draw_power_companies(ax)\n        \n        # 軸とタイトルの設定\n        self._configure_plot(ax)\n        \n        # レイアウトの調整\n        plt.tight_layout()\n        \n        # 画像の保存\n        if save_path:\n            try:\n                plt.savefig(save_path, dpi=300, bbox_inches='tight')\n                self.logger.info(f\"画像を保存しました: {save_path}\")\n            except Exception as e:\n                self.logger.error(f\"画像の保存に失敗: {e}\")\n        \n        # プロットの表示\n        if show_plot:\n            plt.show()\n        else:\n            plt.close()\n    \n    def _draw_japan_map(self, ax, geojson_data: dict) -> None:\n        \"\"\"\n        日本地図の描画\n        \n        Args:\n            ax: Matplotlibの軸オブジェクト\n            geojson_data (dict): 地図データ\n        \"\"\"\n        patches = []\n        \n        # GeoJSONからポリゴンを抽出\n        for feature in geojson_data['features']:\n            geometry = feature['geometry']\n            \n            if geometry['type'] == 'Polygon':\n                # 単一ポリゴンの処理\n                coords = geometry['coordinates'][0]\n                polygon = Polygon(coords, closed=True)\n                patches.append(polygon)\n                \n            elif geometry['type'] == 'MultiPolygon':\n                # 複数ポリゴンの処理\n                for polygon_coords in geometry['coordinates']:\n                    coords = polygon_coords[0]\n                    polygon = Polygon(coords, closed=True)\n                    patches.append(polygon)\n        \n        # 地図の描画設定\n        face_color = self.config.get('map.face_color')\n        edge_color = self.config.get('map.edge_color')\n        line_width = self.config.get('map.line_width')\n        alpha = self.config.get('map.alpha')\n        \n        # パッチコレクションとして描画\n        patch_collection = PatchCollection(\n            patches, \n            facecolor=face_color, \n            edgecolor=edge_color, \n            linewidth=line_width, \n            alpha=alpha\n        )\n        ax.add_collection(patch_collection)\n    \n    def _draw_connections(self, ax) -> None:\n        \"\"\"\n        電力会社間の接続線を描画\n        \n        Args:\n            ax: Matplotlibの軸オブジェクト\n        \"\"\"\n        # 接続線の設定\n        line_color = self.config.get('connections.color')\n        line_width = self.config.get('connections.width')\n        line_alpha = self.config.get('connections.alpha')\n        line_style = self.config.get('connections.style')\n        \n        # 各接続線を描画\n        for company1, company2 in self.connections:\n            if company1 in self.power_companies and company2 in self.power_companies:\n                # 座標の取得\n                lat1, lon1 = self.power_companies[company1]\n                lat2, lon2 = self.power_companies[company2]\n                \n                # 線の描画（zorderで描画順序を制御）\n                ax.plot([lon1, lon2], [lat1, lat2], \n                       color=line_color, \n                       linewidth=line_width, \n                       alpha=line_alpha, \n                       linestyle=line_style, \n                       zorder=1)\n    \n    def _draw_power_companies(self, ax) -> None:\n        \"\"\"\n        電力会社の位置に円を描画\n        \n        Args:\n            ax: Matplotlibの軸オブジェクト\n        \"\"\"\n        # 円の設定\n        circle_color = self.config.get('circles.color')\n        circle_alpha = self.config.get('circles.alpha')\n        edge_color = self.config.get('circles.edge_color')\n        edge_width = self.config.get('circles.edge_width')\n        show_capacity = self.config.get('circles.show_capacity')\n        font_size = self.config.get('display.font_size_annotation')\n        \n        # 各電力会社の円を描画\n        for company, (lat, lon) in self.power_companies.items():\n            # 円のサイズ計算\n            circle_size = self.get_circle_size(company)\n            capacity = self.power_capacity.get(company, 0)\n            \n            # 円の描画（zorderで描画順序を制御）\n            ax.scatter(lon, lat, \n                      s=circle_size, \n                      c=circle_color, \n                      marker='o', \n                      alpha=circle_alpha,\n                      edgecolors=edge_color, \n                      linewidth=edge_width, \n                      zorder=2)\n            \n            # ラベルの作成\n            if show_capacity:\n                label = f'{company}\\n({capacity:.1f}GW)'\n            else:\n                label = company\n            \n            # ラベルの描画\n            ax.annotate(label, \n                       (lon, lat), \n                       xytext=(5, 5), \n                       textcoords='offset points', \n                       fontsize=font_size, \n                       fontweight='bold', \n                       ha='left', \n                       zorder=3)\n    \n    def _configure_plot(self, ax) -> None:\n        \"\"\"\n        プロットの軸とタイトルを設定\n        \n        Args:\n            ax: Matplotlibの軸オブジェクト\n        \"\"\"\n        # 表示範囲の設定\n        bounds = self.config.get('bounds')\n        ax.set_xlim(bounds['lon_min'], bounds['lon_max'])\n        ax.set_ylim(bounds['lat_min'], bounds['lat_max'])\n        ax.set_aspect('equal')\n        \n        # タイトルとラベルの設定\n        title = self.config.get('display.title')\n        title_font_size = self.config.get('display.font_size_title')\n        label_font_size = self.config.get('display.font_size_label')\n        \n        ax.set_title(title, fontsize=title_font_size, fontweight='bold')\n        ax.set_xlabel('経度', fontsize=label_font_size)\n        ax.set_ylabel('緯度', fontsize=label_font_size)\n        \n        # グリッドの設定\n        if self.config.get('display.show_grid'):\n            grid_alpha = self.config.get('display.grid_alpha')\n            ax.grid(True, alpha=grid_alpha)\n    \n    def print_network_info(self) -> None:\n        \"\"\"\n        ネットワーク情報の詳細表示\n        \"\"\"\n        print(\"\\n\" + \"=\"*50)\n        print(\"電力グリッドネットワーク分析\")\n        print(\"=\"*50)\n        \n        # 基本情報\n        print(f\"\\n📊 基本統計:\")\n        print(f\"  電力会社数: {self.network_stats['node_count']}社\")\n        print(f\"  接続数: {self.network_stats['edge_count']}本\")\n        print(f\"  ネットワーク密度: {self.network_stats['density']:.3f}\")\n        print(f\"  連結性: {'連結' if self.network_stats['is_connected'] else '非連結'}\")\n        \n        if self.network_stats['diameter']:\n            print(f\"  ネットワーク直径: {self.network_stats['diameter']}\")\n        if self.network_stats['average_shortest_path']:\n            print(f\"  平均最短経路長: {self.network_stats['average_shortest_path']:.2f}\")\n        \n        print(f\"  平均クラスタリング係数: {self.network_stats['average_clustering']:.3f}\")\n        \n        # 発電能力の詳細\n        print(f\"\\n⚡ 発電能力詳細:\")\n        sorted_capacity = sorted(self.power_capacity.items(), key=lambda x: x[1], reverse=True)\n        total_capacity = sum(self.power_capacity.values())\n        \n        for company, capacity in sorted_capacity:\n            percentage = (capacity / total_capacity) * 100\n            print(f\"  {company:>4}: {capacity:>6.1f}GW ({percentage:>5.1f}%)\")\n        \n        print(f\"  {'総計':>4}: {total_capacity:>6.1f}GW (100.0%)\")\n        \n        # 接続関係の詳細\n        print(f\"\\n🔗 接続関係詳細:\")\n        for company1, company2 in self.connections:\n            print(f\"  {company1} ⟷ {company2}\")\n        \n        # ネットワーク中心性の分析\n        print(f\"\\n📈 中心性分析:\")\n        \n        # 次数中心性\n        degree_centrality = nx.degree_centrality(self.graph)\n        print(f\"  次数中心性（接続数の重要度）:\")\n        for company, centrality in sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True):\n            degree = self.graph.degree[company]\n            print(f\"    {company:>4}: {centrality:.3f} ({degree}本の接続)\")\n        \n        # 媒介中心性（ネットワークが連結されている場合のみ）\n        if self.network_stats['is_connected']:\n            betweenness_centrality = nx.betweenness_centrality(self.graph)\n            print(f\"  媒介中心性（経路上の重要度）:\")\n            for company, centrality in sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True):\n                print(f\"    {company:>4}: {centrality:.3f}\")\n    \n    def print_impedance_matrix(self) -> None:\n        \"\"\"\n        インピーダンス行列の表示\n        \"\"\"\n        print(\"\\n\" + \"=\"*50)\n        print(\"インピーダンス行列 [Ω]\")\n        print(\"=\"*50)\n        \n        # ヘッダーの表示\n        print(f\"{'':>6}\", end=\"\")\n        for name in self.company_names:\n            print(f\"{name:>8}\", end=\"\")\n        print()\n        \n        # 各行の表示\n        for i, name in enumerate(self.company_names):\n            print(f\"{name:>6}\", end=\"\")\n            for j in range(len(self.company_names)):\n                value = self.impedance_matrix[i][j]\n                if value == 0 and i != j:\n                    print(f\"{'∞':>8}\", end=\"\")  # 無限大を表示\n                else:\n                    print(f\"{value:>8.3f}\", end=\"\")\n            print()\n        \n        print(\"\\n注: ∞は直接接続されていない電力会社間を示します\")\n    \n    def export_data(self, output_dir: str = \"output\") -> None:\n        \"\"\"\n        分析結果をファイルに出力\n        \n        Args:\n            output_dir (str): 出力ディレクトリ\n        \"\"\"\n        self.logger.info(f\"分析結果を出力中: {output_dir}\")\n        \n        # 出力ディレクトリの作成\n        Path(output_dir).mkdir(exist_ok=True)\n        \n        try:\n            # ネットワーク統計をJSON形式で出力\n            stats_file = Path(output_dir) / \"network_statistics.json\"\n            with open(stats_file, 'w', encoding='utf-8') as f:\n                json.dump({\n                    'network_stats': self.network_stats,\n                    'power_capacity': self.power_capacity,\n                    'connections': self.connections\n                }, f, ensure_ascii=False, indent=2)\n            \n            # インピーダンス行列をCSV形式で出力\n            impedance_file = Path(output_dir) / \"impedance_matrix.csv\"\n            df_impedance = pd.DataFrame(\n                self.impedance_matrix, \n                index=self.company_names, \n                columns=self.company_names\n            )\n            df_impedance.to_csv(impedance_file, encoding='utf-8')\n            \n            # NetworkXグラフをGraphML形式で出力\n            graph_file = Path(output_dir) / \"power_grid_network.graphml\"\n            nx.write_graphml(self.graph, graph_file)\n            \n            self.logger.info(\"分析結果の出力が完了しました\")\n            \n        except Exception as e:\n            self.logger.error(f\"分析結果の出力に失敗: {e}\")\n    \n    def run_analysis(self, \n                    save_image: bool = True, \n                    export_results: bool = True,\n                    show_plot: bool = True) -> bool:\n        \"\"\"\n        完全な分析と可視化の実行\n        \n        Args:\n            save_image (bool): 画像保存フラグ\n            export_results (bool): 結果出力フラグ\n            show_plot (bool): プロット表示フラグ\n        \n        Returns:\n            bool: 実行成功フラグ\n        \"\"\"\n        self.logger.info(\"電力グリッド分析を開始...\")\n        \n        try:\n            # 地図データの取得\n            japan_geojson = self.data_manager.get_japan_map()\n            if not japan_geojson:\n                self.logger.error(\"地図データの取得に失敗しました\")\n                return False\n            \n            # ネットワーク情報の表示\n            self.print_network_info()\n            \n            # インピーダンス行列の表示\n            self.print_impedance_matrix()\n            \n            # 地図の描画と保存\n            save_path = \"power_grid_map.png\" if save_image else None\n            self.plot_power_grid_map(japan_geojson, save_path, show_plot)\n            \n            # 結果の出力\n            if export_results:\n                self.export_data()\n            \n            self.logger.info(\"電力グリッド分析が完了しました\")\n            return True\n            \n        except Exception as e:\n            self.logger.error(f\"分析の実行中にエラーが発生: {e}\")\n            return False\n\n# ========================================\n# コマンドライン処理\n# ========================================\n\ndef create_parser() -> argparse.ArgumentParser:\n    \"\"\"\n    コマンドライン引数パーサーの作成\n    \n    Returns:\n        argparse.ArgumentParser: 設定されたパーサー\n    \"\"\"\n    parser = argparse.ArgumentParser(\n        description='日本電力グリッド可視化ツール',\n        formatter_class=argparse.RawDescriptionHelpFormatter,\n        epilog=\"\"\"\n例:\n  %(prog)s                              # デフォルト設定で実行\n  %(prog)s --capacity data/capacity.csv # 独自の発電能力データを使用\n  %(prog)s --config config.json        # 設定ファイルを使用\n  %(prog)s --no-show --save             # 画面表示なしで画像保存のみ\n  %(prog)s --log-level DEBUG           # デバッグログを有効化\n        \"\"\"\n    )\n    \n    # 入力ファイル関連\n    parser.add_argument(\n        '--capacity', '-c',\n        type=str,\n        default=None,\n        help='発電能力CSVファイルのパス (デフォルト: power_capacity.csv)'\n    )\n    \n    parser.add_argument(\n        '--connections', '-n',\n        type=str,\n        default=None,\n        help='接続関係CSVファイルのパス (デフォルト: connections.csv)'\n    )\n    \n    parser.add_argument(\n        '--config',\n        type=str,\n        default=None,\n        help='設定ファイル（JSON形式）のパス'\n    )\n    \n    # 出力関連\n    parser.add_argument(\n        '--save', '-s',\n        action='store_true',\n        help='地図画像を保存する'\n    )\n    \n    parser.add_argument(\n        '--output', '-o',\n        type=str,\n        default='output',\n        help='出力ディレクトリ (デフォルト: output)'\n    )\n    \n    parser.add_argument(\n        '--export',\n        action='store_true',\n        help='分析結果をファイルに出力する'\n    )\n    \n    # 表示関連\n    parser.add_argument(\n        '--no-show',\n        action='store_true',\n        help='地図の画面表示を無効にする'\n    )\n    \n    parser.add_argument(\n        '--log-level',\n        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],\n        default='INFO',\n        help='ログレベル (デフォルト: INFO)'\n    )\n    \n    # 分析オプション\n    parser.add_argument(\n        '--info-only',\n        action='store_true',\n        help='ネットワーク情報の表示のみ（地図描画なし）'\n    )\n    \n    return parser\n\ndef main() -> int:\n    \"\"\"\n    メイン実行関数\n    \n    Returns:\n        int: 終了ステータス（0: 成功, 1: 失敗）\n    \"\"\"\n    # コマンドライン引数の解析\n    parser = create_parser()\n    args = parser.parse_args()\n    \n    try:\n        # 設定の読み込み\n        config = PowerGridConfig(args.config) if args.config else PowerGridConfig()\n        \n        # PowerGridシステムの初期化\n        power_grid = PowerGridEnhanced(\n            config=config,\n            capacity_csv=args.capacity,\n            connections_csv=args.connections,\n            log_level=args.log_level\n        )\n        \n        # 情報表示のみの場合\n        if args.info_only:\n            power_grid.print_network_info()\n            power_grid.print_impedance_matrix()\n            if args.export:\n                power_grid.export_data(args.output)\n            return 0\n        \n        # 完全な分析の実行\n        success = power_grid.run_analysis(\n            save_image=args.save,\n            export_results=args.export,\n            show_plot=not args.no_show\n        )\n        \n        return 0 if success else 1\n        \n    except KeyboardInterrupt:\n        print(\"\\n処理が中断されました\")\n        return 1\n    except Exception as e:\n        print(f\"エラーが発生しました: {e}\")\n        return 1\n\n# ========================================\n# モジュールとして直接実行された場合\n# ========================================\n\nif __name__ == \"__main__\":\n    sys.exit(main())