import streamlit as st
import pandas as pd
import plotly.express as px
import json
from views._db_connect import query_all

@st.cache_data(ttl=3600)
def load_cost_data():
    data = query_all("dish_classification", "dish_name_clean, category, cost_estimate, ingredients_detail")
    df = pd.DataFrame(data)
    df = df[df["cost_estimate"].notna()]
    return df

def show():
    st.title("💰 원가 분석")
    with st.spinner("데이터 불러오는 중..."):
        df = load_cost_data()
    if df.empty:
        st.info("분류 완료 후 확인 가능합니다.")
        return
    df["cost_estimate"] = pd.to_numeric(df["cost_estimate"], errors="coerce")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 카테고리별 평균 원가")
        cat_cost = df.groupby("category")["cost_estimate"].mean().reset_index()
        cat_cost.columns = ["카테고리", "평균원가(원)"]
        cat_cost = cat_cost.sort_values("평균원가(원)", ascending=False)
        fig = px.bar(cat_cost, x="카테고리", y="평균원가(원)", color="평균원가(원)", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("💸 원가 높은 메뉴 TOP 20")
        top_cost = df.nlargest(20, "cost_estimate")[["dish_name_clean", "category", "cost_estimate"]]
        top_cost.columns = ["메뉴명", "카테고리", "원가(원)"]
        st.dataframe(top_cost, use_container_width=True)
    st.divider()
    st.subheader("🔍 메뉴별 재료 원가 상세")
    search = st.text_input("메뉴명 검색")
    if search:
        result = df[df["dish_name_clean"].str.contains(search, na=False)]
        if result.empty:
            st.warning("검색 결과가 없습니다.")
        else:
            for _, row in result.iterrows():
                with st.expander(f"{row['dish_name_clean']} — 예상 원가: {row['cost_estimate']:.0f}원"):
                    if row["ingredients_detail"]:
                        try:
                            ingredients = json.loads(row["ingredients_detail"]) if isinstance(row["ingredients_detail"], str) else row["ingredients_detail"]
                            ing_df = pd.DataFrame(ingredients)
                            ing_df = ing_df.rename(columns={"name": "재료명", "amount": "양", "unit_price": "단가(원/g)"})
                            st.dataframe(ing_df, use_container_width=True)
                        except:
                            st.write(row["ingredients_detail"])