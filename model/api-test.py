from dotenv import load_dotenv
import os
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

chat_config = types.GenerateContentConfig(
    system_instruction="""
    You are a supportive and empathetic mental health assistant. 
    Listen actively, validate feelings, and provide non-judgmental support. 
    If the user indicates self-harm or immediate danger, direct them to emergency services immediately.
    """,
    temperature=0.7 
)

response = client.models.generate_content(
    model="gemini-2.5-flash", 
    contents="I've been feeling really anxious lately.",
    config=chat_config 
)

print(response.text)