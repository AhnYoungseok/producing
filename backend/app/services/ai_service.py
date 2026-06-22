def generate_with_llm_placeholder(prompt: str, context: dict) -> dict:
    return {
        "provider": "template",
        "status": "placeholder",
        "prompt_preview": prompt[:200],
        "note": "MVP에서는 외부 LLM API를 호출하지 않습니다. 추후 OpenAI API 등을 이 함수 뒤에 연결할 수 있습니다.",
        "context_keys": list(context.keys()),
    }
