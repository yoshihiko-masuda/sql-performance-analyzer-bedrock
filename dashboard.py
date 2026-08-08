import streamlit as st
import json
from analyze_real_sql import get_execution_plan
from test_bedrock import analyze_sql_performance, save_result_to_s3

st.set_page_config(page_title="SQL性能分析ダッシュボード", layout="wide")

st.title("SQL性能分析ダッシュボード")
st.caption("AWS Bedrock（Claude）を使って、Auroraの実行計画を自動分析します")

# --- SQL入力エリア ---
st.subheader("分析するSQL")
default_sql = """SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01'"""

sql = st.text_area("SQL文を入力してください", value=default_sql, height=120)

analyze_button = st.button("実行計画を取得してAI分析する", type="primary")

if analyze_button:
    # 入力が空の場合は、そもそも処理を始めない
    if not sql.strip():
        st.warning("SQL文を入力してください")
        st.stop()

    with st.spinner("Auroraから実行計画を取得中..."):
        plan_text = get_execution_plan(sql)

    # DB接続失敗・EXPLAIN失敗の場合、get_execution_planはNoneを返す
    if plan_text is None:
        st.error("実行計画の取得に失敗しました。SQL文の内容やAuroraへの接続状況を確認してください。")
        st.stop()

    st.subheader("実行計画（Aurora実データ）")
    st.code(plan_text, language="text")

    with st.spinner("Bedrockで分析中..."):
        result = analyze_sql_performance(sql, plan_text)

    # Bedrock呼び出し失敗・JSON解析失敗の場合、analyze_sql_performanceはNoneを返す
    if result is None:
        st.error("Bedrockでの分析に失敗しました。しばらく待ってから再度お試しください。")
        st.stop()

    # --- サマリー ---
    st.subheader("分析結果")
    st.info(result.get("summary", "サマリー情報がありません"))

    # --- ボトルネック ---
    st.markdown("### ボトルネック")
    severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    for b in result.get("bottlenecks", []):
        icon = severity_color.get(b.get("severity"), "⚪")
        st.markdown(f"{icon} **{b.get('operation', '不明')}**（{b.get('severity', '不明')}）")
        st.write(b.get("issue", ""))

    # --- 改善提案 ---
    st.markdown("### 改善提案")
    for r in result.get("recommendations", []):
        with st.expander(r.get("title", "改善提案")):
            st.write(r.get("description", ""))
            if r.get("sql_example"):
                st.code(r["sql_example"], language="sql")
            st.caption(f"期待効果：{r.get('expected_impact', '不明')}")

    # --- S3保存 ---
    try:
        save_result_to_s3(result, "dashboard_analysis")
        st.success("分析結果をS3に保存しました")
    except Exception as e:
        # save_result_to_s3内部でもエラーはキャッチしているが、念のため画面表示用に捕捉
        st.warning(f"S3への保存中に問題が発生しましたが、分析結果の表示は完了しています: {e}")
