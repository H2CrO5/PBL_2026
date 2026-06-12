"""AWS Bedrock Claude 3 Haiku client wrapper.

Supports two authentication modes:
  1. Bearer Token (AWS_BEARER_TOKEN_BEDROCK) — direct HTTPS calls
  2. boto3 SigV4 (default AWS credentials) — standard SDK calls
"""

import json

import httpx

from config import (
    AWS_REGION,
    BEDROCK_BEARER_TOKEN,
    BEDROCK_ENDPOINT,
    BEDROCK_MODEL_ID,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)

_boto3_client = None


def _invoke_bearer(model_id: str, body: dict) -> dict:
    """Call Bedrock InvokeModel via HTTPS with Bearer Token auth."""
    url = f"{BEDROCK_ENDPOINT}/model/{model_id}/invoke"
    headers = {
        "Authorization": f"Bearer {BEDROCK_BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = httpx.post(url, headers=headers, json=body, timeout=60.0)
    if resp.status_code != 200:
        print(f"[Bedrock Error] status={resp.status_code} body={resp.text[:500]}")
    resp.raise_for_status()
    return resp.json()


def _invoke_boto3(model_id: str, body: dict) -> dict:
    """Call Bedrock InvokeModel via boto3 (SigV4)."""
    import boto3

    global _boto3_client
    if _boto3_client is None:
        _boto3_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    response = _boto3_client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    return json.loads(response["body"].read())


def invoke_model(model_id: str, body: dict) -> dict:
    """Call Bedrock InvokeModel using the best available auth method."""
    if BEDROCK_BEARER_TOKEN:
        return _invoke_bearer(model_id, body)
    return _invoke_boto3(model_id, body)


def invoke(
    prompt: str,
    system: str = "",
    max_tokens: int = LLM_MAX_TOKENS,
    temperature: float = LLM_TEMPERATURE,
) -> str:
    """Send a prompt to Claude 3 Haiku via Bedrock and return the response text."""
    messages = [{"role": "user", "content": prompt}]

    body = {
        "anthropic_version": "bedrock-2023-10-25",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        body["system"] = system

    result = invoke_model(BEDROCK_MODEL_ID, body)
    return result["content"][0]["text"]


def invoke_json(
    prompt: str,
    system: str = "",
    max_tokens: int = LLM_MAX_TOKENS,
    temperature: float = LLM_TEMPERATURE,
) -> dict:
    """Send a prompt and parse the response as JSON.

    The prompt should instruct the model to return valid JSON.
    Attempts to extract JSON from the response even if surrounded by text.
    """
    text = invoke(prompt, system=system, max_tokens=max_tokens, temperature=temperature)

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the response
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # Try array
    start = text.find("[")
    end = text.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")
