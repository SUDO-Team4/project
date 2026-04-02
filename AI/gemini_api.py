import os
import json
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    print("오류: ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    exit(1)

client = anthropic.Anthropic(api_key=API_KEY)
MODEL = "claude-opus-4-6"

HISTORY_FILE = "chat_history.json"
SUMMARY_THRESHOLD = 10  # 대화가 이 횟수를 넘으면 요약

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def summarize_history(history):
    if not history:
        return []
    conversation_text = "\n".join(
        f"{'나' if h['role'] == 'user' else 'AI'}: {h['content']}" for h in history
    )
    prompt = f"다음 대화를 3줄 이내로 요약해줘:\n\n{conversation_text}"
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.content[0].text
        print(f"\n[대화 요약 완료]\n{summary}\n")
        return [{"role": "user", "content": f"[이전 대화 요약]\n{summary}", "timestamp": datetime.now().isoformat()}]
    except Exception as e:
        print(f"요약 중 오류 발생: {e}")
        return history

def build_messages(saved_history):
    return [
        {"role": h["role"], "content": h["content"]}
        for h in saved_history
        if h.get("role") in ("user", "assistant")
    ]

# 히스토리 불러오기
saved_history = load_history()

print("챗봇 시작! 종료하려면 'exit' 입력")
turn_count = len([h for h in saved_history if h.get("role") == "user"])

while True:
    try:
        user_input = input("나: ")
    except (KeyboardInterrupt, EOFError):
        print("\n종료합니다.")
        break

    if user_input.lower() == "exit":
        print("종료합니다.")
        break

    if not user_input.strip():
        continue

    try:
        messages = build_messages(saved_history)
        messages.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=messages
        )
        ai_reply = response.content[0].text
        print(f"AI: {ai_reply}")

        timestamp = datetime.now().isoformat()
        saved_history.append({"role": "user", "content": user_input, "timestamp": timestamp})
        saved_history.append({"role": "assistant", "content": ai_reply, "timestamp": timestamp})
        turn_count += 1

        # 일정 횟수 초과 시 요약
        if turn_count >= SUMMARY_THRESHOLD:
            saved_history = summarize_history(saved_history)
            turn_count = 0

        save_history(saved_history)

    except anthropic.AuthenticationError:
        print("오류: API 키가 유효하지 않습니다. .env 파일을 확인하세요.")
    except anthropic.RateLimitError:
        print("오류: API 사용량 한도 초과. 잠시 후 다시 시도하세요.")
    except Exception as e:
        print(f"오류 발생: {e}")
