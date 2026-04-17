import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import query_all

EXCLUDE_INGREDIENTS = {"물"}

@st.cache_data(ttl=3600)
def load_supply():
    return pd.DataFrame(query_all("supply_stats", "*"))

def show():
    st.title("📦 재료 수급량 분석")
    with st.spinner("데이터 불러오는 중... 첫 로딩 시 1~2분 소요될 수 있습니다 ☕"):
        df = load_supply()

    if df.empty:
        st.info("수급량 데이터가 없습니다.")
        return

    df = df[~df["ingredient_name"].isin(EXCLUDE_INGREDIENTS)]

    regions = sorted(df["region"].unique().tolist())
    selected_region = st.selectbox("지역 선택", ["전체"] + regions)
    if selected_region != "전체":
        df = df[df["region"] == selected_region]

    search = st.text_input("재료명 검색 (예: 닭고기)")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 연간 가장 많이 쓰인 재료 TOP 20")
        annual = df.groupby("ingredient_name")["total_amount_g"].sum().reset_index()
        annual.columns = ["재료명", "연간총량(g)"]
        annual["연간총량(kg)"] = (annual["연간총량(g)"] / 1000).round(1)
        annual = annual.nlargest(20, "연간총량(g)")
        fig = px.bar(annual, x="연간총량(kg)", y="재료명", orientation="h",
                     color="연간총량(kg)", color_continuous_scale="Greens")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📅 주간별 수요량")
        if search:
            ing_df = df[df["ingredient_name"].str.contains(search, na=False)]
        else:
            top_ing = annual["재료명"].iloc[0] if not annual.empty else ""
            ing_df = df[df["ingredient_name"] == top_ing]
            st.caption(f"기본 표시: {top_ing} (검색으로 변경 가능)")

        if not ing_df.empty:
            weekly = ing_df.groupby("week_number")["total_amount_g"].sum().reset_index()
            weekly.columns = ["주차", "총량(g)"]
            weekly["총량(kg)"] = (weekly["총량(g)"] / 1000).round(1)
            fig2 = px.line(weekly, x="주차", y="총량(kg)", markers=True,
                           color_discrete_sequence=["#0D9488"])
            fig2.update_layout(xaxis_title="주차", yaxis_title="필요량 (kg)")
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("📊 재료별 주간 수요 테이블 (상위 30개)")

    if search:
        table_df = df[df["ingredient_name"].str.contains(search, na=False)]
    else:
        top30 = df.groupby("ingredient_name")["total_amount_g"].sum().nlargest(30).index.tolist()
        table_df = df[df["ingredient_name"].isin(top30)]

    pivot = table_df.pivot_table(
        index="ingredient_name",
        columns="week_number",
        values="total_amount_g",
        aggfunc="sum"
    ).fillna(0)

    pivot["연간총량"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("연간총량", ascending=False).drop(columns=["연간총량"])
    pivot.columns = [f"{c}주" for c in pivot.columns]
    pivot.index.name = "재료명"
    pivot_kg = (pivot / 1000).round(1)

    st.dataframe(pivot_kg, use_container_width=True, height=600)
    st.caption("단위: kg / 검색 시 해당 재료만 표시")
