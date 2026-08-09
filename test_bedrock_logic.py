"""
Bedrockのレスポンス処理ロジックをテストする（実際のAPI呼び出しは行わない）
"""
from test_bedrock import extract_text_from_response, clean_json_text, parse_analysis_result


# --- extract_text_from_response のテスト ---

def test_正常なレスポンスからテキストを取り出せる():
    response = {
        "output": {
            "message": {
                "content": [{"text": '{"summary": "テスト"}'}]
            }
        }
    }
    result = extract_text_from_response(response)
    assert result == '{"summary": "テスト"}'


def test_contentが空リストの場合はNoneを返す():
    response = {
        "output": {
            "message": {
                "content": []
            }
        }
    }
    result = extract_text_from_response(response)
    assert result is None


def test_想定外のレスポンス構造でもエラーにならずNoneを返す():
    response = {"unexpected": "structure"}
    result = extract_text_from_response(response)
    assert result is None


# --- clean_json_text のテスト ---

def test_コードブロック記法が除去される():
    text = '```json\n{"summary": "テスト"}\n```'
    result = clean_json_text(text)
    assert result == '{"summary": "テスト"}'


def test_コードブロック記法がない場合はそのまま返る():
    text = '{"summary": "テスト"}'
    result = clean_json_text(text)
    assert result == '{"summary": "テスト"}'


def test_前後の空白が除去される():
    text = '   {"summary": "テスト"}   '
    result = clean_json_text(text)
    assert result == '{"summary": "テスト"}'


# --- parse_analysis_result のテスト ---

def test_正常なJSON文字列をdictに変換できる():
    text = '{"summary": "テスト", "bottlenecks": []}'
    result = parse_analysis_result(text)
    assert result == {"summary": "テスト", "bottlenecks": []}


def test_不正なJSON文字列の場合はNoneを返す():
    text = 'これはJSONではありません'
    result = parse_analysis_result(text)
    assert result is None


def test_空文字列の場合はNoneを返す():
    text = ''
    result = parse_analysis_result(text)
    assert result is None


if __name__ == "__main__":
    test_正常なレスポンスからテキストを取り出せる()
    test_contentが空リストの場合はNoneを返す()
    test_想定外のレスポンス構造でもエラーにならずNoneを返す()
    test_コードブロック記法が除去される()
    test_コードブロック記法がない場合はそのまま返る()
    test_前後の空白が除去される()
    test_正常なJSON文字列をdictに変換できる()
    test_不正なJSON文字列の場合はNoneを返す()
    test_空文字列の場合はNoneを返す()
    print("すべてのテストが成功しました")
