import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import get_client, query_all

@st.cache_data(ttl=3600)
def load_data():
    schools = query_all("schools", "*")
    nutrition = query_all("nutrition", "meal_date, calories, carbohydrate, protein, fat")
    classified = query_all("dish_classification", "category")
    return pd.DataFrame(schools), pd.DataFrame(nutrition), pd.DataFrame(classified)

def show():
    st.title("📊 전체 통계 대시보드")
    with st.spinner("데이터 불러오는 중..."):
        df_schools, df_nutrition, df_classified = load_data()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 학교 수", f"{len(df_schools):,}개")
    col2.metric("분류된 메뉴 수", f"{len(df_classified):,}개")
    if not df_nutrition.empty:
        df_nutrition["calories"] = pd.to_numeric(df_nutrition["calories"], errors="coerce")
        col3.metric("평균 칼로리", f"{df_nutrition['calories'].mean():.0f} kcal")
        col4.metric("수집된 영양데이터", f"{len(df_nutrition):,}건")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏫 학교 종류별 분포")
        if not df_schools.empty:
            type_count = df_schools["school_type"].value_counts().reset_index()
            type_count.columns = ["학교종류", "학교수"]
            fig = px.pie(type_count, names="학교종류", values="학교수", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("🍽️ 메뉴 카테고리별 분포")
        if not df_classified.empty:
            cat_count = df_classified["category"].value_counts().reset_index()
            cat_count.columns = ["카테고리", "메뉴수"]
            fig = px.bar(cat_count, x="카테고리", y="메뉴수", color="메뉴수", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)
    st.subheader("📈 월별 평균 칼로리 추이")
    if not df_nutrition.empty:
        df_nutrition["meal_date"] = pd.to_datetime(df_nutrition["meal_date"])
        df_nutrition["월"] = df_nutrition["meal_date"].dt.to_period("M").astype(str)
        monthly = df_nutrition.groupby("월")["calories"].mean().reset_index()
        monthly.columns = ["월", "평균칼로리"]
        fig = px.line(monthly, x="월", y="평균칼로리", markers=True, color_discrete_sequence=["#FF6B6B"])
        fig.add_hline(y=650, line_dash="dash", line_color="gray", annotation_text="권장 칼로리 650kcal")
        st.plotly_chart(fig, use_container_width=True)