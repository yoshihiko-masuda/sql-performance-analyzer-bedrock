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
