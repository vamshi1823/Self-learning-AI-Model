import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment variables
load_dotenv()

# Configure API Keys
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_API_KEY")
mem0_key = os.getenv("MEM0_API_KEY") or os.getenv("Mem0_API_Key")

# Initialize Gemini Client and Mem0 Client
genai_client = genai.Client(api_key=gemini_key)
mem0_client = MemoryClient(api_key=mem0_key)

st.title("AI Self-Learning Assistant with Mem0")
user_id = st.text_input("User ID", value="Hello vamshi")

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

    # 1. Fetch relevant user memories from Mem0
    memories = mem0_client.get_all(filters={"user_id": user_id})
    memory_context = ""
    if isinstance(memories, list) and len(memories) > 0:
        memory_context = "\n".join([f"- {m.get('memory', '')}" for m in memories if isinstance(m, dict)])

    # 2. Build system instruction configuration using types.GenerateContentConfig
    system_instruction = f"You are a helpful AI assistant. Relevant context about the user:\n{memory_context}"
    config = types.GenerateContentConfig(
        system_instruction=system_instruction
    )

    # 3. Generate content using supported model ID
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=config
    )
    bot_reply = response.text

    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    # 4. Save new interaction to Mem0 memory
    mem0_client.add([{"role": "user", "content": prompt}], user_id=user_id)