import streamlit as st
import pandas as pd
import plotly.express as px
import json
import time
from views._db_connect import get_client, query_all

EXCLUDE_INGREDIENTS = {"물"}
SEASON_MAP = {1:"겨울",2:"겨울",3:"봄",4:"봄",5:"봄",6:"여름",7:"여름",8:"여름",9:"가을",10:"가을",11:"가을",12:"겨울"}
SEASON_COL = {"봄": "spring_count", "여름": "summer_count", "가을": "fall_count", "겨울": "winter_count"}
REGION_MAP = {"전체": None, "서울": "B10", "부산": "C10"}

@st.cache_data(ttl=3600)
def load_schools():
    return pd.DataFrame(query_all("schools", "*"))

@st.cache_data(ttl=3600)
def load_menu_stats():
    client = get_client()
    all_data = []
    page = 0
    while True:
        for attempt in range(3):
            try:
                res = client.table("menu_stats").select(
                    "dish_name, count, spring_count, summer_count, fall_count, winter_count"
                ).range(page*1000, (page+1)*1000-1).execute()
                all_data.extend(res.data)
                if len(res.data) < 1000:
                    return pd.DataFrame(all_data)
                page += 1
                break
            except:
                if attempt == 2:
                    return pd.DataFrame(all_data)
                time.sleep(1)
    return pd.DataFrame(all_data)

@st.cache_data(ttl=3600)
def load_classified():
    return pd.DataFrame(query_all("dish_classification", "dish_name_raw, category, ingredients_detail"))

def load_school_meals(school_code):
    client = get_client()
    all_data = []
    page = 0
    while True:
        for attempt in range(3):
            try:
                res = client.table("meals").select("dish_name, meal_date").eq(
                    "school_code", school_code
                ).range(page*1000, (page+1)*1000-1).execute()
                all_data.extend(res.data)
                if len(res.data) < 1000:
                    return pd.DataFrame(all_data)
                page += 1
                break
            except:
                if attempt == 2:
                    return pd.DataFrame(all_data)
                time.sleep(1)
    return pd.DataFrame(all_data)

def show():
    st.title("📊 전체 현황")

    with st.spinner("데이터 불러오는 중..."):
        df_schools = load_schools()
        df_stats = load_menu_stats()
        df_classified = load_classified()

    # 모드 선택
    mode = st.radio("보기 모드", ["📊 전체 통계", "🪖 부대별 분석"], horizontal=True)

    st.divider()

    if mode == "📊 전체 통계":
        col1, col2 = st.columns(2)
        col1.metric("총 학교 수", f"{len(df_schools):,}개")
        col2.metric("총 고유 메뉴 수", f"{len(df_stats):,}개")

        categories = ["전체"] + sorted(df_classified["category"].dropna().unique().tolist())
        selected_cat = st.selectbox("카테고리 선택", categories)
        period = st.radio("기간 선택", ["1년 전체", "계절별"], horizontal=True)

        if period == "계절별":
            season = st.selectbox("계절 선택", ["봄", "여름", "가을", "겨울"])
            count_col = SEASON_COL[season]
        else:
            count_col = "count"

        if selected_cat != "전체":
            cat_menus = df_classified[df_classified["category"] == selected_cat]["dish_name_raw"].tolist()
            filtered_stats = df_stats[df_stats["dish_name"].isin(cat_menus)]
        else:
            filtered_stats = df_stats

        st.subheader("🏆 인기 메뉴 TOP 30")
        top = filtered_stats.nlargest(30, count_col)[["dish_name", count_col]]
        top.columns = ["메뉴명", "등장횟수"]
        fig = px.bar(top, x="등장횟수", y="메뉴명", orientation="h",
                     color="등장횟수", color_continuous_scale="Oranges")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🧂 인기 재료 TOP 30")

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

        if ingredient_counts:
            ing_df = pd.DataFrame(list(ingredient_counts.items()), columns=["재료명", "사용횟수"])
            ing_df = ing_df.nlargest(30, "사용횟수")
            fig2 = px.bar(ing_df, x="사용횟수", y="재료명", orientation="h",
                          color="사용횟수", color_continuous_scale="Greens")
            fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
            st.plotly_chart(fig2, use_container_width=True)

    else:  # 부대별 분석
        region_sel = st.selectbox("지역 선택", ["전체", "서울", "부산"], index=0)
        edu_code = REGION_MAP[region_sel]

        if edu_code:
            filtered_schools = df_schools[df_schools["edu_office_code"] == edu_code]
        else:
            filtered_schools = df_schools

        col1, col2 = st.columns(2)
        with col1:
            school_type = st.selectbox("학교 종류", ["전체"] + sorted(filtered_schools["school_type"].dropna().unique().tolist()))
        with col2:
            if school_type != "전체":
                filtered_schools = filtered_schools[filtered_schools["school_type"] == school_type]
            school_name = st.selectbox("부대 선택", sorted(filtered_schools["school_name"].dropna().tolist()))

        school_code = df_schools[df_schools["school_name"] == school_name]["school_code"].values[0]

        with st.spinner(f"{school_name} 데이터 불러오는 중..."):
            df_meals = load_school_meals(school_code)

        if df_meals.empty:
            st.warning("해당 부대의 급식 데이터가 없습니다.")
            return

        df_meals["meal_date"] = pd.to_datetime(df_meals["meal_date"])
        df_meals["계절"] = df_meals["meal_date"].dt.month.map(SEASON_MAP)

        st.metric("총 메뉴 수", f"{len(df_meals):,}개")
        st.divider()

        categories = ["전체"] + sorted(df_classified["category"].dropna().unique().tolist())
        selected_cat = st.selectbox("재료 카테고리 선택", categories)
        period = st.radio("기간 선택", ["1년 전체", "계절별"], horizontal=True)

        if period == "계절별":
            season = st.selectbox("계절 선택", ["봄", "여름", "가을", "겨울"])
            df_filtered = df_meals[df_meals["계절"] == season]
        else:
            df_filtered = df_meals

        st.subheader("🏆 인기 메뉴 TOP 20")
        top = df_filtered["dish_name"].value_counts().head(20).reset_index()
        top.columns = ["메뉴명", "등장횟수"]
        fig = px.bar(top, x="등장횟수", y="메뉴명", orientation="h",
                     color="등장횟수", color_continuous_scale="Oranges")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🧂 사용 재료 TOP 20")
        ingredient_counts = {}
        dish_counts = df_filtered["dish_name"].value_counts().to_dict()

        for _, row in df_classified.iterrows():
            if selected_cat != "전체" and row["category"] != selected_cat:
                continue
            detail = row["ingredients_detail"]
            if not detail:
                continue
            try:
                items = json.loads(detail) if isinstance(detail, str) else detail
                dish_name = row["dish_name_raw"]
                multiplier = dish_counts.get(dish_name, 0)
                if multiplier == 0:
                    continue
                for item in items:
                    name = item.get("name", "")
                    if not name or name in EXCLUDE_INGREDIENTS:
                        continue
                    ingredient_counts[name] = ingredient_counts.get(name, 0) + multiplier
            except:
                continue

        if ingredient_counts:
            ing_df = pd.DataFrame(list(ingredient_counts.items()), columns=["재료명", "사용횟수"])
            ing_df = ing_df.nlargest(20, "사용횟수")
            fig2 = px.bar(ing_df, x="사용횟수", y="재료명", orientation="h",
                          color="사용횟수", color_continuous_scale="Greens")
            fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("선택한 카테고리의 재료 데이터가 없습니다.")
