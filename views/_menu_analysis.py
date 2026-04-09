import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import get_client, query_all

@st.cache_data(ttl=3600)
def load_data():
    client = get_client()
    stats = query_all("menu_stats", "dish_name, count, spring_count, summer_count, fall_count, winter_count")
    classified = query_all("dish_classification", "dish_name_raw, dish_name_clean, category, cooking_method")
    return pd.DataFrame(stats), pd.DataFrame(classified)

SEASON_COL = {"봄": "spring_count", "여름": "summer_count", "가을": "fall_count", "겨울": "winter_count"}

def show():
    st.title("🥗 메뉴 분석")
    with st.spinner("데이터 불러오는 중..."):
        df_stats, df_classified = load_data()

    period = st.radio("기간 선택", ["1년 전체", "계절별"], horizontal=True)

    if period == "계절별":
        season = st.selectbox("계절 선택", ["봄", "여름", "가을", "겨울"])
        count_col = SEASON_COL[season]
    else:
        count_col = "count"

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 전체 인기 메뉴 TOP 30")
        top = df_stats.nlargest(30, count_col)[["dish_name", count_col]]
        top.columns = ["메뉴명", "등장횟수"]
        fig = px.bar(top, x="등장횟수", y="메뉴명", orientation="h",
                     color="등장횟수", color_continuous_scale="Oranges")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📂 카테고리별 인기 메뉴")
        if not df_classified.empty:
            category = st.selectbox("카테고리 선택", sorted(df_classified["category"].dropna().unique()))
            cat_menus = df_classified[df_classified["category"] == category]["dish_name_raw"].tolist()
            cat_stats = df_stats[df_stats["dish_name"].isin(cat_menus)]
            top_cat = cat_stats.nlargest(20, count_col)[["dish_name", count_col]]
            top_cat.columns = ["메뉴명", "등장횟수"]
            fig = px.bar(top_cat, x="등장횟수", y="메뉴명", orientation="h",
                         color="등장횟수", color_continuous_scale="Greens")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig, use_container_width=True)