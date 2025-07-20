#!/bin/bash

# 日本地図表示プログラム実行スクリプト
# ダブルクリックで実行可能

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

echo "=================================="
echo "    日本地図表示プログラム"
echo "=================================="
echo ""

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "⚠️  仮想環境が見つかりません。セットアップを実行します..."
    echo ""
    
    # Python3の確認
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3がインストールされていません。"
        echo "   https://www.python.org/ からPython3をインストールしてください。"
        echo ""
        read -p "Enterキーを押して終了してください..."
        exit 1
    fi
    
    # 仮想環境の作成
    echo "🔧 仮想環境を作成中..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ 仮想環境の作成に失敗しました。"
        echo ""
        read -p "Enterキーを押して終了してください..."
        exit 1
    fi
fi

# 仮想環境のアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係のインストール
echo "📦 必要なライブラリをインストール中..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "❌ ライブラリのインストールに失敗しました。"
    echo ""
    read -p "Enterキーを押して終了してください..."
    exit 1
fi

echo ""
echo "✅ セットアップ完了！"
echo ""

# プログラムの選択
echo "実行するプログラムを選択してください："
echo ""
echo "1) 基本的な日本地図"
echo "2) 電力グリッド地図"
echo ""

while true; do
    read -p "番号を入力してください (1 または 2): " choice
    case $choice in
        1)
            echo ""
            echo "🗾 基本的な日本地図を表示します..."
            python map.py
            break
            ;;
        2)
            echo ""
            echo "⚡ 電力グリッド地図を表示します..."
            python power_grid.py
            break
            ;;
        *)
            echo "❌ 1 または 2 を入力してください。"
            ;;
    esac
done

echo ""
echo "🎉 プログラムが完了しました！"
echo ""
read -p "Enterキーを押してウィンドウを閉じてください..."