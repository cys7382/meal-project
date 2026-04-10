import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import query_all

@st.cache_data(ttl=3600)
def load_supply():
    return pd.DataFrame(query_all("supply_stats", "*"))

@st.cache_data(ttl=3600)
def load_menu_stats():
    return pd.DataFrame(query_all("menu_stats", "dish_name, count, spring_count, summer_count, fall_count, winter_count"))

def show():
    st.title("🗺️ 지역별 비교 분석")

    with st.spinner("데이터 불러오는 중..."):
        df_supply = load_supply()
        df_menu = load_menu_stats()

    if df_supply.empty:
        st.info("수급량 데이터가 없습니다. make_supply_stats.py를 실행해주세요.")
        return

    regions = sorted(df_supply["region"].unique().tolist())
    if len(regions) < 2:
        st.info("지역 데이터가 2개 이상 필요합니다.")
        return

    st.subheader("📊 지역별 연간 재료 사용량 비교")

    # 지역별 연간 총량
    annual = df_supply.groupby(["region", "ingredient_name"])["total_amount_g"].sum().reset_index()
    annual["total_amount_kg"] = (annual["total_amount_g"] / 1000).round(1)

    col1, col2 = st.columns(2)
    for i, region in enumerate(regions):
        with col1 if i == 0 else col2:
            st.subheader(f"🏙️ {region} TOP 20")
            top = annual[annual["region"] == region].nlargest(20, "total_amount_kg")[["ingredient_name", "total_amount_kg"]]
            top.columns = ["재료명", "연간총량(kg)"]
            fig = px.bar(top, x="연간총량(kg)", y="재료명", orientation="h",
                        color="연간총량(kg)", color_continuous_scale="Blues")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("🔍 재료별 지역 비교")
    search = st.text_input("재료명 입력 (예: 닭고기)")
    if search:
        ing_data = annual[annual["ingredient_name"].str.contains(search, na=False)]
        if ing_data.empty:
            st.warning("해당 재료 데이터가 없습니다.")
        else:
            fig = px.bar(ing_data, x="region", y="total_amount_kg",
                        color="region", text="total_amount_kg",
                        labels={"region": "지역", "total_amount_kg": "연간총량(kg)"},
                        color_discrete_sequence=["#0D9488", "#F59E0B"])
            fig.update_traces(texttemplate="%{text:.1f}kg", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📅 주간별 수요 비교")
    ing_options = annual.groupby("ingredient_name")["total_amount_kg"].sum().nlargest(30).index.tolist()
    selected_ing = st.selectbox("재료 선택", ing_options)

    weekly = df_supply[df_supply["ingredient_name"] == selected_ing].copy()
    weekly["total_amount_kg"] = (weekly["total_amount_g"] / 1000).round(1)

    fig = px.line(weekly, x="week_number", y="total_amount_kg", color="region",
                  markers=True,
                  labels={"week_number": "주차", "total_amount_kg": "필요량(kg)", "region": "지역"},
                  color_discrete_sequence=["#0D9488", "#F59E0B"])
    fig.update_layout(xaxis_title="주차", yaxis_title="필요량 (kg)")
    st.plotly_chart(fig, use_container_width=True)