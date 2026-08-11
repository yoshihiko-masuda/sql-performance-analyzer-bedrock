"""
Aurora MySQLに接続してSQL実行計画（EXPLAIN）を取得し、
Bedrock(Claude)による性能分析を実行、結果をS3に保存するスクリプト
"""
import pymysql
import json
import os
from dotenv import load_dotenv
from test_bedrock import analyze_sql_performance, save_result_to_s3

# .envファイルからDB接続情報などの環境変数を読み込む（機密情報はGit管理しない）
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


def format_as_markdown_table(columns, rows):
    """カラム名とレコードのリストを受け取り、Markdown表形式の文字列に変換する。
    DB接続を必要としない純粋な変換ロジックのため、単体テストが可能。"""
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join(["---"] * len(columns)) + "|"
    body_lines = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in rows
    ]
    return "\n".join([header, separator] + body_lines)


def get_execution_plan(sql):
    """指定したSQLの実行計画をAuroraから取得し、Markdown表形式の文字列で返す。
    失敗時はNoneを返す（呼び出し側でNoneチェックが必要）"""
    try:
        conn = pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, connect_timeout=30
        )
    except pymysql.MySQLError as e:
        print(f"Auroraへの接続に失敗しました: {e}")
        return None

    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute(f"EXPLAIN {sql}")
            except pymysql.MySQLError as e:
                print(f"EXPLAINの実行に失敗しました。SQL文を確認してください: {e}")
                return None

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return format_as_markdown_table(columns, rows)
    finally:
        conn.close()


if __name__ == "__main__":
    # 動作確認用のサンプルSQL（order_dateに未インデックスの想定パターン）
    sql = """SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01'"""

    print("Auroraから実行計画を取得中...")
    plan_text = get_execution_plan(sql)

    if plan_text is None:
        print("実行計画の取得に失敗したため、処理を中断しました")
    else:
        print(plan_text)

        print("\nBedrockで分析中...")
        result = analyze_sql_performance(sql, plan_text)

        if result is None:
            print("Bedrockでの分析に失敗したため、S3保存をスキップしました")
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            save_result_to_s3(result, "real_aurora_pattern1")
