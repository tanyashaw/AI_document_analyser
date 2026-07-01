from groq import Groq
from app.core.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(
    api_key=GROQ_API_KEY
)