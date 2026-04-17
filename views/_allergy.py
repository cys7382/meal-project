import streamlit as st
import pandas as pd
from views._db_connect import get_client

ALLERGY_MAP = {"1":"난류","2":"우유","3":"메밀","4":"땅콩","5":"대두","6":"밀","7":"고등어","8":"게","9":"새우","10":"돼지고기","11":"복숭아","12":"토마토","13":"아황산류","14":"호두","15":"닭고기","16":"쇠고기","17":"오징어","18":"조개류","19":"잣"}

@st.cache_data(ttl=3600)
def load_allergy_data():
    client = get_client()
    data = client.table("meals").select("dish_name, allergy_info").neq("allergy_info", "").limit(50000).execute().data
    df = pd.DataFrame(data)
    return df[df["allergy_info"].notna() & (df["allergy_info"] != "")]

def show():
    st.title("⚠️ 알레르기 분석")
    st.caption("※ 50,000건 샘플 기준")
    with st.spinner("데이터 불러오는 중... 첫 로딩 시 1~2분 소요될 수 있습니다 ☕"):
        df = load_allergy_data()
    if df.empty:
        st.warning("알레르기 데이터가 없습니다.")
        return
    selected = st.multiselect("알레르기 식재료 선택", options=list(ALLERGY_MAP.values()), default=["난류", "우유"])
    if not selected:
        st.info("알레르기 식재료를 선택해주세요.")
        return
    selected_nums = [k for k, v in ALLERGY_MAP.items() if v in selected]
    def has_allergy(allergy_str):
        if not allergy_str:
            return False
        nums = allergy_str.replace("(","").replace(")","").split(".")
        return any(n.strip() in selected_nums for n in nums)
    filtered = df[df["allergy_info"].apply(has_allergy)]
    filtered = df[df["allergy_info"].apply(has_allergy)]
    result = filtered["dish_name"].drop_duplicates().reset_index(drop=True)
    st.subheader(f"'{', '.join(selected)}' 포함 메뉴 ({len(result)}개)")
    st.dataframe(result.rename("메뉴명"), use_container_width=True, height=500)
