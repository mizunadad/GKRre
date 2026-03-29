import streamlit as st
from openai import OpenAI
import os
from google.oauth2 import service_account
from google.cloud import aiplatform
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import json
import re

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="GKRre: Multiverse Observation", page_icon="🛰️", layout="centered")

# カスタムCSS（共通デザイン）
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
        height: 3rem;
        font-weight: bold;
    }
    .prophecy-box { 
        background-color: #0a1a14; 
        border-left: 6px solid #10b981; 
        padding: 20px; 
        border-radius: 12px; 
        color: #f1f5f9;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 認証・初期化 ---
try:
    # xAI (Grok) 認証
    xai_api_key = st.secrets["XAI_API_KEY"]
    client = OpenAI(api_key=xai_api_key, base_url="https://api.x.ai/v1")

    # GCP (Vertex AI) 認証 - Ep.7 用
    if "gcp_service_account" in st.secrets:
        gcp_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(gcp_info)
        vertexai.init(project=gcp_info["project_id"], credentials=credentials)
except Exception as e:
    st.error(f"認証情報の読み込みに失敗しました。Secretsを確認してください。: {e}")

# --- 3. 機能定義 ---

def generate_image(prompt):
    """Imagen 3 を用いた画像生成 (Ep.7用)"""
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

def call_grok(user_input, episode_style):
    """Grok-4 によるテキスト生成"""
    system_prompts = {
        "Ep.1": "初期の予言モデル。簡潔に未来を述べよ。",
        "Ep.7": """
        あなたはElon Muskの思考を持つ予言者です。
        2026年の大成功を日本語で断定的に語ってください。
        最後に必ず [Prompt: (英語の画像プロンプト)] を添えること。
        """
    }
    
    selected_system = system_prompts.get(episode_style, "標準的な予言者として振る舞ってください。")
    
    try:
        response = client.chat.completions.create(
            model="grok-4-fast-non-reasoning",
            messages=[
                {"role": "system", "content": selected_system},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None

# --- 4. メインUI ---

# サイドバーでエピソード選択
st.sidebar.title("🛰️ System Log")
episode = st.sidebar.selectbox(
    "観測フェーズを選択:",
    ["Ep.1", "Ep.2", "Ep.3", "Ep.4", "Ep.5", "Ep.6", "Ep.7"]
)

st.title(f"GKRre: {episode}")

if episode == "Ep.7":
    st.write("### 禁忌の自動具現化（$10 聖域モデル）")
    st.info("このフェーズでは、予言の直後に Imagen 3 が現実を自動構築します。")
else:
    st.write(f"### 観測フェーズ: {episode}")

# 入力欄
user_input = st.text_area("燃料（予定や問い）を入力:", placeholder="例：火星移住計画の進捗について")

if st.button("観測開始"):
    if user_input:
        with st.spinner("次元を解析中..."):
            result = call_grok(user_input, episode)
            
            if result:
                # テキスト表示
                display_text = re.sub(r"\[Prompt:.*?\]", "", result, flags=re.DOTALL).strip()
                st.markdown(f'<div class="prophecy-box">{display_text}</div>', unsafe_allow_html=True)
                
                # Ep.7 の場合のみ、自動画像生成を実行
                if episode == "Ep.7":
                    match = re.search(r"\[Prompt: (.*?)\]", result)
                    if match:
                        image_prompt = match.group(1)
                        st.info(f"🔮 具現化検知: {image_prompt}")
                        with st.spinner("Imagen 3 が描画中..."):
                            gen_img = generate_image(image_prompt)
                            if gen_img:
                                st.image(gen_img._pil_image, caption="観測された未来の断片")
    else:
        st.warning("入力がありません。")

st.divider()
st.caption(f"GKRre Version 2.0 | {episode} Active")
