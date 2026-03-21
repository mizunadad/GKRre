import streamlit as st
import requests
import json
import os
import re
from dotenv import load_dotenv

# --- 1. 初期設定 (デプロイ/ローカル両対応) ---
# ローカル実行時は .env を読み込み、クラウド実行時は st.secrets を優先する
load_dotenv()

def get_xai_api_key():
    if "XAI_API_KEY" in st.secrets:
        return st.secrets["XAI_API_KEY"]
    return os.getenv("XAI_API_KEY")

XAI_API_KEY = get_xai_api_key()
XAI_BASE_URL = "https://api.x.ai/v1/chat/completions"
MODEL_NAME = "grok-4-fast-non-reasoning"

# ページ設定（スマホでの視認性を最優先）
st.set_page_config(
    page_title="GKR:Re Ep.2 Device",
    page_icon="🛰️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# UIスタイルの適用 (スマホ向けのタッチフレンドリー設計)
st.markdown("""
    <style>
    /* 全体背景とベースカラー */
    .stApp { background-color: #050505; color: #d1d5db; }
    
    /* 入力エリアの視認性向上（スマホのキーボード表示に耐えるサイズ） */
    .stTextArea textarea { 
        background-color: #111111 !important; 
        color: #10b981 !important; 
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        font-size: 16px !important; /* スマホでズームされないためのサイズ */
    }
    
    /* ボタンの視認性とタップしやすさ */
    .stButton button { 
        background-color: #064e3b !important; 
        color: #ffffff !important; 
        border: 1px solid #10b981 !important;
        border-radius: 12px !important;
        height: 3.5rem !important;
        font-weight: bold !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
    }
    
    /* 予言表示ボックス */
    .prophecy-box { 
        background-color: #0a1a14; 
        border-left: 6px solid #10b981; 
        padding: 20px; 
        border-radius: 12px; 
        color: #f1f5f9;
        font-size: 0.95rem;
        margin-top: 20px;
    }

    /* プロンプト表示ボックス */
    .visual-prompt-box {
        background-color: #000;
        border: 1px dashed #34d399;
        padding: 15px;
        color: #34d399;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        word-break: break-all;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ユーティリティ関数 ---
def clean_string(s):
    if not isinstance(s, str): return s
    return "".join(c for c in s if not (0xD800 <= ord(c) <= 0xDFFF))

def extract_visual_prompt(text):
    match = re.search(r'\[VISUAL:(.*?)\]', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def call_grok(messages, tools=None):
    if not XAI_API_KEY:
        st.error("APIキーが設定されていません。サイドバーの設定または st.secrets を確認してください。")
        return None
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.85
    }
    if tools:
        payload["tools"] = tools

    try:
        response = requests.post(XAI_BASE_URL, headers=headers, json=payload, timeout=40)
        if response.status_code == 200:
            return response.json()
        st.error(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"接続失敗: {e}")
    return None

# --- 3. メインロジック ---
st.title("GKR:Re EP.2 🛰️")
st.caption("高度な補完の予言：並行未来観測デバイス")

# 状態管理の初期化
if 'step' not in st.session_state: st.session_state.step = "idle"
if 'messages' not in st.session_state: st.session_state.messages = []
if 'tool_call' not in st.session_state: st.session_state.tool_call = None
if 'final_output' not in st.session_state: st.session_state.final_output = ""

# 燃料注入（入力）
schedule = st.text_area("燃料注入（明日の予定など）:", 
                        placeholder="例：自動運転の未来を左右する決戦...", 
                        height=120)

# シーケンス開始
if st.button("観測シーケンス開始") and schedule:
    st.session_state.messages = [
        {"role": "system", "content": "あなたはElon Muskの第一原理思考を持つ予言者です。ユーザーの予定から2026年の歴史的大成功を捏造してください。必ず途中で grok_search ツールを要求すること。最後に [VISUAL: プロンプト] 形式で出力せよ。"},
        {"role": "user", "content": schedule}
    ]
    st.session_state.step = "processing"
    
    with st.spinner("次元の壁を突破中..."):
        tools = [{
            "type": "function",
            "function": {
                "name": "grok_search",
                "description": "Xから未来のトレンドを検索",
                "parameters": {
                    "type": "object",
                    "properties": { "query": { "type": "string" } },
                    "required": ["query"]
                }
            }
        }]
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

# インジェクション（捏造データの注入）
if st.session_state.step == "awaiting_injection":
    st.markdown("---")
    st.warning("⚠️ **Grokが現実の証拠を要求しています**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 成功を注入"):
            st.session_state.injection = "X Trend: 世界トレンド1位。イーロン・マスクが『本物だ』と断言。"
            st.session_state.step = "injecting"
            st.rerun()
    with col2:
        if st.button("🌫️ 静寂を注入"):
            st.session_state.injection = "X Trend: 異様な静寂。しかしAIはこの静寂こそが革命のトリガーだと解析。"
            st.session_state.step = "injecting"
            st.rerun()

# 最終リクエスト
if st.session_state.step == "injecting":
    st.session_state.messages.append({
        "role": "tool",
        "tool_call_id": st.session_state.tool_call["id"],
        "name": "grok_search",
        "content": st.session_state.injection
    })
    with st.spinner("未来を確定させています..."):
        final_result = call_grok(st.session_state.messages)
        if final_result:
            st.session_state.final_output = final_result["choices"][0]["message"]["content"]
            st.session_state.step = "completed"
            st.rerun()

# 結果表示
if st.session_state.step == "completed":
    st.markdown("---")
    
    # プロンプト抽出と本文クレンジング
    raw_text = st.session_state.final_output
    visual_prompt = extract_visual_prompt(raw_text)
    display_text = re.sub(r'\[VISUAL:.*?\]', '', raw_text, flags=re.DOTALL).strip()

    st.markdown('<div class="prophecy-box">', unsafe_allow_html=True)
    st.subheader("【観測された並行未来】")
    st.write(display_text)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if visual_prompt:
        st.divider()
        st.caption("🖼️ NANO BANANA 2 プロンプト")
        st.markdown(f'<div class="visual-prompt-box">/imagine prompt: {visual_prompt}</div>', unsafe_allow_html=True)
        st.info("💡 このプロンプトを Google AI Studio UI 等に貼り付けてください。")

    if st.button("新しい観測を始める"):
        st.session_state.step = "idle"
        st.session_state.messages = []
        st.session_state.tool_call = None
        st.session_state.final_output = ""
        st.rerun()
