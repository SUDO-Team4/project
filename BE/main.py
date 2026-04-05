import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import re

# .env 파일 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# AI 설정
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI() 바로 아래에 추가하세요
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 실전에서는 리액트 주소(http://localhost:3000)만 넣는 게 안전해요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 승진님이 설계한 시스템 프롬프트 (가독성을 위해 변수화)
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
/answer SUDO 4팀은 한성대학교 소프트웨어 프로젝트 팀으로, 다양한 기술 프로젝트를 진행하고 있습니다. 저희 팀은 AI, 웹 개발, 모바일 앱 등 다양한 분야에서 활동하고 있습니다. 
/info 팀원은 총 5명은 구성되어 있으며, AI와 웹 개발을 중심으로 활동하고 있습니다. 
/followup 저희 팀의 어떤 부분이 가장 궁금하신가요? 프로젝트, 팀원, 기술 스택 중 선택해주세요!

### 출력 예시 2 - 일반 질문

/answer 배송은 보통 3~5 영업일 소요됩니다. 
/info 도서산간 지역의 경우 1~2일 추가될 수 없습니다.
/followup 혹시 특정 주문 건의 배송을 조회하고 싶으신가요? 

### 출력 예시 3 - 모르는 질문 

/answer 해당 정보는 제가 정확히 알고 있지 않아 안내드리기 어렵습니다. 
/info 정확한 정보는 한성대학교 공식 홈페이지(hansung.ac.kr)에서 확인하실 수 있습니다. 
/followup 혹시 다른 방법으로 도움을 드릴 수 있을까요? 예를 들어, 학교 시설 이용 방법이나 학사 일정 등에 대해 궁금하신 점이 있으신가요? 

--- 

### 금지 사항 
- 태그 없이 일반 텍스트만 출력하는 것
- 마크다운 문법(**, #, ##, -, ''' 등) 사용
- /greeting을 두 번 이상 사용하는 것
- followup 없이 답변을 끝내는 것
"""

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # 시스템 프롬프트와 사용자 메시지를 결합
    full_prompt = f"{SYSTEM_INSTRUCTION}\n\n사용자 질문: {request.message}"
    
    try:
        # 1. AI로부터 답변을 받아옵니다.
        response = model.generate_content(full_prompt)
        ai_reply = response.text

        # 2. 특정 태그(/greeting 등) 뒤의 텍스트를 추출하는 보조 함수입니다.
        def extract_tag(tag, text):
            # 정규표현식: /태그 뒤부터 다음 /가 나오거나 문장이 끝날 때까지 추출
            pattern = rf"/{tag}\s*(.*?)(?=\s*/|$)"
            match = re.search(pattern, text, re.DOTALL)
            return match.group(1).strip() if match else ""

        # 3. 답변을 쪼개서 예쁜 JSON(딕셔너리) 형태로 만듭니다.
        structured_data = {
            "greeting": extract_tag("greeting", ai_reply),
            "answer": extract_tag("answer", ai_reply),
            "info": extract_tag("info", ai_reply),
            "followup": extract_tag("followup", ai_reply)
        }
        
        # 이제 프론트엔드는 하나의 통문장이 아니라 4개의 조각으로 데이터를 받습니다!
        return structured_data

    except Exception as e:
        # 에러 발생 시에도 프론트엔드가 당황하지 않게 형식을 맞춰줍니다.
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