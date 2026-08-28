import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment variables (Local .env support)
load_dotenv()

# Safely fetch keys from Streamlit Secrets or OS Environment
def get_secret(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)

gemini_key = get_secret("GEMINI_API_KEY")
mem0_key = get_secret("MEM0_API_KEY")

st.title("AI Self-Learning Assistant with Mem0")
user_id = st.text_input("User ID", value="vamshi")

# Validate API keys before running model code
if not gemini_key:
    st.error("GEMINI_API_KEY is missing! Please check Streamlit Secrets.")
    st.stop()

if not mem0_key:
    st.error("MEM0_API_KEY is missing! Please check Streamlit Secrets.")
    st.stop()

# Initialize API Clients
genai_client = genai.Client(api_key=gemini_key)
mem0_client = MemoryClient(api_key=mem0_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt
if prompt := st.chat_input("Ask something or tell me about yourself..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 1. Fetch relevant user memories from Mem0 safely
    memory_context = ""
    try:
        memories = mem0_client.get_all(user_id=user_id)
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

    # 2. Build system instruction configuration
    system_instruction = f"You are a helpful AI assistant. Relevant context about the user:\n{memory_context}" if memory_context else "You are a helpful AI assistant."
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction
    )

    # 3. Generate response with error catching
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
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

    # 4. Save new interaction to Mem0 memory
    try:
        mem0_client.add([{"role": "user", "content": prompt}], user_id=user_id)
    except Exception as err:
        st.warning(f"Could not save memory to Mem0: {err}")