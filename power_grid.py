import requests
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import pandas as pd
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

def get_japan_map():
    """日本の地図データを取得"""
    url = "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        japan_data = response.json()
        return japan_data
    except requests.RequestException as e:
        print(f"データ取得エラー: {e}")
        return None

class PowerGrid:
    def __init__(self, capacity_csv='power_capacity.csv', connections_csv='connections.csv'):
        # 9電力会社の名前と位置座標（緯度、経度）
        self.power_companies = {
            '北海道': (43.2, 141.5),
            '東北': (38.5, 140.5),
            '東京': (35.7, 139.7),
            '中部': (35.2, 137.0),
            '北陸': (36.8, 137.2),
            '関西': (34.7, 135.5),
            '中国': (34.4, 132.5),
            '四国': (33.8, 133.5),
            '九州': (33.0, 130.5)
        }
        
        # CSVファイルから発電能力を読み込み
        self.load_power_capacity(capacity_csv)
        
        # CSVファイルから接続関係を読み込み
        self.load_connections(connections_csv)
        
        # グラフの作成
        self.graph = nx.Graph()
        self.graph.add_nodes_from(self.power_companies.keys())
        self.graph.add_edges_from(self.connections)
        
        # インピーダンス行列の作成
        self.create_impedance_matrix()
    
    def load_power_capacity(self, csv_file):
        """CSVファイルから発電能力を読み込み"""
        try:
            df = pd.read_csv(csv_file)
            self.power_capacity = {}
            for _, row in df.iterrows():
                company = row['電力会社']
                capacity = row['発電能力_GW']
                self.power_capacity[company] = capacity
            print(f"発電能力データを読み込みました: {csv_file}")
        except FileNotFoundError:
            print(f"CSVファイルが見つかりません: {csv_file}")
            # デフォルト値を設定
            self.power_capacity = {
                '北海道': 8.5, '東北': 17.2, '東京': 52.8, '中部': 32.1,
                '北陸': 7.3, '関西': 33.5, '中国': 12.8, '四国': 6.7, '九州': 18.9
            }
        except Exception as e:
            print(f"CSVファイル読み込みエラー: {e}")
            self.power_capacity = {
                '北海道': 8.5, '東北': 17.2, '東京': 52.8, '中部': 32.1,
                '北陸': 7.3, '関西': 33.5, '中国': 12.8, '四国': 6.7, '九州': 18.9
            }
    
    def load_connections(self, csv_file):
        """CSVファイルから接続関係を読み込み"""
        try:
            df = pd.read_csv(csv_file)
            self.connections = []
            for _, row in df.iterrows():
                company1 = row['電力会社1']
                company2 = row['電力会社2']
                self.connections.append((company1, company2))
            print(f"接続関係データを読み込みました: {csv_file}")
        except FileNotFoundError:
            print(f"CSVファイルが見つかりません: {csv_file}")
            # デフォルト値を設定
            self.connections = [
                ('北海道', '東北'), ('東北', '東京'), ('東京', '中部'),
                ('中部', '北陸'), ('中部', '関西'), ('北陸', '関西'),
                ('関西', '中国'), ('関西', '四国'), ('中国', '九州')
            ]
        except Exception as e:
            print(f"CSVファイル読み込みエラー: {e}")
            self.connections = [
                ('北海道', '東北'), ('東北', '東京'), ('東京', '中部'),
                ('中部', '北陸'), ('中部', '関西'), ('北陸', '関西'),
                ('関西', '中国'), ('関西', '四国'), ('中国', '九州')
            ]
    
    def get_circle_size(self, company):
        """発電能力に応じて丸のサイズを計算"""
        capacity = self.power_capacity.get(company, 10)
        # ベースサイズを800として、発電能力に比例してサイズを決定
        base_size = 800
        size_factor = capacity / 10  # 10GWを基準とする
        return base_size * size_factor
    
    def create_impedance_matrix(self):
        """インピーダンス行列を作成"""
        companies = list(self.power_companies.keys())
        n = len(companies)
        self.impedance_matrix = np.zeros((n, n))
        
        # 適当なインピーダンス値を設定
        np.random.seed(42)  # 再現性のため
        
        for i, company1 in enumerate(companies):
            for j, company2 in enumerate(companies):
                if i == j:
                    # 自己インピーダンス
                    self.impedance_matrix[i][j] = np.random.uniform(0.1, 0.3)
                elif self.graph.has_edge(company1, company2):
                    # 接続されている場合の相互インピーダンス
                    impedance = np.random.uniform(0.05, 0.15)
                    self.impedance_matrix[i][j] = impedance
                    self.impedance_matrix[j][i] = impedance
                else:
                    # 直接接続されていない場合
                    self.impedance_matrix[i][j] = 0
        
        self.company_names = companies
    
    def plot_power_grid_map(self, geojson_data, show_gw=True, save_figure=False, save_path=None, save_format='png'):
        """日本地図に電力グリッドを描画"""
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        # 日本地図の描画
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
        
        p = PatchCollection(patches, facecolor='lightgray', edgecolor='none', linewidth=0, alpha=0.7)
        ax.add_collection(p)
        
        # 接続線の描画（丸の下に来るように先に描画）
        for company1, company2 in self.connections:
            lat1, lon1 = self.power_companies[company1]
            lat2, lon2 = self.power_companies[company2]
            ax.plot([lon1, lon2], [lat1, lat2], color='#404040', linewidth=2, alpha=0.9, zorder=1)
        
        # 電力会社の位置に丸を描画（発電能力に応じてサイズを変更）
        for company, (lat, lon) in self.power_companies.items():
            circle_size = self.get_circle_size(company)
            capacity = self.power_capacity.get(company, 0)
            
            ax.scatter(lon, lat, s=circle_size, c='white', marker='o', alpha=1.0, 
                      edgecolors='black', linewidth=2, zorder=2)
            
            # GW表示の選択
            if show_gw:
                label_text = f'{company}\n({capacity:.1f}GW)'
            else:
                label_text = company
            
            ax.annotate(label_text, (lon, lat), xytext=(5, 5), 
                       textcoords='offset points', fontsize=9, fontweight='bold', ha='left', zorder=3)
        
        ax.set_xlim(129, 146)
        ax.set_ylim(30, 46)
        ax.set_aspect('equal')
        ax.set_title('日本電力グリッド接続図', fontsize=16, fontweight='bold')
        ax.set_xlabel('経度')
        ax.set_ylabel('緯度')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 図の保存
        if save_figure and save_path:
            try:
                fig.savefig(save_path, format=save_format, dpi=300, bbox_inches='tight')
                print(f"図を保存しました: {save_path}")
            except Exception as e:
                print(f"図の保存に失敗しました: {e}")
        
        plt.show()
    
    def print_network_info(self):
        """ネットワーク情報を表示"""
        print("=== 電力グリッド情報 ===")
        print(f"電力会社数: {len(self.power_companies)}")
        print(f"接続数: {len(self.connections)}")
        print("\n発電能力:")
        for company, capacity in self.power_capacity.items():
            print(f"  {company}: {capacity:.1f}GW")
        
        print("\n接続関係:")
        for company1, company2 in self.connections:
            print(f"  {company1} - {company2}")
        
        print(f"\nグラフの次数分布:")
        for company in self.power_companies.keys():
            degree = self.graph.degree[company]
            print(f"  {company}: {degree}本の接続")
    
    def print_impedance_matrix(self):
        """インピーダンス行列を表示"""
        print("\n=== インピーダンス行列 ===")
        print("     ", end="")
        for name in self.company_names:
            print(f"{name:>8}", end="")
        print()
        
        for i, name in enumerate(self.company_names):
            print(f"{name:>5}", end="")
            for j in range(len(self.company_names)):
                print(f"{self.impedance_matrix[i][j]:8.3f}", end="")
            print()

