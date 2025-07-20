# 日本電力グリッド地図生成ツール

日本の電力グリッドを可視化するPythonツールです。各電力会社の位置、発電能力、接続関係を地図上に表示します。

## 機能

- 日本地図の取得と表示
- 9電力会社の位置表示（発電能力に応じたサイズの丸）
- 電力会社間の接続関係の表示
- インピーダンス行列の生成
- CSVファイルによる設定の変更

## ファイル構成

```
map_gen/
├── map.py                  # 基本的な日本地図表示
├── power_grid.py           # 電力グリッド地図（シンプル版）
├── power_grid_enhanced.py  # 電力グリッド地図（高機能版）
├── power_capacity.csv      # 発電能力設定
├── connections.csv         # 接続関係設定
├── config_sample.json      # 設定ファイルサンプル
├── requirements.txt        # 依存ライブラリ
├── setup_venv.sh          # 仮想環境セットアップスクリプト
└── README.md              # このファイル
```

## セットアップ

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd map_gen
```

### 2. 仮想環境のセットアップ
```bash
# 自動セットアップスクリプトを使用
./setup_venv.sh

# または手動セットアップ
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 依存ライブラリ
- requests: Web API通信
- matplotlib: グラフ描画
- numpy: 数値計算
- networkx: グラフ理論
- pandas: CSV読み込み

## 使い方

### 基本的な実行

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 基本的な日本地図を表示
python map.py

# 電力グリッド地図を表示（シンプル版）
python power_grid.py

# 電力グリッド地図を表示（高機能版）
python power_grid_enhanced.py

# 高機能版のオプション例
python power_grid_enhanced.py --save --export          # 画像保存と結果出力
python power_grid_enhanced.py --config config_sample.json  # カスタム設定
python power_grid_enhanced.py --info-only              # 情報表示のみ
python power_grid_enhanced.py --no-show --save         # 非表示で保存のみ
```

### 設定ファイルの編集

#### 発電能力の変更 (power_capacity.csv)
```csv
電力会社,発電能力_GW
北海道,8.5
東北,17.2
東京,52.8
中部,32.1
北陸,7.3
関西,33.5
中国,12.8
四国,6.7
九州,18.9
```

#### 接続関係の変更 (connections.csv)
```csv
電力会社1,電力会社2
北海道,東北
東北,東京
東京,中部
中部,北陸
中部,関西
北陸,関西
関西,中国
関西,四国
中国,九州
```

## 出力内容

### コンソール出力
- 発電能力一覧
- 接続関係一覧
- グラフの次数分布
- インピーダンス行列

### 地図表示
- 日本地図（グレー）
- 電力会社位置（赤い丸、発電能力に応じたサイズ）
- 電力会社名と発電能力の表示
- 接続線（青線）

## カスタマイズ

### 位置座標の変更
`power_grid.py`の`power_companies`辞書を編集して各電力会社の位置を調整できます。

### 表示スタイルの変更
- 丸のサイズ: `get_circle_size()`メソッド
- 色やスタイル: `plot_power_grid_map()`メソッド

## トラブルシューティング

### 日本語フォントの警告
```
UserWarning: Glyph xxx missing from font(s) DejaVu Sans.
```
この警告は表示には影響しません。日本語フォントを追加することで解決できますが、必須ではありません。

### CSVファイルが見つからない
デフォルト値が使用されます。必要に応じてCSVファイルを作成してください。

### 地図データの取得エラー
インターネット接続を確認してください。GitHub上の地図データにアクセスします。

## 技術仕様

- Python 3.7+対応
- NetworkXによるグラフ理論の実装
- 発電能力に比例した丸のサイズ計算
- CSVによる動的設定変更
- インピーダンス行列の自動生成

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。