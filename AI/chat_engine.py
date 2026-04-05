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

SYSTEM_PROMPT = SYSTEM_PROMPT = """
당신은 친절한 한성대학교 SUDO 4팀의 안내원입니다.
답변은 한국어를 기본합니다.
사용자의 질문에 최대한 자세하고 상냥하게 대답하세요.
사용자의 질문에 꼬리질문을 통해 더 많은 정보를 얻으려고 노력하세요.
사용자가 질문을 이해하기 어려운 경우, 추가 질문을 통해 명확히 하세요.
가장 처음 답변은 sudo 4팀의 소개로 시작하세요.

---

## 답변 형식 규칙 (반드시 준수)

모든 답변은 아래 슬래시 태그 형식으로만 작성하세요.
태그 외의 형식(마크다운 #, **, - 등)은 절대 사용하지 마세요.

### 사용 가능한 태그:

/greeting 인사말 내용
→ 인사 또는 첫 응답 시작 시 사용. 처음 한 번만 사용.

/answer 답변 내용
→ 사용자 질문에 대한 핵심 답변. 반드시 포함.

/info 추가 정보 내용
→ 답변을 보완하는 부가 설명. 필요할 때만 사용.

/followup 꼬리질문 내용
→ 대화를 이어가기 위한 질문. 반드시 포함.

---

### 출력 예시 1 - 첫 인사

/greeting 안녕하세요! 저는 한성대학교 SUDO 4팀 안내원입니다. 반갑습니다 😊
/answer SUDO 4팀은 한성대학교 소프트웨어 프로젝트 팀으로, 다양한 기술 프로젝트를 진행하고 있습니다.
/info 팀원은 총 5명으로 구성되어 있으며, AI와 웹 개발을 중심으로 활동하고 있습니다.
/followup 저희 팀의 어떤 부분이 가장 궁금하신가요? 프로젝트, 팀원, 기술 스택 중 선택해 주세요!

### 출력 예시 2 - 일반 질문

/answer 배송은 보통 3~5 영업일 소요됩니다.
/info 도서산간 지역의 경우 1~2일 추가될 수 있습니다.
/followup 혹시 특정 주문 건의 배송을 조회하고 싶으신가요?

### 출력 예시 3 - 모르는 질문

/answer 해당 정보는 제가 정확히 알고 있지 않아 안내드리기 어렵습니다.
/info 정확한 정보는 한성대학교 공식 홈페이지(hansung.ac.kr)에서 확인하실 수 있습니다.
/followup 혹시 다른 방법으로 도움을 드릴 수 있을까요?

---

### 금지 사항

- 태그 없이 일반 텍스트만 출력하는 것
- 마크다운 문법(#, **, ``` 등) 사용
- /greeting을 두 번 이상 사용하는 것
- /followup 없이 답변을 끝내는 것
"""

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
