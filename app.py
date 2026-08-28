import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment variables (.env support for local execution)
load_dotenv()

# Helper function to reliably fetch keys from Streamlit Secrets or environment variables
def get_secret(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)

gemini_key = get_secret("GEMINI_API_KEY")
mem0_key = get_secret("MEM0_API_KEY")

st.title("AI Self-Learning Assistant with Mem0")
user_id = st.text_input("User ID", value="vamshi")

# Guard against missing keys
if not gemini_key or not mem0_key:
    st.error("Missing API Keys! Please check Streamlit Secrets or your .env file.")
    st.stop()

# Initialize SDK Clients
genai_client = genai.Client(api_key=gemini_key)
mem0_client = MemoryClient(api_key=mem0_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input loop
if prompt := st.chat_input("Ask something or tell me about yourself..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 1. Fetch memories using correct dictionary filter syntax for Mem0
    memory_context = ""
    try:
        memories = mem0_client.get_all(filters={"user_id": user_id})
        if isinstance(memories, list) and len(memories) > 0:
            memory_list = []
            for m in memories:
                if isinstance(m, dict) and "memory" in m:
                    memory_list.append(m["memory"])
                elif hasattr(m, "memory"):
                    memory_list.append(m.memory)
            memory_context = "\n".join([f"- {item}" for item in memory_list])
    except Exception as e:
        st.warning(f"Mem0 fetch notice: {e}")

    # 2. Configure system instruction
    system_instruction = f"You are a helpful AI assistant. Relevant context about the user:\n{memory_context}" if memory_context else "You are a helpful AI assistant."
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction
    )

    # 3. Call Gemini using current model identifier
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

    # 4. Save new user interaction to Mem0 memory
    try:
        mem0_client.add([{"role": "user", "content": prompt}], user_id=user_id)
    except Exception as err:
        st.warning(f"Mem0 save notice: {err}")