import streamlit as st
st.set_page_config(page_title="FoodLink", page_icon="🔗", layout="wide")

from views import _overview as overview
from views import _nutrition as nutrition
from views import _allergy as allergy
from views import _cost as cost
from views import _supply as supply
from views import _compare as compare

st.sidebar.title("🔗 FoodChain")
st.sidebar.caption("급식 식재료 수급 매칭 플랫폼")
st.sidebar.divider()

menu = st.sidebar.radio("", [
    "📦 시기별 재료 사용량",
    "🗺️ 지역별 비교",
    "📊 부대별 메뉴 분석",
    "📁 기타 분석",
])

if menu == "📦 시기별 재료 사용량":
    supply.show()
elif menu == "🗺️ 지역별 비교":
    compare.show()
elif menu == "📊 부대별 메뉴 분석":
    overview.show()
elif menu == "📁 기타 분석":
    sub = st.selectbox("분석 선택", [
        "🧪 영양성분 분석",
        "⚠️ 알레르기 분석",
        "💰 원가 분석",
    ])
    if sub == "🧪 영양성분 분석":
        nutrition.show()
    elif sub == "⚠️ 알레르기 분석":
        allergy.show()
    elif sub == "💰 원가 분석":
        cost.show()
