import streamlit as st
import pandas as pd
import plotly.express as px
from views._db_connect import get_client, query_all
import json

EXCLUDE_INGREDIENTS = {"물", "소금", "설탕"}

@st.cache_data(ttl=3600)
def load_schools():
    return pd.DataFrame(query_all("schools", "school_code"))

@st.cache_data(ttl=3600)
def load_menu_stats():
    return pd.DataFrame(query_all("menu_stats", "dish_name, count, spring_count, summer_count, fall_count, winter_count"))

@st.cache_data(ttl=3600)
def load_classified():
    return pd.DataFrame(query_all("dish_classification", "dish_name_raw, category, ingredients_detail"))

SEASON_KO = {"spring": "봄", "summer": "여름", "fall": "가을", "winter": "겨울"}
SEASON_COL = {"봄": "spring_count", "여름": "summer_count", "가을": "fall_count", "겨울": "winter_count"}

def show():
    st.title("📊 전체 통계 대시보드")
    with st.spinner("데이터 불러오는 중..."):
        df_schools = load_schools()
        df_stats = load_menu_stats()
        df_classified = load_classified()

    col1, col2 = st.columns(2)
    col1.metric("총 학교 수", f"{len(df_schools):,}개")
    col2.metric("총 고유 메뉴 수", f"{len(df_stats):,}개")

    st.divider()

    # 카테고리 필터
    categories = ["전체"] + sorted(df_classified["category"].dropna().unique().tolist())
    selected_cat = st.selectbox("카테고리 선택", categories)

    period = st.radio("기간 선택", ["1년 전체", "계절별"], horizontal=True)
    if period == "계절별":
        season = st.selectbox("계절 선택", ["봄", "여름", "가을", "겨울"])
        count_col = SEASON_COL[season]
    else:
        count_col = "count"

    st.subheader("🏆 인기 메뉴 TOP 30")

    # 카테고리 필터 적용
    if selected_cat != "전체":
        cat_menus = df_classified[df_classified["category"] == selected_cat]["dish_name_raw"].tolist()
        filtered_stats = df_stats[df_stats["dish_name"].isin(cat_menus)]
    else:
        filtered_stats = df_stats

    top = filtered_stats.nlargest(30, count_col)[["dish_name", count_col]]
    top.columns = ["메뉴명", "등장횟수"]
    fig = px.bar(top, x="등장횟수", y="메뉴명", orientation="h",
                 color="등장횟수", color_continuous_scale="Oranges")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🧂 인기 재료 TOP 30")

    if df_classified.empty or df_classified["ingredients_detail"].isna().all():
        st.info("재료 데이터가 없습니다.")
        return

    ingredient_counts = {}
    for _, row in df_classified.iterrows():
        if selected_cat != "전체" and row["category"] != selected_cat:
            continue
        detail = row["ingredients_detail"]
        if not detail:
            continue
        try:
            items = json.loads(detail) if isinstance(detail, str) else detail
            dish_name = row["dish_name_raw"]
            dish_count = df_stats[df_stats["dish_name"] == dish_name][count_col].values
            multiplier = int(dish_count[0]) if len(dish_count) > 0 else 1
            for item in items:
                name = item.get("name", "")
                if not name or name in EXCLUDE_INGREDIENTS:
                    continue
                ingredient_counts[name] = ingredient_counts.get(name, 0) + multiplier
        except:
            continue

    if not ingredient_counts:
        st.info("선택한 카테고리의 재료 데이터가 없습니다.")
        return

    ing_df = pd.DataFrame(list(ingredient_counts.items()), columns=["재료명", "사용횟수"])
    ing_df = ing_df.nlargest(30, "사용횟수")
    fig2 = px.bar(ing_df, x="사용횟수", y="재료명", orientation="h",
                  color="사용횟수", color_continuous_scale="Greens")
    fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
    st.plotly_chart(fig2, use_container_width=True)
