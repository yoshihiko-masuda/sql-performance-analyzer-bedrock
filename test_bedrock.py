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

sql_prompt = """あなたはSQLパフォーマンスチューニングの専門家です。
以下のSQL実行計画を分析し、必ず以下のJSON形式のみで出力してください。前置きや説明文は不要です。JSON以外の文字は一切出力しないでください。

【SQL】
SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01';

【実行計画】
| Operation | Cost | Rows |
|---|---|---|
| TABLE ACCESS FULL orders | 8500 | 1200000 |
| TABLE ACCESS FULL customers | 3200 | 500000 |
| HASH JOIN | 12000 | 45000 |

出力JSON形式：
{
  "summary": "全体の問題点を1〜2文で要約",
  "bottlenecks": [
    {"operation": "問題のある処理名", "severity": "high / medium / low", "issue": "何が問題か"}
  ],
  "recommendations": [
    {"title": "改善策のタイトル", "description": "改善内容の説明", "sql_example": "実際に実行できるSQL文（あれば）", "expected_impact": "期待される効果"}
  ]
}
"""

messages = [
    {"role": "user", "content": [{"text": sql_prompt}]}
]

response = client.converse(
    modelId=model_id,
    messages=messages,
)


# 応答テキストを表示
# content の中から text を持つブロックを探す
output_text = None
for block in response["output"]["message"]["content"]:
    if "text" in block:
        output_text = block["text"]
        break

if output_text is None:
    print("テキストが見つかりませんでした。response全体:")
    print(response)

# コードフェンス（```json や ```）が付いていたら取り除く
cleaned_text = output_text.strip()
if cleaned_text.startswith("```"):
    cleaned_text = cleaned_text.split("\n", 1)[1]  # 1行目（```json）を除去
    cleaned_text = cleaned_text.rsplit("```", 1)[0]  # 末尾の```を除去

# JSONとしてパースして表示
result = json.loads(cleaned_text)
print(json.dumps(result, indent=2, ensure_ascii=False))
