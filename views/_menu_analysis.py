import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import get_client, query_all

@st.cache_data(ttl=3600)
def load_data():
    client = get_client()
    meals = query_all("meals", "dish_name, meal_date, meal_type")
    classified = query_all("dish_classification", "dish_name_raw, dish_name_clean, category, cooking_method")
    return pd.DataFrame(meals), pd.DataFrame(classified)

def show():
    st.title("🥗 메뉴 분석")
    with st.spinner("데이터 불러오는 중..."):
        df_meals, df_classified = load_data()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 전체 인기 메뉴 TOP 30")
        top = df_meals["dish_name"].value_counts().head(30).reset_index()
        top.columns = ["메뉴명", "등장횟수"]
        fig = px.bar(top, x="등장횟수", y="메뉴명", orientation="h", color="등장횟수", color_continuous_scale="Oranges")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("📂 카테고리별 인기 메뉴")
        if not df_classified.empty:
            category = st.selectbox("카테고리 선택", sorted(df_classified["category"].dropna().unique()))
            cat_menus = df_classified[df_classified["category"] == category]["dish_name_raw"]
            cat_meals = df_meals[df_meals["dish_name"].isin(cat_menus)]
            top_cat = cat_meals["dish_name"].value_counts().head(20).reset_index()
            top_cat.columns = ["메뉴명", "등장횟수"]
            fig = px.bar(top_cat, x="등장횟수", y="메뉴명", orientation="h", color="등장횟수", color_continuous_scale="Greens")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig, use_container_width=True)
    st.subheader("🌸 계절별 인기 메뉴")
    if not df_meals.empty:
        df_meals["meal_date"] = pd.to_datetime(df_meals["meal_date"])
        df_meals["계절"] = df_meals["meal_date"].dt.month.map({12:"겨울",1:"겨울",2:"겨울",3:"봄",4:"봄",5:"봄",6:"여름",7:"여름",8:"여름",9:"가을",10:"가을",11:"가을"})
        season = st.selectbox("계절 선택", ["봄", "여름", "가을", "겨울"])
        season_top = df_meals[df_meals["계절"] == season]["dish_name"].value_counts().head(20).reset_index()
        season_top.columns = ["메뉴명", "등장횟수"]
        fig = px.bar(season_top, x="등장횟수", y="메뉴명", orientation="h", color_discrete_sequence=["#95E1D3"])
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)