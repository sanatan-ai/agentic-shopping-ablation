import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.converse(
    modelId='us.meta.llama3-1-70b-instruct-v1:0',
    messages=[{'role': 'user', 'content': [{'text': 'Say OK.'}]}],
    inferenceConfig={'maxTokens': 10, 'temperature': 0.0},
)
print('70B response:', repr(response['output']['message']['content'][0]['text']))
print('Tokens:', response['usage'])
