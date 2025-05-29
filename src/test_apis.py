import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests


def test_gemini_api(gemini_api_key):
    genai.configure(api_key=gemini_api_key)

    # Example usage (refer to Gemini API docs)
    model = genai.GenerativeModel("gemini-2.0-flash")  # Or other suitable model
    prompt = "Explain how AI works in simple terms."
    response = model.generate_content(prompt)
    print(response.text)


def test_perplexity_api(perplexity_api_key):
    # Example usage (refer to Perplexity API docs for actual endpoints/payloads)
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain how AI works in simple terms."},
        ],
    }  # Your query
    response = requests.post(
        "https://api.perplexity.ai/chat/completions", headers=headers, json=payload
    )
    print(response.json())


if __name__ == "__main__":
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    # test_gemini_api(gemini_api_key)

    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    if not perplexity_api_key:
        raise ValueError("PERPLEXITY_API_KEY environment variable is not set.")
    test_perplexity_api(perplexity_api_key)
