🛰️ GKRre (Grok Knowledge Refinery: Renaissance)

2026 Parallel Future Observation Device [Episode 7: Auto-Materialization]

🌌 Overview

GKRre は、xAI の最新モデル Grok-4 の「捏造力（ハルシネーション）」と、Google Cloud Vertex AI (Imagen 3) の「具現化力」を直結させた、並行世界観測デバイスです。

日常の些細な予定や問いを「燃料」として注入することで、2026年の歴史的な成功物語を紡ぎ出し、その光景を即座に可視化します。

🛰️ Key Features

Grok-4 Integration: Elon Musk の第一原理思考をベースとした強気な予言生成。

Auto-Materialization: Imagen 3.0 による全自動画像生成（Ep.7）。コピペ不要で予言の直後に画像が表示されます。

Multi-Episode Mode: Ep.1〜Ep.7 までの異なる観測プロトコルを搭載。

Security Gate: SITE_PASSWORD（合言葉）によるセッション保護と、安全なログアウト機能。

🛠️ Setup Guide

1. 必要要件

xAI API Key

Google Cloud Project (Vertex AI API 有効化済み)

サービスアカウントの JSON キー

2. Streamlit Cloud へのデプロイ

このリポジトリをフォークまたはプッシュ。

Streamlit Cloud で gkr_re_streamlit_app_git.py をメインファイルとしてデプロイ。

Advanced settings > Secrets に以下の情報を入力してください。

XAI_API_KEY = "あなたの xAI API キー"
SITE_PASSWORD = "認証用の合言葉（任意）"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n..."
client_email = "..."
# (以下、ダウンロードした JSON の中身をすべて貼り付け)


🚀 How to Observe

アプリを起動し、設定した SITE_PASSWORD で認証。

サイドバーから Observation Mode（エピソード）を選択。

燃料注入 (Input) スロットに、あなたの予定や問いを入力。

観測と具現化を開始 ボタンを押下し、未来が構築されるのを待つ。

⚠️ Disclaimer

このデバイスで観測される未来は、Grok-4 による高度な捏造データです。現実との同期を目的としたものではありません。10ドルの聖域（クレジット枠）を大切に運用してください。