def get_user_preferences():
    """ユーザーの設定を取得"""
    print("\n=== 表示設定 ===")
    
    # GW表示の確認
    while True:
        gw_choice = input("グラフにGW（発電能力）を表示しますか？ (y/n): ").lower().strip()
        if gw_choice in ['y', 'yes', 'はい', '']:
            show_gw = True
            break
        elif gw_choice in ['n', 'no', 'いいえ']:
            show_gw = False
            break
        else:
            print("y または n を入力してください。")
    
    # 図の保存確認
    while True:
        save_choice = input("図を保存しますか？ (y/n): ").lower().strip()
        if save_choice in ['y', 'yes', 'はい']:
            save_figure = True
            break
        elif save_choice in ['n', 'no', 'いいえ', '']:
            save_figure = False
            save_path = None
            save_format = 'png'
            break
        else:
            print("y または n を入力してください。")
    
    if save_figure:
        # 保存フォルダの指定
        print("\n保存フォルダを指定してください：")
        print("1) カレントディレクトリ (デフォルト)")
        print("2) デスクトップ")
        print("3) カスタムパス")
        
        while True:
            folder_choice = input("選択してください (1/2/3): ").strip()
            if folder_choice == '1' or folder_choice == '':
                save_folder = "."
                break
            elif folder_choice == '2':
                import os
                save_folder = os.path.expanduser("~/Desktop")
                break
            elif folder_choice == '3':
                save_folder = input("保存フォルダのパスを入力してください: ").strip()
                if not save_folder:
                    save_folder = "."
                break
            else:
                print("1, 2, または 3 を入力してください。")
        
        # 保存形式の選択
        print("\n保存形式を選択してください：")
        print("1) PNG (デフォルト)")
        print("2) PDF")
        print("3) SVG")
        print("4) JPEG")
        
        while True:
            format_choice = input("選択してください (1/2/3/4): ").strip()
            if format_choice == '1' or format_choice == '':
                save_format = 'png'
                break
            elif format_choice == '2':
                save_format = 'pdf'
                break
            elif format_choice == '3':
                save_format = 'svg'
                break
            elif format_choice == '4':
                save_format = 'jpeg'
                break
            else:
                print("1, 2, 3, または 4 を入力してください。")
        
        # ファイル名の生成
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"power_grid_map_{timestamp}.{save_format}"
        save_path = f"{save_folder}/{filename}"
    else:
        save_path = None
        save_format = 'png'
    
    return show_gw, save_figure, save_path, save_format

if __name__ == "__main__":
    print("日本電力グリッド地図を生成中...")
    
    # 日本地図データを取得
    japan_geojson = get_japan_map()
    
    if japan_geojson:
        # 電力グリッドのインスタンスを作成
        power_grid = PowerGrid()
        
        # ユーザー設定を取得
        show_gw, save_figure, save_path, save_format = get_user_preferences()
        
        # ネットワーク情報を表示
        power_grid.print_network_info()
        
        # インピーダンス行列を表示
        power_grid.print_impedance_matrix()
        
        # 地図を描画
        print("\n地図を描画中...")
        power_grid.plot_power_grid_map(japan_geojson, show_gw, save_figure, save_path, save_format)
    else:
        print("地図データの取得に失敗しました。")