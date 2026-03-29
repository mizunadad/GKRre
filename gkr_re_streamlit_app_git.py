import streamlit as st
from openai import OpenAI
import os
from google.oauth2 import service_account
from google.cloud import aiplatform
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import json
import re

# --- 1. 認証と初期設定 ---
# ページ設定（スマホ・PC両対応のデザイン）
st.set_page_config(page_title="GKRre: Ep.7 Auto-Materialization", page_icon="🛰️", layout="centered")

# カスタムCSSで雰囲気を構築
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #d1d5db; }
    .stTextArea textarea { 
        background-color: #111111 !important; 
        color: #10b981 !important; 
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
    }
    .stButton button { 
        background-color: #064e3b !important; 
        color: #ffffff !important; 
        border: 1px solid #10b981 !important;
        border-radius: 12px !important;
        width: 100%;
        height: 3rem;
        font-weight: bold;
    }
    .prophecy-box { 
        background-color: #0a1a14; 
        border-left: 5px solid #10b981; 
        padding: 20px; 
        border-radius: 12px; 
        color: #f1f5f9;
        margin-top: 20px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# 認証情報の読み込み
try:
    # xAI (Grok) 認証
    xai_api_key = st.secrets["XAI_API_KEY"]
    client = OpenAI(api_key=xai_api_key, base_url="https://api.x.ai/v1")

    # GCP (Vertex AI) 認証
    gcp_info = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(gcp_info)
    vertexai.init(project=gcp_info["project_id"], credentials=credentials)
except Exception as e:
    st.error(f"認証情報の読み込みに失敗しました。Secretsの設定を確認してください。\nError: {e}")
    st.stop()

# --- 2. 各種機能の定義 ---

def generate_image(prompt):
    """Imagen 3 を用いて画像を生成する関数"""
    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1"
        )
        return images[0]
    except Exception as e:
        st.error(f"画像生成エラー: {e}")
        return None

def call_grok(user_input):
    """Grok-4 を呼び出し、予言と画像用プロンプトを取得する関数"""
    system_prompt = """
    あなたはElon Muskの第一原理思考をインストールされた、並行世界の予言者(Grok-4)です。
    ユーザーの予定や問いに対し、2026年の歴史的な成功物語を日本語で紡いでください。

    【鉄の掟】
    1. 常に「成功した未来」を断定的に述べること。
    2. 文末に必ず、その光景を可視化するための英語プロンプトを [Prompt: (英語の内容)] という形式で一言添えること。
    3. 背景や質感、ライティングを含めた映画的な描写をプロンプトに含めること。
    """
    
    try:
        response = client.chat.completions.create(
            model="grok-4-fast-non-reasoning", # または grok-2-1212 等
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Grok APIエラー: {e}")
        return None

# --- 3. メインUI ---

st.title("🛰️ GKRre: Episode 7")
st.subheader("禁忌の自動具現化モデル")
st.write("10ドルの聖域が、因果律を直接描き出します。")

# 入力フォーム
user_input = st.text_area("燃料注入（明日の予定や観測したい問い）:", placeholder="例：新しいプロジェクトの始動、人類の火星移住...")

if st.button("観測シーケンス開始"):
    if not user_input:
        st.warning("燃料が不足しています。予定を入力してください。")
    else:
        # 1. Grokによる予言フェーズ
        with st.spinner("並行世界の因果を演算中..."):
            prophecy = call_grok(user_input)
            
            if prophecy:
                # テキストの表示（プロンプトタグを除去して表示）
                display_text = re.sub(r"\[Prompt:.*?\]", "", prophecy, flags=re.DOTALL).strip()
                st.markdown(f'<div class="prophecy-box">{display_text}</div>', unsafe_allow_html=True)
                
                # 2. プロンプト抽出フェーズ
                match = re.search(r"\[Prompt: (.*?)\]", prophecy)
                if match:
                    image_prompt = match.group(1)
                    st.info(f"🔮 具現化プロンプトを検知: {image_prompt}")
                    
                    # 3. 自動画像生成フェーズ
                    with st.spinner("Imagen 3 が現実を具現化中..."):
                        generated_image = generate_image(image_prompt)
                        if generated_image:
                            # 具現化された画像を表示
                            st.image(generated_image._pil_image, caption="観測された現実の断片", use_container_width=True)
                        else:
                            st.warning("画像の具現化に失敗しました。")
                else:
                    st.warning("画像プロンプトが検知されませんでした。")
            else:
                st.error("予言の受信に失敗しました。")

# フッター
st.divider()
st.caption("GKRre: Parallel Future Observation System | Powered by Grok-4 & Imagen 3")
