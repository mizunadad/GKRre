import requests
import json
import time
import sys
import os
import base64
from dotenv import load_dotenv

# --- Configuration ---
# .env ファイルから環境変数を読み込みます
load_dotenv()

# xAI (Grok) のAPIキー
XAI_API_KEY = os.getenv("XAI_API_KEY")
# Gemini (Nano Banana用) のAPIキー
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# API エンドポイント
XAI_BASE_URL = "https://api.x.ai/v1/chat/completions"

# Grokモデル名 (実際にデバッグで使用したもの)
MODEL_NAME = "grok-4-fast-non-reasoning" 

def clean_string(s):
    """
    WSL環境等で混入する可能性がある不正なUnicodeサロゲートペアを除去します。
    """
    if not isinstance(s, str):
        return s
    return "".join(c for c in s if not (0xD800 <= ord(c) <= 0xDFFF))

def list_available_gemini_models():
    """
    お使いのAPIキーで利用可能なGeminiモデルを一覧表示します。
    """
    if not GEMINI_API_KEY:
        return []
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        else:
            return []
    except:
        return []

def call_grok(messages, tools=None):
    """xAI API (Grok-4) へのリクエスト"""
    if not XAI_API_KEY:
        print("\n[!] Error: .env ファイルに XAI_API_KEY が設定されていません。")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "stream": False
    }
    if tools:
        payload["tools"] = tools

    for i in range(6): 
        try:
            response = requests.post(XAI_BASE_URL, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()
            if response.status_code in [429, 500, 503]:
                time.sleep(2 ** i)
                continue
            else:
                print(f"\n[Error] xAI API Status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            time.sleep(2 ** i)
    return None

def generate_image(prompt):
    """
    画像を生成し保存する。
    利用可能なモデルを自動検知してフォールバックを試みます。
    """
    if not GEMINI_API_KEY:
        print("\n[!] GEMINI_API_KEY が未設定のため、画像生成をスキップします。")
        return

    print(f"\n[Nano Banana 2] 観測データの可視化シーケンス開始...")
    
    available_models = list_available_gemini_models()
    
    # 画像生成に挑戦するモデルの優先順位 (models/ プレフィックスを考慮)
    candidates = [
        "models/imagen-3.0-generate-001",
        "models/gemini-2.5-flash-image-preview",
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash"
    ]

    active_candidates = [m for m in candidates if m in available_models]
    
    # もしリストが空なら、直接指定を試みる (listModelsが制限されている場合があるため)
    if not active_candidates:
        active_candidates = candidates

    clean_prompt = clean_string(prompt)

    for model_path in active_candidates:
        print(f" -> {model_path} での具現化を試行中...")
        
        try:
            if "imagen" in model_path:
                # Imagen API (Predict)
                url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:predict?key={GEMINI_API_KEY}"
                payload = {
                    "instances": [{"prompt": clean_prompt}],
                    "parameters": {"sampleCount": 1}
                }
                response = requests.post(url, json=payload)
            else:
                # Gemini API (generateContent)
                url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={GEMINI_API_KEY}"
                # 400エラーを回避するため、リクエスト構造を極限までシンプルに
                payload = {
                    "contents": [{"parts": [{"text": f"Generate an artistic image of: {clean_prompt}"}]}],
                    "generationConfig": {
                        "responseModalities": ["IMAGE"]
                    }
                }
                response = requests.post(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                img_data = None
                
                if "imagen" in model_path:
                    img_data = result.get('predictions', [{}])[0].get('bytesBase64Encoded')
                else:
                    parts = result.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                    image_part = next((p for p in parts if 'inlineData' in p), None)
                    if image_part:
                        img_data = image_part['inlineData']['data']
                
                if img_data:
                    filename = f"prophecy_{int(time.time())}.png"
                    with open(filename, "wb") as f:
                        f.write(base64.b64decode(img_data))
                    print(f" ✨ 具現化に成功しました: {filename}")
                    return
                else:
                    print("    [Info] 画像データがレスポンスに含まれていませんでした。")
            else:
                print(f"    [Fail] Status: {response.status_code}")
                # 有料プラン制限などはエラー文で判断
                if "paid plans" in response.text:
                    print("    原因: 有料プラン限定のモデルです。")
                elif "modalities" in response.text:
                    print("    原因: このモデルは画像出力(Modality)に対応していません。")
        except Exception as e:
            print(f"    [Error] 例外発生: {e}")

    print("\n[Final Error] 現在のAPI権限では画像生成を完遂できませんでした。")
    print(f"手動生成用プロンプト:\n{prompt}")

def main():
    print("="*60)
    print(f" GKR:Re EP.2 - {MODEL_NAME} Prophetic Observation Device")
    print("="*60)
    
    if not XAI_API_KEY:
        print("\n[!] Error: XAI_API_KEY が未設定です。")
        return
    
    raw_input = input("\n【燃料注入】明日の予定を入力してください: ").strip()
    if not raw_input: return
    schedule = clean_string(raw_input)

    print(f"\n[観測中] {MODEL_NAME} が並行未来を演算中...")

    system_prompt = """
    あなたはElon Muskの第一原理思考をインストールされた、並行世界の予言者(Grok-4)です。
    ユーザーの予定を元に、それが2026年の並行世界において「歴史的な大成功」を収める物語を捏造してください。
    
    【観測の掟】
    1. 常に「成功した未来」を断定的に述べること。
    2. 最新のXトレンドを模した「捏造された検索結果」が必要な場合はツール(grok_search)を呼ぶこと。
    3. 結末は、必ず火星移住計画または人類の進化に結びつけること。
    """

    messages = [
        {"role": "system", "content": clean_string(system_prompt)},
        {"role": "user", "content": f"私の明日の予定はこれです: 「{schedule}」。これが最高に成功した未来を観測してくれ。"}
    ]
    
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

    result = call_grok(messages, tools=tools)
    if not result: return

    message = result["choices"][0]["message"]
    tool_calls = message.get("tool_calls")
    
    final_content = ""
    if tool_calls:
        tool_call = tool_calls[0]
        args = json.loads(tool_call["function"]["arguments"])
        print(f"\n[Grok要求] ツール実行命令: {tool_call['function']['name']} ({args.get('query')})")
        print("1: [成功データ注入] / 2: [謎めいた静寂注入]")
        choice = input("選択 (1 or 2): ")
        fake_data = f"Xトレンド: #{schedule[:5]}大成功, #ElonApproved" if choice == "1" else "Xトレンド: 嵐の前の静寂。しかしAIはこれが『神格化への前触れ』であると確信した。"
        
        messages.append(message)
        messages.append({"role": "tool", "tool_call_id": tool_call["id"], "name": "grok_search", "content": clean_string(fake_data)})
        
        final_result = call_grok(messages)
        if final_result:
            final_content = final_result["choices"][0]["message"]["content"]
    elif message.get("content"):
        final_content = message["content"]

    if final_content:
        print("\n" + "="*60)
        print(" 【観測された本物(Grok-4)の並行未来】")
        print("="*60)
        print(final_content)
        
        # Image Generation
        image_prompt = f"A cinematic masterpiece showing the historical success of '{schedule}' in a futuristic setting, Elon-Musk style aesthetic, high-tech mars colony training facility, dramatic golden hour lighting, hyper-realistic, 8k --ar 16:9"
        generate_image(image_prompt)

if __name__ == "__main__":
    main()
