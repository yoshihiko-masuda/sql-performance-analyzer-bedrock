import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

s3_client = boto3.client("s3", region_name="ap-northeast-1")
BUCKET_NAME = "sql-performance-portfolio-2026"


def save_result_to_s3(result, label):
    """分析結果をS3にJSONファイルとして保存する"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"results/{label}_{timestamp}.json"

    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(result, ensure_ascii=False, indent=2),
            ContentType="application/json"
        )
        print(f"S3に保存しました: s3://{BUCKET_NAME}/{key}")
    except ClientError as e:
        print(f"S3への保存に失敗しました(AWSエラー): {e}")
    except BotoCoreError as e:
        print(f"S3への保存に失敗しました(接続エラー): {e}")


client = boto3.client("bedrock-runtime", region_name="ap-northeast-1")
model_id = "global.anthropic.claude-sonnet-5"


def extract_text_from_response(response):
    """Bedrockのレスポンスから、テキストブロックを取り出す。
    見つからない場合はNoneを返す。"""
    try:
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                return block["text"]
    except (KeyError, IndexError):
        return None
    return None


def clean_json_text(text):
    """Bedrockの出力からコードブロック記法（```）を取り除き、
    JSONとしてパースできる形式に整形する"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip()


def parse_analysis_result(text):
    """整形済みテキストをJSON(dict)としてパースする。
    失敗時はNoneを返す。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"分析結果のJSON解析に失敗しました: {e}")
        print(f"受け取った内容: {text[:200]}...")
        return None


def analyze_sql_performance(sql, execution_plan_table):
    """SQLと実行計画を渡すと、Bedrockで分析してJSON(dict)を返す。
    失敗時はNoneを返す（呼び出し側でNoneチェックが必要）"""

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

    try:
        response = client.converse(modelId=model_id, messages=messages)
    except ClientError as e:
        print(f"Bedrock呼び出しに失敗しました(AWSエラー): {e}")
        return None
    except BotoCoreError as e:
        print(f"Bedrock呼び出しに失敗しました(接続エラー): {e}")
        return None

    output_text = extract_text_from_response(response)
    if output_text is None:
        print("Bedrockのレスポンスにテキストが含まれていません")
        return None

    cleaned_text = clean_json_text(output_text)
    return parse_analysis_result(cleaned_text)


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
    if result1:
        print(json.dumps(result1, indent=2, ensure_ascii=False))
        save_result_to_s3(result1, "pattern1")
    else:
        print("パターン1の分析に失敗したため、S3保存をスキップしました")

    print("\n=== パターン2 ===")
    result2 = analyze_sql_performance(sql2, plan2)
    if result2:
        print(json.dumps(result2, indent=2, ensure_ascii=False))
        save_result_to_s3(result2, "pattern2")
    else:
        print("パターン2の分析に失敗したため、S3保存をスキップしました")
