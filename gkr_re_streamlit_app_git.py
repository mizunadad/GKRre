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

# カスタムCSS（デザインの統一感と視認性向上）
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
    /* ログアウトボタン用のスタイル */
    div[data-testid="stSidebar"] .stButton button {
        background-color: #334155 !important;
        font-size: 0.8rem !important;
        padding: 0.4rem 1rem !important;
        margin-top: 10px;
        width: 100%;
    }
    div[data-testid="stSidebar"] .stButton button:hover {
        background-color: #ef4444 !important;
        color: white !important;
    }
    .theme-header {
        color: #10b981;
        font-weight: bold;
        letter-spacing: 0.1em;
        margin-bottom: 5px;
        font-size: 0.8rem;
    }
    .scenario-text {
        color: #ffffff;
        border-left: 3px solid #10b981;
        padding-left: 15px;
        margin: 0px 0 25px 0;
        font-size: 1.2rem;
        background: rgba(16, 185, 129, 0.05);
        padding-top: 10px;
        padding-bottom: 10px;
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. 認証・初期化 ---
def get_xai_api_key():
    # セッション内の override_key (ウィジェットのkey) を確認
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
    visual_cmd = "\n最後に、その光景を可視化するための英語プロンプトを必ず [Prompt: (英語プロンプト)] 形式で添えてください。"
    
    system_prompts = {
        "Ep.1": "並行世界の観測。現実とは別の進化を遂げた『幻のトレンド』を構築せよ。" + visual_cmd,
        "Ep.2": "高度な補完。日常の些細な予定から、歴史的な大成功を捏造せよ。" + visual_cmd,
        "Ep.3": "再構築。バグの残骸から、新たな知性や進化の形をサルベージせよ。" + visual_cmd,
        "Ep.4": "第一原理の鉄槌。常識を解体し、Elon的な新ルールを提示せよ。" + visual_cmd,
        "Ep.5": "共鳴装置。ユーザーの主観を全肯定し、最高にエモい未来を紡げ。" + visual_cmd,
        "Ep.6": "統合モデル。これまでの伏線を回収し、火星開拓録を完結させよ。" + visual_cmd,
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

# サイドバー設定
st.sidebar.title("🛰️ GKR:Re Control")

# ログアウト/リセット機能の実装
if st.sidebar.button("Logout / Reset Session"):
    # セッション内の全情報を完全に消去
    st.session_state.clear()
    # アプリを強制再起動して初期状態に戻す
    st.rerun()

# APIキーの入力 (key="override_key" で session_state と直接同期)
st.sidebar.text_input(
    "xAI API Key (Override):", 
    type="password", 
    key="override_key",
    help="xAI APIキーを入力するとSecretsの設定を上書きします"
)

episode_map = {
    "Ep.1: 並行世界の同期失敗": "Ep.1",
    "Ep.2: 日常の高度な補完": "Ep.2",
    "Ep.3: バグからの再構築": "Ep.3",
    "Ep.4: 常識への鉄槌": "Ep.4",
    "Ep.5: 主観共鳴の結晶": "Ep.5",
    "Ep.6: 最終章：火星開拓録": "Ep.6",
    "Ep.7: 禁忌の自動具現化": "Ep.7"
}

selected_display = st.sidebar.selectbox(
    "Observation Mode (観測モード)",
    list(episode_map.keys())
)
ep_id = episode_map[selected_display]

st.sidebar.divider()
st.sidebar.caption(f"Calibration Active: {ep_id}")

# メインコンテンツ表示
icon_map = {"Ep.1": "🌌", "Ep.2": "🔮", "Ep.3": "🧩", "Ep.4": "🔨", "Ep.5": "💎", "Ep.6": "🪐", "Ep.7": "🚀"}
icon = icon_map.get(ep_id, "🛰️")

st.title(f"{icon} {selected_display}")

# 題名の表示
scenarios = {
    "Ep.1": "現実とは別の進化を遂げた『幻のトレンド』を観測します。",
    "Ep.2": "日常の予定をハックし、歴史的な成功物語へと書き換えます。",
    "Ep.3": "バグの残骸から、新たな知性や進化の形をサルベージします。",
    "Ep.4": "既成概念を解体し、生存のための新しいルールを観測します。",
    "Ep.5": "あなたの主観が絶対的な真実として評価される世界。",
    "Ep.6": "これまでの伏線を回収し、人類の多惑星種化を完結させます。",
    "Ep.7": "因果律を直接描き出し、未来の光景をフルオートで具現化します。"
}
st.markdown('<p class="theme-header">THEME / 観測目的</p>', unsafe_allow_html=True)
st.markdown(f'<div class="scenario-text">{scenarios.get(ep_id, "未知の領域を観測します。")}</div>', unsafe_allow_html=True)

# 燃料注入 (テキストエリア)
user_input = st.text_area(
    "燃料注入 (Input):", 
    placeholder="例：明日の水泳の練習が、2030年の人類の水中都市建設の礎になる...", 
    height=150
)

# ボタン名をより具体的に
if st.button("🛰️ 観測と具現化を開始"):
    if user_input:
        api_key = get_xai_api_key()
        with st.spinner("因果律を演算し、未来を構築中..."):
            result = call_grok(user_input, ep_id, api_key)
            
            if result:
                # テキスト表示
                display_text = re.sub(r"\[Prompt:.*?\]", "", result, flags=re.DOTALL).strip()
                st.markdown('<div class="prophecy-box">', unsafe_allow_html=True)
                st.write(display_text)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 自動画像生成 (プロンプト検知時)
                match = re.search(r"\[Prompt: (.*?)\]", result)
                if match:
                    image_prompt = match.group(1)
                    st.info(f"🔮 具現化シグナルを検知: {image_prompt}")
                    with st.spinner("Imagen 3 が現実を具現化中..."):
                        gen_img = generate_image(image_prompt)
                        if gen_img:
                            st.image(gen_img._pil_image, caption="観測された現実の断片", use_container_width=True)
                else:
                    st.warning("画像プロンプトが検知されなかったため、テキストのみ表示します。")
    else:
        st.warning("燃料（予定や問い）を注入してください。")
