import boto3
import json
from datetime import datetime

s3_client = boto3.client("s3", region_name="ap-northeast-1")
BUCKET_NAME = "sql-performance-portfolio-2026"

def save_result_to_s3(result, label):
    """分析結果をS3にJSONファイルとして保存する"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"results/{label}_{timestamp}.json"

    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(result, ensure_ascii=False, indent=2),
        ContentType="application/json"
    )
    print(f"S3に保存しました: s3://{BUCKET_NAME}/{key}")

client = boto3.client("bedrock-runtime", region_name="ap-northeast-1")
model_id = "global.anthropic.claude-sonnet-5"


def analyze_sql_performance(sql, execution_plan_table):
    """SQLと実行計画を渡すと、Bedrockで分析してJSON(dict)を返す"""

    prompt = f"""あなたはSQLパフォーマンスチューニングの専門家です。
以下のSQL実行計画を分析し、必ず以下のJSON形式のみで出力してください。前置きや説明文は不要です。JSON以外の文字は一切出力しないでください。

【SQL】
{sql}

【実行計画】
{execution_plan_table}

出力JSON形式：
{{
  "summary": "全体の問題点を1〜2文で要約",
  "bottlenecks": [
    {{"operation": "問題のある処理名", "severity": "high / medium / low", "issue": "何が問題か"}}
  ],
  "recommendations": [
    {{"title": "改善策のタイトル", "description": "改善内容の説明", "sql_example": "実際に実行できるSQL文（あれば）", "expected_impact": "期待される効果"}}
  ]
}}
"""

    messages = [{"role": "user", "content": [{"text": prompt}]}]
    response = client.converse(modelId=model_id, messages=messages)

    output_text = None
    for block in response["output"]["message"]["content"]:
        if "text" in block:
            output_text = block["text"]
            break

    cleaned_text = output_text.strip()
    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text.split("\n", 1)[1]
        cleaned_text = cleaned_text.rsplit("```", 1)[0]

    return json.loads(cleaned_text)


if __name__ == "__main__":
    # パターン1：JOIN + フルスキャン
    sql1 = """SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01';"""

    plan1 = """| Operation | Cost | Rows |
|---|---|---|
| TABLE ACCESS FULL orders | 8500 | 1200000 |
| TABLE ACCESS FULL customers | 3200 | 500000 |
| HASH JOIN | 12000 | 45000 |"""

    # パターン2：サブクエリ + ソート処理が重いケース
    sql2 = """SELECT product_id, SUM(amount) as total
FROM sales
WHERE sale_date BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY product_id
ORDER BY total DESC;"""

    plan2 = """| Operation | Cost | Rows |
|---|---|---|
| TABLE ACCESS FULL sales | 15000 | 3000000 |
| SORT GROUP BY | 22000 | 8000 |
| SORT ORDER BY | 23500 | 8000 |"""

    print("=== パターン1 ===")
    result1 = analyze_sql_performance(sql1, plan1)
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    save_result_to_s3(result1, "pattern1")


    print("\n=== パターン2 ===")
    result2 = analyze_sql_performance(sql2, plan2)
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    save_result_to_s3(result2, "pattern2")
