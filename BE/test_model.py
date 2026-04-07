import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY") # 승진님이 설정한 변수명 그대로!
genai.configure(api_key=API_KEY)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)