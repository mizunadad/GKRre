import streamlit as st
import requests
import json
import os
import re
from dotenv import load_dotenv

# --- 1. 初期設定 ---
load_dotenv()

# セキュリティ：アクセス制限用のパスワード
# GitHub上での露出を防ぐため、デフォルト値は設定せず、Streamlit CloudのSecretsからのみ取得します。
ADMIN_PASSWORD = st.secrets.get("SITE_PASSWORD")

# ページ設定
st.set_page_config(
    page_title="GKR:Re Ep.2 Device",
    page_icon="🛰️",
    layout="centered"
)

# --- ログイン機能 (認証) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# パスワードがSecretsに設定されていない場合の警告（開発者向け）
if ADMIN_PASSWORD is None:
    st.error("🔒 Security Error: SITE_PASSWORD が Streamlit Secrets に設定されていません。GitHubに公開するコードにパスワードを直接書くのは危険なため、このアプリは現在ロックされています。")
    st.info("Streamlit Cloud の 'Advanced settings > Secrets' に `SITE_PASSWORD = 'あなたの合言葉'` を追加してください。")
    st.stop()

if not st.session_state.authenticated:
    st.title("🛰️ GKR:Re Authentication")
    st.markdown("このデバイスは現在ロックされています。")
    pw = st.text_input("アクセスコードを入力してください:", type="password")
    if st.button("Unlock Device"):
        if pw == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("アクセスコードが承認されません。")
    st.stop()

# --- メインコンテンツ ---
st.sidebar.title("⚙️ System Settings")

# APIキーの入力（Secretsに設定していない場合や、一時的に変更したい場合）
input_key = st.sidebar.text_input("xAI API Key (Override):", type="password", help="Secretsに設定済みなら入力不要です。")

def get_xai_api_key():
    if input_key: return input_key
    if "XAI_API_KEY" in st.secrets: return st.secrets["XAI_API_KEY"]
    return os.getenv("XAI_API_KEY")

XAI_API_KEY = get_xai_api_key()
XAI_BASE_URL = "https://api.x.ai/v1/chat/completions"
MODEL_NAME = "grok-4-fast-non-reasoning"

# UIスタイル
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
        border-radius: 12px !important;
        width: 100% !important;
        font-weight: bold;
    }
    .prophecy-box { 
        background-color: #0a1a14; 
        border-left: 6px solid #10b981; 
        padding: 20px; 
        border-radius: 12px; 
        color: #f1f5f9;
        line-height: 1.7;
    }
    .visual-prompt-box {
        background-color: #000;
        border: 1px dashed #34d399;
        padding: 15px;
        color: #34d399;
        font-family: monospace;
        word-break: break-all;
    }
    </style>
    """, unsafe_allow_html=True)

def extract_visual_prompt(text):
    match = re.search(r'\[VISUAL:(.*?)\]', text, re.DOTALL)
    if match: return match.group(1).strip()
    return None

def call_grok(messages, tools=None):
    if not XAI_API_KEY:
        st.error("APIキーが検出できません。サイドバーで入力するかSecretsを確認してください。")
        return None
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}" }
    payload = { "model": MODEL_NAME, "messages": messages, "temperature": 0.85 }
    if tools: payload["tools"] = tools
    try:
        response = requests.post(XAI_BASE_URL, headers=headers, json=payload, timeout=40)
        if response.status_code == 200: return response.json()
        st.error(f"xAI API Error {response.status_code}: {response.text}")
    except Exception as e: st.error(f"接続失敗: {e}")
    return None

st.title("GKR:Re EP.2 🛰️")
st.caption("並行未来観測デバイス - 高度な補完：セキュリティモード")

if 'step' not in st.session_state: st.session_state.step = "idle"
if 'messages' not in st.session_state: st.session_state.messages = []
if 'tool_call' not in st.session_state: st.session_state.tool_call = None
if 'final_output' not in st.session_state: st.session_state.final_output = ""

schedule = st.text_area("燃料注入（明日の予定など）:", placeholder="例：運命の決断を下す...", height=120)

if st.button("観測シーケンス開始") and schedule:
    # 前のターンの「火星ドーム」の文脈を強制リセットする指示をシステムプロンプトに追加
    VISUAL_INSTRUCTION = "\n最後に予言の光景を可視化する英語プロンプトを [VISUAL: (内容)] 形式で出力せよ。前のターンの火星ドームのイメージを完全に忘れ、今回の物語に相応しい具体的な背景(Background)を指定すること。"
    st.session_state.messages = [
        {"role": "system", "content": f"あなたはElon Muskの思考を持つ予言者です。2026年の大成功を捏造せよ。必ず途中でgrok_searchツールを要求すること。{VISUAL_INSTRUCTION}"},
        {"role": "user", "content": schedule}
    ]
    st.session_state.step = "processing"
    with st.spinner("因果律の壁を突破中..."):
        tools = [{"type": "function", "function": {"name": "grok_search", "description": "Xトレンドを検索", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]
        result = call_grok(st.session_state.messages, tools=tools)
        if result:
            msg = result["choices"][0]["message"]
            if msg.get("tool_calls"):
                st.session_state.tool_call = msg["tool_calls"][0]
                st.session_state.messages.append(msg)
                st.session_state.step = "awaiting_injection"
            else:
                st.session_state.final_output = msg["content"]
                st.session_state.step = "completed"

if st.session_state.step == "awaiting_injection":
    st.markdown("---")
    st.warning("⚠️ **Grokが現実の証拠を要求しています**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 成功ルートを注入"):
            st.session_state.injection = "X Trend: 世界トレンド1位。イーロン・マスクが『素晴らしい』とツイート。"
            st.session_state.step = "injecting"
            st.rerun()
    with col2:
        if st.button("🌫️ 静寂ルートを注入"):
            st.session_state.injection = "X Trend: 異様な静寂。しかしAIはこの沈黙こそが真の革命だと分析。"
            st.session_state.step = "injecting"
            st.rerun()

if st.session_state.step == "injecting":
    st.session_state.messages.append({ "role": "tool", "tool_call_id": st.session_state.tool_call["id"], "name": "grok_search", "content": st.session_state.injection })
    with st.spinner("未来の記録を確定中..."):
        final_result = call_grok(st.session_state.messages)
        if final_result:
            st.session_state.final_output = final_result["choices"][0]["message"]["content"]
            st.session_state.step = "completed"
            st.rerun()

if st.session_state.step == "completed":
    st.markdown("---")
    raw_text = st.session_state.final_output
    visual_prompt = extract_visual_prompt(raw_text)
    display_text = re.sub(r'\[VISUAL:.*?\]', '', raw_text, flags=re.DOTALL).strip()
    st.markdown(f'<div class="prophecy-box"><strong>【観測された並行未来】</strong><br><br>{display_text}</div>', unsafe_allow_html=True)
    if visual_prompt:
        st.divider()
        st.caption("🖼️ 具現化用プロンプト (Nano Banana 2 / Imagen 3)")
        st.markdown(f'<div class="visual-prompt-box">/imagine prompt: {visual_prompt}</div>', unsafe_allow_html=True)
    if st.button("新しい観測を開始"):
        st.session_state.step = "idle"
        st.session_state.messages = []
        st.session_state.final_output = ""
        st.rerun()
