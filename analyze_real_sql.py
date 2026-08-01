import pymysql
import json
import os
from dotenv import load_dotenv
from test_bedrock import analyze_sql_performance, save_result_to_s3

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


def get_execution_plan(sql):
    """指定したSQLの実行計画をAuroraから取得し、Markdown表形式の文字列で返す"""
    conn = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, connect_timeout=30
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"EXPLAIN {sql}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            # Markdown表形式に変換
            header = "| " + " | ".join(columns) + " |"
            separator = "|" + "|".join(["---"] * len(columns)) + "|"
            body_lines = [
                "| " + " | ".join(str(v) for v in row) + " |"
                for row in rows
            ]
            return "\n".join([header, separator] + body_lines)
    finally:
        conn.close()


if __name__ == "__main__":
    sql = """SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01'"""

    print("Auroraから実行計画を取得中...")
    plan_text = get_execution_plan(sql)
    print(plan_text)

    print("\nBedrockで分析中...")
    result = analyze_sql_performance(sql, plan_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    save_result_to_s3(result, "real_aurora_pattern1")
