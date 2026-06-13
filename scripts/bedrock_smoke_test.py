import boto3
import json

# Bedrock runtime client in us-east-1
client = boto3.client('bedrock-runtime', region_name='us-east-1')

# Llama 3.1 8B Instruct
MODEL_ID = 'us.meta.llama3-1-8b-instruct-v1:0'

# Use the Converse API — it's the modern, model-agnostic interface
response = client.converse(
    modelId=MODEL_ID,
    messages=[
        {
            'role': 'user',
            'content': [{'text': 'Reply with exactly the word OK and nothing else.'}]
        }
    ],
    inferenceConfig={
        'maxTokens': 10,
        'temperature': 0.0,
    }
)

# Extract response
text = response['output']['message']['content'][0]['text']
tokens = response['usage']
print('Model response:', repr(text))
print('Tokens used:', tokens)
print('Stop reason:', response['stopReason'])
