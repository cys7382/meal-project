import streamlit as st
st.set_page_config(page_title="학교급식 분석 대시보드", page_icon="🍱", layout="wide")
from views import _overview as overview
from views import _school as school
from views import _menu_analysis as menu_analysis
from views import _nutrition as nutrition
from views import _allergy as allergy
from views import _cost as cost

st.sidebar.title("🍱 학교급식 분석")
menu = st.sidebar.radio("메뉴 선택", ["📊 전체 통계", "🏫 학교별 분석", "🥗 메뉴 분석", "🧪 영양성분 분석", "⚠️ 알레르기 분석", "💰 원가 분석"])

if menu == "📊 전체 통계":
    overview.show()
elif menu == "🏫 학교별 분석":
    school.show()
elif menu == "🥗 메뉴 분석":
    menu_analysis.show()
elif menu == "🧪 영양성분 분석":
    nutrition.show()
elif menu == "⚠️ 알레르기 분석":
    allergy.show()
elif menu == "💰 원가 분석":
    cost.show()