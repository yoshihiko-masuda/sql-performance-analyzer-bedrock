import boto3
import json

# Bedrockクライアントを作成
client = boto3.client("bedrock-runtime", region_name="ap-northeast-1")

# Claude Sonnet 5 のモデルID（Bedrock上での識別子）
model_id = "global.anthropic.claude-sonnet-5"

# 送信するメッセージ
messages = [
    {"role": "user", "content": [{"text": "こんにちは、動作確認です。調子はどうですか？"}]}
]

response = client.converse(
    modelId=model_id,
    messages=messages,
)

# 応答テキストを表示
output_text = response["output"]["message"]["content"][0]["text"]
print(output_text)
