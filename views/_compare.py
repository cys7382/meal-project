import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import query_all

EXCLUDE_INGREDIENTS = {"물"}

@st.cache_data(ttl=3600)
def load_supply():
    data = query_all("supply_stats", "region, ingredient_name, week_number, total_amount_g")
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def load_school_counts():
    data = query_all("schools", "edu_office_code")
    df = pd.DataFrame(data)
    return {
        "서울": len(df[df["edu_office_code"] == "B10"]),
        "부산": len(df[df["edu_office_code"] == "C10"]),
    }

def show():
    st.title("🗺️ 지역별 비교 분석")

    with st.spinner("데이터 불러오는 중..."):
        df = load_supply()
        school_counts = load_school_counts()

    if df.empty:
        st.info("수급량 데이터가 없습니다.")
        return

    df = df[~df["ingredient_name"].isin(EXCLUDE_INGREDIENTS)]

    regions = sorted(df["region"].unique().tolist())
    if len(regions) < 2:
        st.info("지역 데이터가 2개 이상 필요합니다.")
        return

    # 연간 총량
    annual = df.groupby(["region", "ingredient_name"])["total_amount_g"].sum().reset_index()
    annual["total_amount_kg"] = (annual["total_amount_g"] / 1000).round(1)

    # 서울 대비 부산 비율 계산
    pivot_annual = annual.pivot_table(index="ingredient_name", columns="region", values="total_amount_kg", aggfunc="sum").fillna(0)
    if "서울" in pivot_annual.columns and "부산" in pivot_annual.columns:
        pivot_annual["부산/서울(%)"] = (pivot_annual["부산"] / pivot_annual["서울"] * 100).round(1)

    st.subheader("📊 지역별 연간 재료 사용량 TOP 20")
    col1, col2 = st.columns(2)
    for i, region in enumerate(regions):
        with col1 if i == 0 else col2:
            school_count = school_counts.get(region, 0)
            st.subheader(f"🏙️ {region} ({school_count}개교)")
            top = annual[annual["region"] == region].nlargest(20, "total_amount_kg")[["ingredient_name", "total_amount_kg"]]
            top.columns = ["재료명", "연간총량(kg)"]
            fig = px.bar(top, x="연간총량(kg)", y="재료명", orientation="h",
                        color="연간총량(kg)", color_continuous_scale="Blues")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🔍 재료별 지역 비교")

    top_ingredients = annual.groupby("ingredient_name")["total_amount_kg"].sum().nlargest(50).index.tolist()
    selected_ing = st.selectbox("재료 선택", top_ingredients)

    ing_annual = annual[annual["ingredient_name"] == selected_ing].copy()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 연간 총량 비교")
        fig = px.bar(ing_annual, x="region", y="total_amount_kg",
                    color="region", text="total_amount_kg",
                    labels={"region": "지역", "total_amount_kg": "연간총량(kg)"},
                    color_discrete_sequence=["#0D9488", "#F59E0B"])
        fig.update_traces(texttemplate="%{text:.1f}kg", textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📈 부산/서울 비율 비교 TOP 20")
        if "부산/서울(%)" in pivot_annual.columns:
            ratio_df = pivot_annual["부산/서울(%)"].reset_index()
            ratio_df.columns = ["재료명", "비율(%)"]
            ratio_df = ratio_df[ratio_df["비율(%)"] > 0].nlargest(20, "비율(%)")
            fig2 = px.bar(ratio_df, x="비율(%)", y="재료명", orientation="h",
                         color="비율(%)", color_continuous_scale="RdYlGn",
                         range_color=[0, 150])
            fig2.add_vline(x=100, line_dash="dash", line_color="gray",
                          annotation_text="서울 기준 100%")
            fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("📅 주간 수요 비교")
    ing_weekly = df[df["ingredient_name"] == selected_ing].groupby(
        ["region", "week_number"])["total_amount_g"].sum().reset_index()
    ing_weekly["total_amount_kg"] = (ing_weekly["total_amount_g"] / 1000).round(2)

    fig3 = px.line(ing_weekly, x="week_number", y="total_amount_kg", color="region",
                 markers=True,
                 labels={"week_number": "주차", "total_amount_kg": "필요량(kg)", "region": "지역"},
                 color_discrete_sequence=["#0D9488", "#F59E0B"])
    st.plotly_chart(fig3, use_container_width=True)
