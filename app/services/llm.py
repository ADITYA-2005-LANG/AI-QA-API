import os
import time

from dotenv import load_dotenv
from google import genai
from fastapi import HTTPException, status

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=api_key,
    http_options={
        "timeout": 10000
    }
)


def ask_llm(question: str):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=question
            )

            usage = response.usage_metadata

            return {
                "answer": response.text,
                "prompt_tokens": usage.prompt_token_count,
                "completion_tokens": usage.candidates_token_count,
                "total_tokens": usage.total_token_count
            }

        except Exception as e:
            print(f"LLM attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="LLM service is temporarily unavailable"
                )