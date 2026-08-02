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
    with st.spinner("Auroraから実行計画を取得中..."):
        plan_text = get_execution_plan(sql)

    st.subheader("実行計画（Aurora実データ）")
    st.code(plan_text, language="text")

    with st.spinner("Bedrockで分析中..."):
        result = analyze_sql_performance(sql, plan_text)

    # --- サマリー ---
    st.subheader("分析結果")
    st.info(result["summary"])

    # --- ボトルネック ---
    st.markdown("### ボトルネック")
    severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    for b in result["bottlenecks"]:
        icon = severity_color.get(b["severity"], "⚪")
        st.markdown(f"{icon} **{b['operation']}**（{b['severity']}）")
        st.write(b["issue"])

    # --- 改善提案 ---
    st.markdown("### 改善提案")
    for r in result["recommendations"]:
        with st.expander(r["title"]):
            st.write(r["description"])
            if r.get("sql_example"):
                st.code(r["sql_example"], language="sql")
            st.caption(f"期待効果：{r['expected_impact']}")

    # --- S3保存 ---
    save_result_to_s3(result, "dashboard_analysis")
    st.success("分析結果をS3に保存しました")
