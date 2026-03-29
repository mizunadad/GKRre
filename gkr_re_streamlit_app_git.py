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

# カスタムCSS
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
    """パスワード認証の管理"""
    # Secrets にパスワードが設定されていない場合は、APIキーの有無で判定（旧仕様）
    target_password = st.secrets.get("SITE_PASSWORD")
    
    if not target_password:
        # パスワード設定がない場合は APIキーがあればパス
        return bool(st.secrets.get("XAI_API_KEY") or st.session_state.get("override_key"))

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    return st.session_state.authenticated

def get_xai_api_key():
    if "override_key" in st.session_state and st.session_state.override_key:
        return st.session_state.override_key
    return st.secrets.get("XAI_API_KEY", "")

# Google Cloud (Vertex AI) 初期化
try:
    if "gcp_service_account" in st.secrets:
        gcp_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(gcp_info)
        vertexai.init(project=gcp_info["project_id"], credentials=credentials)
except Exception:
    pass

# --- 3. プロンプト定義 ---
VISUAL_CMD = "\n最後に、その光景を可視化するための英語プロンプトを必ず [Prompt: (英語プロンプト)] 形式で添えてください。"
SYSTEM_PROMPTS = {
    "Ep.1": "あなたは並行世界の観測モデルです。幻のトレンドを構築してください。" + VISUAL_CMD,
    "Ep.7": "あなたはElon Muskの思考を持つ予言者です。2026年の大成功を語ってください。" + VISUAL_CMD
}
SCENARIOS = {
    "Ep.1": "現実とは別の進化を遂げた『幻のトレンド』を観測します。",
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
        
        # Secrets にパスワードがある場合
        if st.secrets.get("SITE_PASSWORD"):
            pwd_input = st.text_input("Enter Site Password (合言葉):", type="password")
            if st.button("Unlock System"):
                if pwd_input == st.secrets["SITE_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("パスワードが正しくありません。")
        else:
            # Secrets に何もない場合、または APIキーでの解除を待つ場合
            st.warning("Secrets に API キーまたはパスワードが設定されていません。")
            st.session_state.override_key = st.text_input("xAI API Key を直接入力して開始:", type="password")
            if st.session_state.override_key:
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 認証成功後のメイン画面 ---

api_key = get_xai_api_key()

episode_map = {"Ep.1: 並行世界の同期失敗": "Ep.1", "Ep.7: 禁忌の自動具現化": "Ep.7"}
selected_display = st.sidebar.selectbox("Observation Mode", list(episode_map.keys()), key="observation_mode")
ep_id = episode_map[selected_display]

st.sidebar.divider()
st.sidebar.caption(f"Calibration Active: {ep_id}")

st.title(f"🛰️ {selected_display}")

st.markdown('<p class="theme-header">THEME / 観測目的</p>', unsafe_allow_html=True)
st.markdown(f'<div class="scenario-text">{SCENARIOS.get(ep_id)}</div>', unsafe_allow_html=True)

with st.expander("🛠️ SYSTEM COMMAND"):
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
