#!/bin/bash

echo "日本地図生成プロジェクトの仮想環境をセットアップします..."

# 仮想環境を作成
python3 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate

# pip をアップグレード
pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements.txt

echo "セットアップ完了！"
echo "仮想環境をアクティベートするには: source venv/bin/activate"
echo "プログラムを実行するには: python first.py"