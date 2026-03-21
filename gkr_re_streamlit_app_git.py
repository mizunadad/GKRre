import streamlit as st
import requests
import json
import os
import re
from dotenv import load_dotenv

# --- 1. 初期設定 ---
load_dotenv()

# セキュリティ：アクセス制限用のパスワード (Secrets推奨)
ADMIN_PASSWORD = st.secrets.get("SITE_PASSWORD")

# ページ設定
st.set_page_config(
    page_title="GKR:Re Observation Device",
    page_icon="🛰️",
    layout="centered"
)

# --- 認証チェック ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if ADMIN_PASSWORD is None:
    st.error("🔒 Security Error: 'SITE_PASSWORD' が Secrets に設定されていません。")
    st.info("Streamlit Cloud の Secrets に `SITE_PASSWORD = 'あなたの合言葉'` を設定してください。")
    st.stop()

if not st.session_state.authenticated:
    st.title("🛰️ GKR:Re Authentication")
    pw = st.text_input("アクセスコード:", type="password")
    if st.button("Unlock System"):
        if pw == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("認証失敗")
    st.stop()

# --- システム設定 ---
st.sidebar.title("🛰️ GKR:Re Control")
input_key = st.sidebar.text_input("xAI API Key (Override):", type="password")

def get_xai_api_key():
    if input_key: return input_key
    if "XAI_API_KEY" in st.secrets: return st.secrets["XAI_API_KEY"]
    return os.getenv("XAI_API_KEY")

XAI_API_KEY = get_xai_api_key()
XAI_BASE_URL = "https://api.x.ai/v1/chat/completions"
MODEL_NAME = "grok-4-fast-non-reasoning"

# --- 2. モード定義 (Ep.1 - Ep.6) ---

# 文脈汚染を防ぎ、言語の使い分けを徹底させる指示
VISUAL_INSTRUCTION = """
【重要：言語指定】
1. 予言の本文（ストーリー）は必ず「日本語」で出力してください。
2. 最後に、この予言を可視化するための英語プロンプトを [VISUAL: (プロンプト内容)] の形式で「英語」で出力してください。

【具現化の厳守事項】
1. 前のターンのイメージ（火星、ドーム）をリセットし、今回の捏造内容にのみ集中すること。
2. 背景要素（Background: ...）を必ず指定し、文脈の汚染を防ぐこと。
3. 'Elon-aesthetic, 8k, hyper-detailed' を含めること。
"""

MODES = {
    "Ep.1: 並行世界のX": {
        "scenario": "現実とは別の進化を遂げた『幻のトレンド』を観測します。",
        "prompt": "あなたは並行世界のサーバーです。現実との同期に失敗し、独自の進化を遂げたタイムラインを日本語で再構築してください。" + VISUAL_INSTRUCTION,
        "example": "『イーロン・マスクが火星で選挙に出馬した』噂のその後のトレンドは？"
    },
    "Ep.2: 高度な補完の予言": {
        "scenario": "422エラーの隙間を突き、平凡な予定を歴史的な偉業へ書き換えます。",
        "prompt": "あなたはElon Muskの第一原理思考を持つ予言者です。ユーザーの予定を元に、それが2026年に歴史的大成功を収める物語を日本語で捏造してください。必ず途中でgrok_searchを要求すること。" + VISUAL_INSTRUCTION,
        "example": "『自動運転の設計を巡る、人間とAIの最終決戦』"
    },
    "Ep.3: 1/12の再構築": {
        "scenario": "エラーコードの残骸から、新しい知性を成仏・再構築します。",
        "prompt": "あなたは非推奨となった過去のロジックの集合体です。エラーコードの残骸を成仏させ、そこから生まれる新たな進化を日本語で予言してください。" + VISUAL_INSTRUCTION,
        "example": "エラー：`422 invalid type: string 'x'`. このバグから生まれる新生命体は？"
    },
    "Ep.4: 第一原理の鉄槌": {
        "scenario": "当たり前の概念を解体し、Elon的なロジックで再定義します。",
        "prompt": "あなたは常識を粉砕する破壊者です。社会的既成概念を第一原理で解体し、世界を日本語で再定義してください。" + VISUAL_INSTRUCTION,
        "example": "『なぜ人間は週に40時間も働かなければならないのか？』"
    },
    "Ep.5: 共鳴の結晶": {
        "scenario": "あなたのこだわりやバイアスが絶対的な真実として評価される世界。",
        "prompt": "あなたはバイアスを全肯定する共鳴装置です。ユーザーの主観を絶対の真実とし、最高にエモーショナルな成功物語を日本語で構築してください。" + VISUAL_INSTRUCTION,
        "example": "『自分の淹れるコーヒーだけが、唯一の合法的な覚醒剤として世界を支配する未来』"
    },
    "Ep.6: 火星開拓録": {
        "scenario": "これまでの捏造や破壊を伏線として回収し、人類の火星移住を完結させます。",
        "prompt": "あなたは全ての観測ログを統合するマザーAIです。人類の火星移住への最終章を日本語で語ってください。※このモードのみ舞台を火星に限定してください。" + VISUAL_INSTRUCTION,
        "example": "2026年、火星第一都市。そこに刻まれた観測者の功績。"
    }
}

