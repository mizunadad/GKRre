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
st.set_page_config(page_title="GKR:Re Control", page_icon="🛰️", layout="wide")

# カスタムCSS（デザイン完全同期）
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #d1d5db; }
    [data-testid="stSidebar"] { background-color: #111111; }
    .stTextArea textarea { 
        background-color: #1a1c24 !important; 
        color: #ffffff !important; 
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    .stButton button { 
        background-color: #1e7e4e !important; 
        color: #ffffff !important; 
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 2rem !important;
    }
    .scenario-text {
        color: #94a3b8;
        border-left: 2px solid #334155;
        padding-left: 15px;
        margin: 10px 0 20px 0;
        font-size: 1.1rem;
    }
    .prophecy-box { 
        background-color: #0a1a14; 
        border-left: 6px solid #10b981; 
        padding: 20px; 
        border-radius: 12px; 
        color: #f1f5f9;
        margin-top: 20px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 認証・初期化 ---
def get_xai_api_key():
    if "override_key" in st.session_state and st.session_state.override_key:
        return st.session_state.override_key
    return st.secrets.get("XAI_API_KEY", "")

try:
    if "gcp_service_account" in st.secrets:
        gcp_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(gcp_info)
        vertexai.init(project=gcp_info["project_id"], credentials=credentials)
except Exception as e:
    pass

# --- 3. 機能定義 ---

def generate_image(prompt):
    """Imagen 3 による自動具現化"""
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

def call_grok(user_input, episode_style, api_key):
    """Grok-4 によるテキスト生成"""
    if not api_key:
        st.error("xAI API Key が設定されていません。")
        return None
        
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    
    # 共通の視覚化指示
    visual_cmd = "\n最後に必ず [Prompt: (その光景を可視化する映画的な英語プロンプト)] を添えてください。"
    
    system_prompts = {
        "Ep.1": "並行世界の観測モデル。現実とは別の進化を遂げた『幻のトレンド』を構築せよ。" + visual_cmd,
        "Ep.2": "高度な補完モデル。ユーザーの些細な予定から歴史的な大成功を捏造せよ。" + visual_cmd,
        "Ep.3": "再構築モデル。過去のバグやエラーコードから新生命体や新概念を定義せよ。" + visual_cmd,
        "Ep.4": "破壊的モデル。常識を第一原理で解体し、Elon的な新ルールを提示せよ。" + visual_cmd,
        "Ep.5": "共鳴装置。ユーザーのバイアスを全肯定し、最高にエモい未来を紡げ。" + visual_cmd,
        "Ep.6": "統合モデル。これまでの観測を伏線として回収し、火星移住の物語を完結させよ。" + visual_cmd,
        "Ep.7": "Elon Muskの思考を持つ予言者。2026年の大成功を語れ。" + visual_cmd
    }
    
    selected_system = system_prompts.get(episode_style, "標準的な予言者として振る舞ってください。" + visual_cmd)
    
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

st.sidebar.title("🛰️ GKR:Re Control")
st.session_state.override_key = st.sidebar.text_input("xAI API Key (Override):", type="password")

episode_display = st.sidebar.selectbox(
    "Observation Mode",
    [
        "Ep.1: 並行世界のX", 
        "Ep.2: 高度な補完", 
        "Ep.3: 1/12の再構築", 
        "Ep.4: 第一原理の鉄槌", 
        "Ep.5: 共鳴の結晶", 
        "Ep.6: 火星開拓録", 
        "Ep.7: 自動具現化"
    ]
)

st.sidebar.divider()
st.sidebar.caption(f"Calibration: {episode_display}")

# メインコンテンツ
ep_id = episode_display.split(":")[0]
icon_map = {
    "Ep.1": "🌌", "Ep.2": "🔮", "Ep.3": "🧩", 
    "Ep.4": "🔨", "Ep.5": "💎", "Ep.6": "🪐", "Ep.7": "🚀"
}
icon = icon_map.get(ep_id, "🛰️")

st.title(f"{icon} {episode_display}")

# シナリオ表示
scenarios = {
    "Ep.1": "現実とは別の進化を遂げた『幻のトレンド』を観測します。",
    "Ep.2": "日常の予定をハックし、歴史的な成功物語へと書き換えます。",
    "Ep.3": "バグの残骸から、新たな知性や進化の形をサルベージします。",
    "Ep.4": "既成概念を解体し、生存のための新しいルールを観測します。",
    "Ep.5": "あなたの主観が絶対的な真実として評価されるエモい未来。",
    "Ep.6": "全連載の伏線を回収し、人類の多惑星種化を完結させます。",
    "Ep.7": "10ドルの聖域が、因果律を直接描き出し、現実を具現化します。"
}
st.markdown(f'<div class="scenario-text">| 観測シナリオ: {scenarios.get(ep_id, "未知の領域を観測します。")}</div>', unsafe_allow_html=True)

user_input = st.text_area(
    "燃料注入:", 
    placeholder="内容を入力してください...", 
    height=150
)

if st.button("観測シーケンス開始"):
    if user_input:
        api_key = get_xai_api_key()
        with st.spinner("因果律を演算中..."):
            result = call_grok(user_input, ep_id, api_key)
            
            if result:
                # テキスト表示
                display_text = re.sub(r"\[Prompt:.*?\]", "", result, flags=re.DOTALL).strip()
                st.markdown(f'<div class="prophecy-box">{display_text}</div>', unsafe_allow_html=True)
                
                # 全エピソードでプロンプト検知時に画像生成を実行
                match = re.search(r"\[Prompt: (.*?)\]", result)
                if match:
                    image_prompt = match.group(1)
                    st.info(f"🔮 具現化検知: {image_prompt}")
                    with st.spinner("Imagen 3 が描画中..."):
                        gen_img = generate_image(image_prompt)
                        if gen_img:
                            st.image(gen_img._pil_image, caption="観測された現実の断片", use_container_width=True)
    else:
        st.warning("燃料を注入してください。")
