import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import get_client, query_all

RECOMMENDED = {"calories": 650, "carbohydrate": 97.5, "protein": 20, "fat": 18, "calcium": 300, "iron": 4, "vitamin_a": 225, "vitamin_c": 30}

@st.cache_data(ttl=3600)
def load_nutrition():
    return pd.DataFrame(query_all("nutrition", "*"))

def show():
    st.title("🧪 영양성분 분석")
    with st.spinner("데이터 불러오는 중..."):
        df = load_nutrition()
    if df.empty:
        st.warning("영양 데이터가 없습니다.")
        return
    nutrients = ["calories", "carbohydrate", "protein", "fat", "calcium", "iron", "vitamin_a", "vitamin_c"]
    nutrient_names = ["칼로리", "탄수화물", "단백질", "지방", "칼슘", "철분", "비타민A", "비타민C"]
    for col in nutrients:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    st.subheader("📊 권장량 대비 평균 충족률")
    means = df[nutrients].mean()
    rates = [(means[n] / RECOMMENDED[n] * 100) for n in nutrients]
    rate_df = pd.DataFrame({"영양소": nutrient_names, "충족률(%)": rates})
    fig = px.bar(rate_df, x="영양소", y="충족률(%)", color="충족률(%)", color_continuous_scale="RdYlGn", range_color=[0, 150])
    fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="권장량 100%")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("🏫 영양소 분포")
    nutrient_sel = st.selectbox("영양소 선택", nutrient_names)
    nutrient_col = nutrients[nutrient_names.index(nutrient_sel)]
    fig = px.histogram(df, x=nutrient_col, nbins=50, labels={nutrient_col: nutrient_sel}, color_discrete_sequence=["#4ECDC4"])
    fig.add_vline(x=RECOMMENDED[nutrient_col], line_dash="dash", line_color="red", annotation_text=f"권장량 {RECOMMENDED[nutrient_col]}")
    st.plotly_chart(fig, use_container_width=True)