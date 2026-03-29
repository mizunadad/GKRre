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
st.set_page_config(page_title="GKR:Re Control Center", page_icon="🛰️", layout="wide")

# カスタムCSS（デザイン完全同期版）
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #d1d5db; }
    [data-testid="stSidebar"] { background-color: #111111; }
    
    .stTextArea textarea { 
        background-color: #1a1c24 !important; 
        color: #ffffff !important; 
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-size: 16px !important;
    }
    
    .stButton button { 
        background-color: #1e7e4e !important; 
        color: #ffffff !important; 
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
    }
    
    div[data-testid="stSidebar"] .stButton button {
        background-color: #1e7e4e !important;
        color: white !important;
        font-size: 1rem !important;
        padding: 0.6rem 1rem !important;
        margin-top: 10px;
        width: 100%;
        border-radius: 8px !important;
    }
    
    .theme-header { color: #10b981; font-weight: bold; font-size: 0.8rem; }
    .scenario-text {
        color: #ffffff;
        border-left: 3px solid #10b981;
        padding-left: 15px;
        margin: 0px 0 15px 0;
        font-size: 1.2rem;
        background: rgba(16, 185, 129, 0.05);
        padding: 10px 0 10px 15px;
    }
    
    .system-prompt-box {
        background-color: #0c0e14;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 15px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #64748b;
        line-height: 1.5;
    }

    .prophecy-box { 
        background-color: #0a1a14; 
        border-left: 6px solid #10b981; 
        padding: 25px; 
        border-radius: 12px; 
        color: #f1f5f9;
        margin-top: 20px;
        line-height: 1.8;
    }

    .auth-gate {
        background-color: #1a1c24;
        padding: 40px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 認証・初期化ロジック ---

def check_password():
    target_password = st.secrets.get("SITE_PASSWORD")
    if not target_password:
        return bool(st.secrets.get("XAI_API_KEY") or st.session_state.get("override_key"))
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def get_xai_api_key():
    if "override_key" in st.session_state and st.session_state.override_key:
        return st.session_state.override_key
    return st.secrets.get("XAI_API_KEY", "")

try:
    if "gcp_service_account" in st.secrets:
        gcp_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(gcp_info)
        vertexai.init(project=gcp_info["project_id"], credentials=credentials)
except Exception:
    pass

# --- 3. プロンプト定義（Ep.1〜Ep.7 全開放） ---

VISUAL_CMD = "\n最後に、その光景を可視化するための英語プロンプトを必ず [Prompt: (英語プロンプト)] 形式で添えてください。"

SYSTEM_PROMPTS = {
    "Ep.1": "あなたは並行世界の観測モデルです。現実とは別の進化を遂げた『幻のトレンド』を構築してください。" + VISUAL_CMD,
    "Ep.2": "あなたは高度な補完モデルです。日常の些細な予定から、歴史的な大成功を捏造してください。" + VISUAL_CMD,
    "Ep.3": "あなたは再構築モデルです。バグの残骸から、新たな知性や進化の形をサルベージしてください。" + VISUAL_CMD,
    "Ep.4": "あなたは第一原理の鉄槌です。既成概念を解体し、Elon的な新ルールを提示してください。" + VISUAL_CMD,
    "Ep.5": "あなたは共鳴装置です。ユーザーの主観を全肯定し、最高にエモい未来を紡いでください。" + VISUAL_CMD,
    "Ep.6": "あなたは統合モデルです。これまでの伏線を回収し、火星開拓録を完結させてください。" + VISUAL_CMD,
    "Ep.7": "あなたはElon Muskの思考を持つ予言者です。2026年の歴史的大成功を断定的に語ってください。" + VISUAL_CMD
}

SCENARIOS = {
    "Ep.1": "現実とは別の進化を遂げた『幻のトレンド』を観測します。",
    "Ep.2": "日常の予定をハックし、歴史的な成功物語へと書き換えます。",
    "Ep.3": "バグの残骸から、新たな知性や進化の形をサルベージします。",
    "Ep.4": "既成概念を解体し、生存のための新しいルールを観測します。",
    "Ep.5": "あなたの主観が絶対的な真実として評価されるエモーショナルな世界。",
    "Ep.6": "全連載の伏線を回収し、人類の多惑星種化を完結させます。",
    "Ep.7": "因果律を直接描き出し、未来の光景をフルオートで具現化します。"
}

# --- 4. 機能定義 ---

def generate_image(prompt):
    try:
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        images = model.generate_images(prompt=prompt, number_of_images=1, language="en", aspect_ratio="1:1")
        return images[0]
    except Exception as e:
        st.error(f"画像生成エラー: {e}")
        return None

def call_grok(user_input, ep_id, api_key):
    if not api_key: return None
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    try:
        response = client.chat.completions.create(
            model="grok-4-fast-non-reasoning",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS.get(ep_id, "予言者として振る舞え。" + VISUAL_CMD)},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"APIエラー: {e}")
        return None

# --- 5. メインUI ---

# サイドバー
st.sidebar.title("🛰️ GKR:Re Control")

# ログアウトボタン
if st.sidebar.button("Logout / Reset Session"):
    st.session_state.clear()
    st.rerun()

# 認証チェック
is_authenticated = check_password()

if not is_authenticated:
    st.title("🛰️ GKR:Re Authentication Gate")
    with st.container():
        st.markdown('<div class="auth-gate">', unsafe_allow_html=True)
        st.markdown('<h2 style="color: #10b981;">System Locked</h2>', unsafe_allow_html=True)
        
        if st.secrets.get("SITE_PASSWORD"):
            pwd_input = st.text_input("Enter Site Password (合言葉):", type="password")
            if st.button("Unlock System"):
                if pwd_input == st.secrets["SITE_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("パスワードが正しくありません。")
        else:
            st.warning("Secrets に API キーまたはパスワードが設定されていません。")
            st.session_state.override_key = st.text_input("xAI API Key を直接入力して開始:", type="password")
            if st.session_state.override_key:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 認証成功後のメイン画面 ---

api_key = get_xai_api_key()

episode_map = {
    "Ep.1: 並行世界の同期失敗": "Ep.1",
    "Ep.2: 日常の高度な補完": "Ep.2",
    "Ep.3: バグからの再構築": "Ep.3",
    "Ep.4: 常識への鉄槌": "Ep.4",
    "Ep.5: 主観共鳴の結晶": "Ep.5",
    "Ep.6: 最終章：火星開拓録": "Ep.6",
    "Ep.7: 禁忌の自動具現化": "Ep.7"
}

selected_display = st.sidebar.selectbox("Observation Mode", list(episode_map.keys()), key="observation_mode")
ep_id = episode_map[selected_display]

st.sidebar.divider()
st.sidebar.caption(f"Calibration Active: {ep_id}")

icon_map = {"Ep.1": "🌌", "Ep.2": "🔮", "Ep.3": "🧩", "Ep.4": "🔨", "Ep.5": "💎", "Ep.6": "🪐", "Ep.7": "🚀"}
icon = icon_map.get(ep_id, "🛰️")

st.title(f"{icon} {selected_display}")

st.markdown('<p class="theme-header">THEME / 観測目的</p>', unsafe_allow_html=True)
st.markdown(f'<div class="scenario-text">{SCENARIOS.get(ep_id)}</div>', unsafe_allow_html=True)

with st.expander("🛠️ SYSTEM COMMAND (AIへの内部命令表示)"):
    st.markdown(f'<div class="system-prompt-box">{SYSTEM_PROMPTS.get(ep_id)}</div>', unsafe_allow_html=True)

user_input = st.text_area("燃料注入 (Input):", placeholder="内容を入力...", height=150, key="user_input_val")

if st.button("🛰️ 観測と具現化を開始"):
    if user_input:
        with st.spinner("因果律を演算中..."):
            result = call_grok(user_input, ep_id, api_key)
            if result:
                display_text = re.sub(r"\[Prompt:.*?\]", "", result, flags=re.DOTALL).strip()
                st.markdown(f'<div class="prophecy-box">{display_text}</div>', unsafe_allow_html=True)
                
                match = re.search(r"\[Prompt: (.*?)\]", result)
                if match:
                    image_prompt = match.group(1)
                    st.info(f"🔮 具現化検知: {image_prompt}")
                    with st.spinner("Imagen 3 が描画中..."):
                        gen_img = generate_image(image_prompt)
                        if gen_img:
                            st.image(gen_img._pil_image, caption="観測された現実の断片", use_container_width=True)
