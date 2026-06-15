"""Test whether Bedrock returns identical responses across two identical calls at temperature=0.0.

This addresses the determinism methodology question: even at temp=0, LLM providers
do not formally guarantee deterministic outputs. We verify empirically.

Output: prints two responses side-by-side and reports whether they match byte-for-byte.
"""
import boto3

PROMPT = (
    "List the first 5 prime numbers as a comma-separated list. "
    "Reply with the list and nothing else."
)
MODEL_ID = "us.meta.llama3-1-8b-instruct-v1:0"
REGION = "us-east-1"

client = boto3.client("bedrock-runtime", region_name=REGION)


def one_call(label: str) -> str:
    response = client.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": PROMPT}]}],
        inferenceConfig={"maxTokens": 50, "temperature": 0.0},
    )
    text = response["output"]["message"]["content"][0]["text"]
    tokens = response["usage"]
    print(f"\n--- {label} ---")
    print(f"Response: {text!r}")
    print(f"Tokens: in={tokens['inputTokens']}, out={tokens['outputTokens']}")
    return text


if __name__ == "__main__":
    print(f"Model:  {MODEL_ID}")
    print(f"Region: {REGION}")
    print(f"Prompt: {PROMPT!r}")
    print(f"Temperature: 0.0")

    r1 = one_call("Call 1")
    r2 = one_call("Call 2")

    print("\n" + "=" * 60)
    if r1 == r2:
        print("✓ DETERMINISTIC: both responses are byte-identical.")
    else:
        print("✗ NON-DETERMINISTIC: responses differ.")
        print(f"\nDiff:")
        print(f"  Call 1: {r1!r}")
        print(f"  Call 2: {r2!r}")