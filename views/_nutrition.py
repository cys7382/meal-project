import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import get_client

RECOMMENDED = {
    "carbohydrate": 97.5, "protein": 20, "fat": 18,
    "calcium": 300, "iron": 4, "vitamin_a": 225, "vitamin_c": 30
}
NUTRIENT_LABELS = {
    "carbohydrate": "탄수화물", "protein": "단백질", "fat": "지방",
    "calcium": "칼슘", "iron": "철분", "vitamin_a": "비타민A", "vitamin_c": "비타민C"
}
NUTRIENT_UNITS = {
    "carbohydrate": "g", "protein": "g", "fat": "g",
    "calcium": "mg", "iron": "mg", "vitamin_a": "μg", "vitamin_c": "mg"
}

@st.cache_data(ttl=3600)
def load_nutrition():
    client = get_client()
    data = client.table("nutrition").select(
        "carbohydrate, protein, fat, calcium, iron, vitamin_a, vitamin_c"
    ).limit(10000).execute().data
    return pd.DataFrame(data)

def show():
    st.title("🧪 영양성분 분석")
    st.caption("※ 최근 10,000건 기준 / 한 끼 급식 권장량 대비 충족률")
    with st.spinner("데이터 불러오는 중..."):
        df = load_nutrition()
    if df.empty:
        st.warning("영양 데이터가 없습니다.")
        return

    nutrients = list(RECOMMENDED.keys())
    for col in nutrients:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    st.subheader("📊 한 끼 권장량 대비 평균 충족률")
    st.caption("각 영양소의 학교급식 한 끼 권장량 기준으로 계산됩니다.")
    means = df[nutrients].mean()
    rates = [(means[n] / RECOMMENDED[n] * 100) for n in nutrients]
    rate_df = pd.DataFrame({
        "영양소": [NUTRIENT_LABELS[n] for n in nutrients],
        "충족률(%)": rates
    })
    fig = px.bar(rate_df, x="영양소", y="충족률(%)",
                 color="충족률(%)", color_continuous_scale="RdYlGn",
                 range_color=[0, 150],
                 text="충족률(%)")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.add_hline(y=100, line_dash="dash", line_color="gray", annotation_text="권장량 100%")
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("📈 급식 건수")
    nutrient_sel = st.selectbox("영양소 선택", [NUTRIENT_LABELS[n] for n in nutrients])
    nutrient_col = nutrients[[NUTRIENT_LABELS[n] for n in nutrients].index(nutrient_sel)]
    unit = NUTRIENT_UNITS[nutrient_col]
    rec_val = RECOMMENDED[nutrient_col]

    fig2 = px.histogram(df, x=nutrient_col, nbins=50,
                        color_discrete_sequence=["#4ECDC4"])
    fig2.add_vline(x=rec_val, line_dash="dash", line_color="red",
                   annotation_text=f"권장량 {rec_val}{unit}",
                   annotation_position="top right")
    fig2.update_layout(
        xaxis_title=f"{nutrient_sel} ({unit})",
        yaxis_title="급식 건수",
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)
