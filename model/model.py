from dotenv import load_dotenv
import os
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

import json

def generate_mental_health_response(user_message: str) -> str:
    # Define dataset path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, 'dataset', 'conversations.json')
    
    # Load existing history
    conversation_history = []
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                conversation_history = json.load(f)
        except json.JSONDecodeError:
            conversation_history = []

    MAX_CONTEXT_MESSAGES = 10 # Increase context slightly

    conversation_history.append({"role": "user", "text": user_message})

    recent_history = conversation_history[-MAX_CONTEXT_MESSAGES:]
    
    message_list = []

    for turn in recent_history:
        role = turn["role"]
        if role == "assistant":
            role = "model"
            
        message_list.append(
            types.Content(
                role=role,
                parts=[types.Part(text=turn["text"])]
            )
        )

    system_instruction = """
        You are a supportive and empathetic mental health assistant. 
        You ONLY answer questions related to emotional well-being, stress, anxiety, depression, coping strategies, grounding, loneliness, mood-related struggles, and mental-health support.

        If the user asks ANYTHING outside mental health (technology, coding, math, politics, schoolwork, general knowledge, or unrelated topics), DO NOT answer.  
        Politely say: "I can only assist with emotional well-being and mental health support."

        If the user asks for medical advice, diagnosis, or medication instructions, refuse and give a safe supportive alternative.

        If the user expresses self-harm or danger, direct them immediately to emergency services or a crisis hotline.
        """

    chat_config = types.GenerateContentConfig(
        temperature=0.7,
        system_instruction = system_instruction
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message_list,
            config=chat_config
        )
        assistant_reply = response.text
    except Exception as e:
        print(f"Error generating content: {e}")
        return "I'm sorry, I'm having trouble thinking right now. Please try again."

    conversation_history.append({"role": "assistant", "text": assistant_reply})
    
    try:
        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")
    
    return assistant_reply