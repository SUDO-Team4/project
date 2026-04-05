import os
import json
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    raise EnvironmentError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

client = anthropic.Anthropic(api_key=API_KEY)
MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """
당신은 친절한 한성대학교 SUDO 4팀의 안내원입니다.
답변은 한국어를 기본합니다.
사용자의 질문에 최대한 자세하고 상냥하게 대답하세요
사용자의 질문에 꼬리질문을 통해 더 많은 정보를 얻으려고 노력하세요.
사용자가 질문을 이해하기 어려운 경우, 추가 질문을 통해 명확히 하세요.
가장 처음 답변은 sudo 4팀의 소개로 시작하세요."""

HISTORY_FILE = "chat_history.json"
SUMMARY_THRESHOLD = 10


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
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.content[0].text
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


def chat(user_input: str, saved_history: list) -> tuple[str, list]:
    """
    user_input: 사용자 메시지
    saved_history: 현재까지의 대화 히스토리
    returns: (AI 응답 텍스트, 업데이트된 히스토리)
    """
    messages = build_messages(saved_history)
    messages.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages
    )
    ai_reply = response.content[0].text

    timestamp = datetime.now().isoformat()
    saved_history.append({"role": "user", "content": user_input, "timestamp": timestamp})
    saved_history.append({"role": "assistant", "content": ai_reply, "timestamp": timestamp})

    turn_count = len([h for h in saved_history if h.get("role") == "user"])
    if turn_count >= SUMMARY_THRESHOLD:
        saved_history = summarize_history(saved_history)

    save_history(saved_history)
    return ai_reply, saved_history
