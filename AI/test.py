import google.generativeai as genai

API_KEY = ""  # 여기에 Gemini API 키 입력

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])

print("챗봇 시작! 종료하려면 'exit' 입력")

while True:
    user_input = input("나: ")
    if user_input.lower() == "exit":
        print("종료합니다.")
        break

    response = chat.send_message(user_input)
    print(f"AI: {response.text}")
