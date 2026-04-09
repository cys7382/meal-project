import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import get_client, query_all

@st.cache_data(ttl=3600)
def load_schools():
    return pd.DataFrame(query_all("schools", "*"))

@st.cache_data(ttl=3600)
def load_school_data(school_code):
    meals = query_all("meals", "*", filters={"school_code": school_code})
    nutrition = query_all("nutrition", "*", filters={"school_code": school_code})
    return pd.DataFrame(meals), pd.DataFrame(nutrition)

def show():
    st.title("🏫 학교별 분석")
    df_schools = load_schools()
    if df_schools.empty:
        st.warning("학교 데이터가 없습니다.")
        return
    col1, col2 = st.columns(2)
    with col1:
        school_type = st.selectbox("학교 종류", ["전체"] + sorted(df_schools["school_type"].dropna().unique().tolist()))
    with col2:
        filtered = df_schools if school_type == "전체" else df_schools[df_schools["school_type"] == school_type]
        school_name = st.selectbox("학교 선택", sorted(filtered["school_name"].dropna().tolist()))
    school_code = df_schools[df_schools["school_name"] == school_name]["school_code"].values[0]
    with st.spinner(f"{school_name} 데이터 불러오는 중..."):
        df_meals, df_nutrition = load_school_data(school_code)
    if df_meals.empty:
        st.warning("해당 학교의 급식 데이터가 없습니다.")
        return
    col1, col2, col3 = st.columns(3)
    col1.metric("총 급식 횟수", f"{len(df_nutrition):,}회")
    col2.metric("총 메뉴 수", f"{len(df_meals):,}개")
    if not df_nutrition.empty:
        df_nutrition["calories"] = pd.to_numeric(df_nutrition["calories"], errors="coerce")
        col3.metric("평균 칼로리", f"{df_nutrition['calories'].mean():.0f} kcal")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 월별 평균 칼로리")
        if not df_nutrition.empty:
            df_nutrition["meal_date"] = pd.to_datetime(df_nutrition["meal_date"])
            df_nutrition["월"] = df_nutrition["meal_date"].dt.to_period("M").astype(str)
            monthly = df_nutrition.groupby("월")["calories"].mean().reset_index()
            fig = px.line(monthly, x="월", y="calories", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("🏆 인기 메뉴 TOP 20")
        if not df_meals.empty:
            top_menus = df_meals["dish_name"].value_counts().head(20).reset_index()
            top_menus.columns = ["메뉴명", "등장횟수"]
            fig = px.bar(top_menus, x="등장횟수", y="메뉴명", orientation="h", color="등장횟수", color_continuous_scale="Oranges")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)