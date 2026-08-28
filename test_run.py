import os
from dotenv import load_dotenv
from mem0 import MemoryClient

# 1. Load your secret API keys from the .env file
load_dotenv()

# 2. Connect to the Mem0 Memory service
client = MemoryClient(api_key=os.getenv("Mem0_API_Key"))

# 3. Add a user memory
print("Adding memory to Mem0...")
messages = [
    {"role": "user", "content": "Hi, I am building an AI portfolio project using Gemini and Mem0."}
]
client.add(messages, user_id="Hello vamshi")

# 4. Fetch and print stored memories
print("Retrieving memories from Mem0:")
memories = client.get_all(user_id="varun")
print(memories)