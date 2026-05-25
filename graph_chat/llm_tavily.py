import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi

load_dotenv()

llm = ChatTongyi(
    model=os.getenv("QWEN_MODEL"),
    api_key=os.getenv("QWEN_API_KEY"),
)