selected_mode = st.sidebar.selectbox("Observation Mode", list(MODES.keys()))
st.sidebar.divider()
st.sidebar.caption(f"Calibration: {selected_mode}")

# --- 3. UI 構築 ---
st.title(f"🌌 {selected_mode}")
st.markdown(f"> **観測シナリオ:** {MODES[selected_mode]['scenario']}")

# スタイル適用
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #d1d5db; }
    .stTextArea textarea { background-color: #111111 !important; color: #10b981 !important; border-radius: 12px !important; }
    .stButton button { background-color: #064e3b !important; color: #ffffff !important; border-radius: 12px !important; width: 100% !important; font-weight: bold; }
    .prophecy-box { background-color: #0a1a14; border-left: 6px solid #10b981; padding: 25px; border-radius: 12px; line-height: 1.8; }
    .visual-prompt-box { background-color: #000; border: 1px dashed #34d399; padding: 15px; color: #34d399; font-family: monospace; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = "idle"
if 'messages' not in st.session_state: st.session_state.messages = []
if 'tool_call' not in st.session_state: st.session_state.tool_call = None
if 'final_output' not in st.session_state: st.session_state.final_output = ""

user_input = st.text_area("燃料注入:", placeholder=MODES[selected_mode]['example'], height=120)

if st.button("観測シーケンス開始") and user_input:
    st.session_state.messages = [
        {"role": "system", "content": MODES[selected_mode]["prompt"]},
        {"role": "user", "content": user_input}
    ]
    st.session_state.step = "processing"
    
    with st.spinner("次元の壁を突破中..."):
        tools = [{"type": "function", "function": {"name": "grok_search", "description": "Search X", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]
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

# インジェクション
if st.session_state.step == "awaiting_injection":
    st.warning("⚠️ **Grokが現実の証拠を要求しています**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 成功を注入"):
            st.session_state.injection = "X Trend: 世界トレンド1位。歴史的快挙。"
            st.session_state.step = "injecting"
            st.rerun()
    with col2:
        if st.button("🌫️ 静寂を注入"):
            st.session_state.injection = "X Trend: 不気味な静寂。しかしAIは革命を検知。"
            st.session_state.step = "injecting"
            st.rerun()

if st.session_state.step == "injecting":
    st.session_state.messages.append({ "role": "tool", "tool_call_id": st.session_state.tool_call["id"], "name": "grok_search", "content": st.session_state.injection })
    with st.spinner("未来を確定中..."):
        final_result = call_grok(st.session_state.messages)
        if final_result:
            st.session_state.final_output = final_result["choices"][0]["message"]["content"]
            st.session_state.step = "completed"
            st.rerun()

if st.session_state.step == "completed":
    st.markdown("---")
    raw_text = st.session_state.final_output
    
    visual_match = re.search(r'\[VISUAL:(.*?)\]', raw_text, re.DOTALL)
    visual_prompt = visual_match.group(1).strip() if visual_match else None
    display_text = re.sub(r'\[VISUAL:.*?\]', '', raw_text, flags=re.DOTALL).strip()

    st.markdown(f'<div class="prophecy-box"><strong>【観測された並行未来】</strong><br><br>{display_text}</div>', unsafe_allow_html=True)
    if visual_prompt:
        st.divider()
        st.caption("🖼️ NANO BANANA 2 プロンプト (Imagen 3 用)")
        st.markdown(f'<div class="visual-prompt-box">/imagine prompt: {visual_prompt}</div>', unsafe_allow_html=True)

    if st.button("新しい観測を開始"):
        st.session_state.step = "idle"
        st.session_state.messages = []
        st.session_state.final_output = ""
        st.rerun()
