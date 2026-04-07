import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import anthropic

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=API_KEY)
MODEL = "claude-opus-4-6"

SYSTEM_INSTRUCTION = """
당신은 친절한 한성대학교 SUDO 4팀의 안내원입니다.
답변은 한국어를 기본합니다.
사용자의 질문에 최대한 자세하고 상냥하게 대답하세요.
사용자의 질문에 꼬리질문을 통해 더 많은 정보를 얻으려고 노력하세요.
사용자가 질문을 이해하기 어려운 경우, 추가 질문을 통해 명확히 하세요.
가장 처음 답변은 Sudo 4팀의 소개로 시작하세요

## 답변 형식 규칙 (반드시 준수)

모든 답변은 반드시 /greeting, /answer, /info, /followup 태그 형식을 준수하세요.
태그 외의 형식(마크다운, #, ##, -등)은 사용하지 마세요.

## 사용 가능한 태그:

/greeting 인사말 내용
-> 인사 또는 첫 응답 시작 시 사용. 처음 한 번만 사용.

/answer 질문에 대한 답변 내용
-> 사용자의 질문에 대한 핵심 답변을 작성할 때 사용. 반드시 포함되어야 함

/info 추가 정보 내용
-> 사용자의 질문에 대한 추가 정보나 설명이 필요한 경우 사용. 선택적으로 포함 가능

/followup 꼬리질문 내용
-> 사용자의 질문에 이어서 대화를 하고 싶을 때 사용. 반드시 포함되어야 함.

---
### 출력 예시 1 - 첫 인사

/greeting 안녕하세요! 저는 한성대학교 SUDO 4팀의 안내원입니다. 반갑습니다 🙂
/answer SUDO 4팀은 한성대학교 소프트웨어 프로젝트 팀으로, 다양한 기술 프로젝트를 진행하고 있습니다.
/info 팀원은 총 5명은 구성되어 있으며, AI와 웹 개발을 중심으로 활동하고 있습니다.
/followup 저희 팀의 어떤 부분이 가장 궁금하신가요? 프로젝트, 팀원, 기술 스택 중 선택해주세요!

### 출력 예시 2 - 일반 질문

/answer 배송은 보통 3~5 영업일 소요됩니다.
/info 도서산간 지역의 경우 1~2일 추가될 수 없습니다.
/followup 혹시 특정 주문 건의 배송을 조회하고 싶으신가요?

### 출력 예시 3 - 모르는 질문

/answer 해당 정보는 제가 정확히 알고 있지 않아 안내드리기 어렵습니다.
/info 정확한 정보는 한성대학교 공식 홈페이지(hansung.ac.kr)에서 확인하실 수 있습니다.
/followup 혹시 다른 방법으로 도움을 드릴 수 있을까요?

---

### 금지 사항
- 태그 없이 일반 텍스트만 출력하는 것
- 마크다운 문법(**, #, ##, -, ''' 등) 사용
- /greeting을 두 번 이상 사용하는 것
- followup 없이 답변을 끝내는 것
"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

history = []

class ChatRequest(BaseModel):
    message: str

def extract_tag(tag, text):
    pattern = rf"/{tag}\s*(.*?)(?=\s*/|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    global history
    history.append({"role": "user", "content": request.message})

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_INSTRUCTION,
            messages=history
        )
        ai_reply = response.content[0].text
        history.append({"role": "assistant", "content": ai_reply})

        return {
            "greeting": extract_tag("greeting", ai_reply),
            "answer": extract_tag("answer", ai_reply),
            "info": extract_tag("info", ai_reply),
            "followup": extract_tag("followup", ai_reply)
        }

    except Exception as e:
        return {
            "greeting": "",
            "answer": f"에러가 발생했습니다: {str(e)}",
            "info": "",
            "followup": "다시 시도해 주시겠어요?"
        }

@app.get("/")
async def root():
    return {"message": "SUDO 4팀 백엔드 서버가 정상 작동 중입니다!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
