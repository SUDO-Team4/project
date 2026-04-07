import anthropic
from chat_engine import chat, load_history

saved_history = load_history()

print("챗봇 시작! 종료하려면 'exit' 입력")

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
        ai_reply, saved_history = chat(user_input, saved_history)
        print(f"AI: {ai_reply}")
    except anthropic.AuthenticationError:
        print("오류: API 키가 유효하지 않습니다. .env 파일을 확인하세요.")
    except anthropic.RateLimitError:
        print("오류: API 사용량 한도 초과. 잠시 후 다시 시도하세요.")
    except Exception as e:
        print(f"오류 발생: {e}")
