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
        # 権限不足・バケット不存在など、AWS側からの明確なエラー
        print(f"S3への保存に失敗しました(AWSエラー): {e}")
    except BotoCoreError as e:
        # ネットワーク不通など、boto3内部のエラー
        print(f"S3への保存に失敗しました(接続エラー): {e}")


client = boto3.client("bedrock-runtime", region_name="ap-northeast-1")
model_id = "global.anthropic.claude-sonnet-5"


def analyze_sql_performance(sql, execution_plan_table):
    """SQLと実行計画を渡すと、Bedrockで分析してJSON(dict)を返す。
    失敗時はNoneを返す(呼び出し側でNoneチェックが必要)"""

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

    # 1. Bedrock呼び出し自体の失敗に備える
    try:
        response = client.converse(modelId=model_id, messages=messages)
    except ClientError as e:
        print(f"Bedrock呼び出しに失敗しました(AWSエラー): {e}")
        return None
    except BotoCoreError as e:
        print(f"Bedrock呼び出しに失敗しました(接続エラー): {e}")
        return None

    # 2. レスポンスの中にtextブロックが見つからない場合に備える
    output_text = None
    try:
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                output_text = block["text"]
                break
    except (KeyError, IndexError) as e:
        print(f"レスポンス形式が想定と異なります: {e}")
        return None

    if output_text is None:
        print("Bedrockのレスポンスにテキストが含まれていません")
        return None

    cleaned_text = output_text.strip()
    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text.split("\n", 1)[1]
        cleaned_text = cleaned_text.rsplit("```", 1)[0]

    # 3. JSONパース失敗に備える(モデルが指示通りJSONを返さない場合)
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"分析結果のJSON解析に失敗しました: {e}")
        print(f"受け取った内容: {cleaned_text[:200]}...")  # デバッグ用に先頭だけ表示
        return None
