import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from mem0 import MemoryClient

load_dotenv()

def get_secret(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)

gemini_key = get_secret("GEMINI_API_KEY")
mem0_key = get_secret("MEM0_API_KEY")

st.title("AI Self-Learning Assistant with Mem0")
user_id = st.text_input("User ID", value="vamshi")

if not gemini_key or not mem0_key:
    st.error("Missing API Keys! Please check Streamlit Secrets or your .env file.")
    st.stop()

genai_client = genai.Client(api_key=gemini_key)
mem0_client = MemoryClient(api_key=mem0_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask something or tell me about yourself..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 1. Safely fetch and parse user memories from Mem0
    memory_context = ""
    try:
        response = mem0_client.get_all(filters={"user_id": user_id})
        
        if isinstance(response, dict):
            mem_items = response.get("results", [])
        elif isinstance(response, list):
            mem_items = response
        else:
            mem_items = []

        memory_list = []
        for m in mem_items:
            if isinstance(m, dict) and "memory" in m:
                memory_list.append(str(m["memory"]))
            elif hasattr(m, "memory"):
                memory_list.append(str(m.memory))

        if memory_list:
            memory_context = "\n".join([f"- {item}" for item in memory_list])
    except Exception as e:
        st.warning(f"Mem0 fetch notice: {e}")

    # 2. Build system instruction configuration
    if memory_context:
        system_instruction = f"You are a helpful AI assistant. Relevant context about the user:\n{memory_context}"
    else:
        system_instruction = "You are a helpful AI assistant."

    config = types.GenerateContentConfig(
        system_instruction=system_instruction
    )

    # 3. Call Gemini with active flash model
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        bot_reply = response.text
    except Exception as err:
        st.error(f"Gemini API Error: {err}")
        st.stop()

    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    # 4. Save new user interaction to Mem0
    try:
        mem0_client.add([{"role": "user", "content": prompt}], user_id=user_id)
    except Exception as err:
        st.warning(f"Mem0 save notice: {err}")