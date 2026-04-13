import streamlit as st
import pandas as pd
import plotly.express as px
import json
from views._db_connect import query_all, get_client

@st.cache_data(ttl=3600)
def load_schools():
    return pd.DataFrame(query_all("schools", "*"))

@st.cache_data(ttl=3600)
def load_classified():
    return pd.DataFrame(query_all("dish_classification", "dish_name_raw, category, ingredients_detail"))

@st.cache_data(ttl=3600)
def get_schools_with_data():
    # menu_stats에 있는 학교코드 기반으로 확인 (이미 집계된 데이터 활용)
    client = get_client()
    res = client.table("meals").select("school_code").limit(1000).execute()
    codes = set(r["school_code"] for r in res.data)
    page = 1
    while len(res.data) == 1000:
        res = client.table("meals").select("school_code").range(page*1000, (page+1)*1000-1).execute()
        codes.update(r["school_code"] for r in res.data)
        page += 1
        if page > 300:  # 최대 30만건까지만 확인
            break
    return codes

SEASON_MAP = {1:"겨울",2:"겨울",3:"봄",4:"봄",5:"봄",6:"여름",7:"여름",8:"여름",9:"가을",10:"가을",11:"가을",12:"겨울"}
EXCLUDE_INGREDIENTS = {"물", "소금", "설탕"}

def load_school_meals(school_code):
    from views._db_connect import query_with_retry
    meals = query_with_retry("meals", "dish_name, meal_date", filters={"school_code": school_code})
    return pd.DataFrame(meals)

def show():
    st.title("🪖 부대별 분석")
    df_schools = load_schools()
    if df_schools.empty:
        st.warning("학교 데이터가 없습니다.")
        return

    col1, col2 = st.columns(2)
    with col1:
        school_type = st.selectbox("학교 종류", ["전체"] + sorted(df_schools["school_type"].dropna().unique().tolist()))
    with col2:
        filtered = df_schools if school_type == "전체" else df_schools[df_schools["school_type"] == school_type]
        school_name = st.selectbox("부대 선택", sorted(filtered["school_name"].dropna().tolist()))

    school_code = df_schools[df_schools["school_name"] == school_name]["school_code"].values[0]

    with st.spinner(f"{school_name} 데이터 불러오는 중..."):
        df_meals = load_school_meals(school_code)
        df_classified = load_classified()

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
