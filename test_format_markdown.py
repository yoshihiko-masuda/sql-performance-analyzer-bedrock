"""
format_as_markdown_table のロジックをテストする（DB接続不要）
"""
from analyze_real_sql import format_as_markdown_table


def test_基本的な変換ができる():
    columns = ["id", "type", "rows"]
    rows = [(1, "ALL", 1200000)]

    result = format_as_markdown_table(columns, rows)

    assert "| id | type | rows |" in result
    assert "| 1 | ALL | 1200000 |" in result


def test_複数行のデータを変換できる():
    columns = ["id", "table"]
    rows = [(1, "orders"), (2, "customers")]

    result = format_as_markdown_table(columns, rows)
    lines = result.split("\n")

    # ヘッダー行 + 区切り行 + データ2行 = 合計4行になるはず
    assert len(lines) == 4
    assert "orders" in lines[2]
    assert "customers" in lines[3]


def test_空のデータでもエラーにならない():
    columns = ["id"]
    rows = []

    result = format_as_markdown_table(columns, rows)

    # ヘッダーと区切り線だけが返る
    assert "| id |" in result
    assert result.count("\n") == 1  # ヘッダー行+区切り行の2行のみ


def test_none値が含まれていても文字列化される():
    columns = ["id", "key"]
    rows = [(1, None)]

    result = format_as_markdown_table(columns, rows)

    assert "None" in result


if __name__ == "__main__":
    test_基本的な変換ができる()
    test_複数行のデータを変換できる()
    test_空のデータでもエラーにならない()
    test_none値が含まれていても文字列化される()
    print("すべてのテストが成功しました")
