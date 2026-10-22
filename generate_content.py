"""
Optional: writes an Instagram caption with Meta's Model API (Muse Spark).
Only used for one-off posts, or queue entries that have no saved "caption".

Muse Spark is a reasoning model, so its hidden thinking counts against the
token limit. reasoning_effort goes through extra_body because the openai SDK
does not know that parameter.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(base_url="https://api.meta.ai/v1", api_key=os.getenv("LLAMA_API_KEY"))
META_MODEL = "muse-spark-1.1"


def generate_caption(topic: str, brand_voice: str = "friendly and concise") -> str:
    prompt = f"""Write an Instagram caption about: {topic}

    Tone: {brand_voice}
    Requirements:
    - Under 150 words
    - Include 5-8 relevant hashtags at the end
    - No markdown formatting, plain text only
    - Do not use emojis excessively (max 3)
    """
    response = client.chat.completions.create(
        model=META_MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
        extra_body={"reasoning_effort": "minimal"},
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError(f"Model returned no visible content: {response}")
    return content.strip()


if __name__ == "__main__":
    print(generate_caption("a water-based walnut wood stain"))
