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

    # 서울이 항상 왼쪽
    regions = ["서울", "부산"]

    # 연간 총량
    annual = df.groupby(["region", "ingredient_name"])["total_amount_g"].sum().reset_index()
    annual["total_amount_kg"] = (annual["total_amount_g"] / 1000).round(1)

    # 피벗 테이블
    pivot_annual = annual.pivot_table(
        index="ingredient_name", columns="region",
        values="total_amount_kg", aggfunc="sum"
    ).fillna(0)

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

    # 재료 선택 — 차이 적은 순 (배추 맨 위)
    if "서울" in pivot_annual.columns and "부산" in pivot_annual.columns:
        common = pivot_annual[(pivot_annual["서울"] > 1) & (pivot_annual["부산"] > 1)].copy()
        common["차이비율"] = abs(common["서울"] - common["부산"]) / (common["서울"] + common["부산"])
        sorted_ingredients = common.sort_values("차이비율").index.tolist()
        # 배추 맨 위로
        if "배추" in sorted_ingredients:
            sorted_ingredients.remove("배추")
            sorted_ingredients = ["배추"] + sorted_ingredients
    else:
        sorted_ingredients = annual.groupby("ingredient_name")["total_amount_kg"].sum().nlargest(50).index.tolist()

    selected_ing = st.selectbox("재료 선택", sorted_ingredients)
    ing_annual = annual[annual["ingredient_name"] == selected_ing].copy()
    # 서울 먼저 오도록 정렬
    ing_annual["region"] = pd.Categorical(ing_annual["region"], categories=["서울", "부산"], ordered=True)
    ing_annual = ing_annual.sort_values("region")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 연간 총량 비교")
        fig = px.bar(ing_annual, x="region", y="total_amount_kg",
                    color="region", text="total_amount_kg",
                    labels={"region": "지역", "total_amount_kg": "연간총량(kg)"},
                    color_discrete_map={"서울": "#F59E0B", "부산": "#0D9488"})
        fig.update_traces(texttemplate="%{text:.1f}kg", textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🌟 지역 특색 재료")
        tab1, tab2 = st.tabs(["🟠 서울 특색", "🟢 부산 특색"])

        if "서울" in pivot_annual.columns and "부산" in pivot_annual.columns:
            filtered = pivot_annual[(pivot_annual["서울"] > 1) & (pivot_annual["부산"] > 1)].copy()
            filtered["서울비율"] = (filtered["서울"] / filtered["부산"]).round(1)
            filtered["부산비율"] = (filtered["부산"] / filtered["서울"]).round(1)

            with tab1:
                seoul_top = filtered.nlargest(15, "서울비율")[["서울", "부산", "서울비율"]].reset_index()
                seoul_top.columns = ["재료명", "서울(kg)", "부산(kg)", "서울/부산 비율"]
                fig2 = px.bar(seoul_top, x="서울/부산 비율", y="재료명", orientation="h",
                             color="서울/부산 비율", color_continuous_scale="Oranges")
                fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
                st.plotly_chart(fig2, use_container_width=True)
                st.caption("서울이 부산보다 상대적으로 많이 쓰는 재료")

            with tab2:
                busan_top = filtered.nlargest(15, "부산비율")[["서울", "부산", "부산비율"]].reset_index()
                busan_top.columns = ["재료명", "서울(kg)", "부산(kg)", "부산/서울 비율"]
                fig3 = px.bar(busan_top, x="부산/서울 비율", y="재료명", orientation="h",
                             color="부산/서울 비율", color_continuous_scale="Teal")
                fig3.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
                st.plotly_chart(fig3, use_container_width=True)
                st.caption("부산이 서울보다 상대적으로 많이 쓰는 재료")

    st.divider()
    st.subheader("📅 주간 수요 비교")
    ing_weekly = df[df["ingredient_name"] == selected_ing].groupby(
        ["region", "week_number"])["total_amount_g"].sum().reset_index()
    ing_weekly["total_amount_kg"] = (ing_weekly["total_amount_g"] / 1000).round(2)

    fig4 = px.line(ing_weekly, x="week_number", y="total_amount_kg", color="region",
                 markers=True,
                 labels={"week_number": "주차", "total_amount_kg": "필요량(kg)", "region": "지역"},
                 color_discrete_map={"서울": "#F59E0B", "부산": "#0D9488"})
    st.plotly_chart(fig4, use_container_width=True)
