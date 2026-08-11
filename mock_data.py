"""
デプロイ環境（Streamlit Community Cloudなど）でAuroraに接続できない場合に使う、
あらかじめ用意した実行計画のサンプルデータ
"""

MOCK_EXECUTION_PLANS = {
    """SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01'""": """| id | select_type | table | partitions | type | possible_keys | key | key_len | ref | rows | filtered | Extra |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SIMPLE | o | None | ALL | None | None | None | None | 5 | 33.33 | Using where |
| 1 | SIMPLE | c | None | eq_ref | PRIMARY | PRIMARY | 4 | sql_portfolio.o.customer_id | 1 | 100.0 | None |"""
}

DEFAULT_MOCK_PLAN = """| id | select_type | table | partitions | type | possible_keys | key | key_len | ref | rows | filtered | Extra |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SIMPLE | sample_table | None | ALL | None | None | None | None | 100 | 50.0 | Using where |"""


def get_mock_execution_plan(sql):
    """SQLに対応するモック実行計画を返す。該当がなければデフォルトのモックを返す。"""
    return MOCK_EXECUTION_PLANS.get(sql, DEFAULT_MOCK_PLAN)
