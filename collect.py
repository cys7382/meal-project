# collect.py
import requests
import time
from datetime import datetime
from tqdm import tqdm
from config import NEIS_API_KEY, SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ATPT_CODE = "B10"  # 서울
TARGET_YEAR = "2024"
BASE_URL = "https://open.neis.go.kr/hub"

# ─────────────────────────────────────────
# 1. 학교 목록 수집
# ─────────────────────────────────────────
def fetch_schools():
    print("\n[1/4] 서울 학교 목록 수집 중...")
    schools = []
    page = 1

    while True:
        params = {
            "KEY": NEIS_API_KEY,
            "Type": "json",
            "pIndex": page,
            "pSize": 1000,
            "ATPT_OFCDC_SC_CODE": ATPT_CODE
        }
        res = requests.get(f"{BASE_URL}/schoolInfo", params=params)
        data = res.json()

        if "schoolInfo" not in data:
            break

        rows = data["schoolInfo"][1]["row"]
        schools.extend(rows)

        if len(rows) < 1000:
            break
        page += 1

    print(f"  → 학교 {len(schools)}개 수집 완료")
    return schools


def save_schools(schools):
    print("[1/4] 학교 정보 DB 저장 중...")
    records = []
    for s in schools:
        records.append({
            "school_code": s.get("SD_SCHUL_CODE"),
            "school_name": s.get("SCHUL_NM"),
            "school_type": s.get("SCHUL_KND_SC_NM"),
            "address": s.get("ORG_RDNMA"),
            "edu_office_code": s.get("ATPT_OFCDC_SC_CODE")
        })

    # 1000개씩 나눠서 저장
    for i in range(0, len(records), 1000):
        chunk = records[i:i+1000]
        supabase.table("schools").upsert(chunk).execute()

    print(f"  → {len(records)}개 저장 완료")
    return records


# ─────────────────────────────────────────
# 2. 급식 데이터 수집 (메뉴 + 영양 + 원산지)
# ─────────────────────────────────────────
def fetch_meal_data(school_code, year=TARGET_YEAR):
    """학교 1개의 1년치 급식 데이터 수집"""
    all_meals = []
    all_nutrition = []
    all_origins = []
    page = 1

    while True:
        params = {
            "KEY": NEIS_API_KEY,
            "Type": "json",
            "pIndex": page,
            "pSize": 1000,
            "ATPT_OFCDC_SC_CODE": ATPT_CODE,
            "SD_SCHUL_CODE": school_code,
            "MLSV_YMD": year  # 연도만 넣으면 1년치 다 가져옴
        }

        try:
            res = requests.get(f"{BASE_URL}/mealServiceDietInfo", params=params, timeout=10)
            data = res.json()
        except Exception as e:
            print(f"  오류: {school_code} - {e}")
            break

        if "mealServiceDietInfo" not in data:
            break

        rows = data["mealServiceDietInfo"][1]["row"]

        for row in rows:
            date = row.get("MLSV_YMD", "")
            meal_type = row.get("MMEAL_SC_NM", "")

            # 메뉴 파싱 (줄바꿈으로 구분된 메뉴명)
            dish_raw = row.get("DDISH_NM", "")
            dishes = [d.strip() for d in dish_raw.split("<br/>") if d.strip()]

            for dish in dishes:
                # 알레르기 번호 분리 (예: "김치찌개 (1.2.3)" → 메뉴명 + 알레르기)
                if "(" in dish:
                    dish_name = dish[:dish.rfind("(")].strip()
                    allergy = dish[dish.rfind("("):].strip()
                else:
                    dish_name = dish.strip()
                    allergy = ""

                all_meals.append({
                    "school_code": school_code,
                    "meal_date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                    "meal_type": meal_type,
                    "dish_name": dish_name,
                    "allergy_info": allergy
                })

            # 영양정보 파싱
            def safe_float(val):
                try:
                    return float(str(val).replace(",", "").strip())
                except:
                    return None

            all_nutrition.append({
                "school_code": school_code,
                "meal_date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                "meal_type": meal_type,
                "calories":     safe_float(row.get("CAL_INFO")),
                "carbohydrate": safe_float(row.get("NTR_INFO", "").split("<br/>")[0].split(":")[1] if "탄수화물" in row.get("NTR_INFO","") else None),
                "protein":      safe_float(row.get("NTR_INFO", "").split("<br/>")[1].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 1 else None),
                "fat":          safe_float(row.get("NTR_INFO", "").split("<br/>")[2].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 2 else None),
                "calcium":      safe_float(row.get("NTR_INFO", "").split("<br/>")[3].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 3 else None),
                "iron":         safe_float(row.get("NTR_INFO", "").split("<br/>")[4].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 4 else None),
                "vitamin_a":    safe_float(row.get("NTR_INFO", "").split("<br/>")[5].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 5 else None),
                "vitamin_c":    safe_float(row.get("NTR_INFO", "").split("<br/>")[6].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 6 else None),
                "niacin":       safe_float(row.get("NTR_INFO", "").split("<br/>")[7].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 7 else None),
                "riboflavin":   safe_float(row.get("NTR_INFO", "").split("<br/>")[8].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 8 else None),
                "thiamine":     safe_float(row.get("NTR_INFO", "").split("<br/>")[9].split(":")[1] if row.get("NTR_INFO","").count("<br/>") >= 9 else None),
            })

            # 원산지 정보
            origin = row.get("ORPLC_INFO", "")
            if origin:
                all_origins.append({
                    "school_code": school_code,
                    "meal_date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
                    "meal_type": meal_type,
                    "origin_info": origin
                })

        if len(rows) < 1000:
            break
        page += 1

    return all_meals, all_nutrition, all_origins


def save_meal_data(meals, nutrition, origins):
    """수집한 데이터 DB에 저장"""
    chunk_size = 500

    if meals:
        for i in range(0, len(meals), chunk_size):
            supabase.table("meals").insert(meals[i:i+chunk_size]).execute()

    if nutrition:
        for i in range(0, len(nutrition), chunk_size):
            supabase.table("nutrition").insert(nutrition[i:i+chunk_size]).execute()

    if origins:
        for i in range(0, len(origins), chunk_size):
            supabase.table("origins").insert(origins[i:i+chunk_size]).execute()


# ─────────────────────────────────────────
# 3. 전체 실행
# ─────────────────────────────────────────
def run():
    # 학교 목록 수집 & 저장
    schools = fetch_schools()
    saved = save_schools(schools)

    # 각 학교 급식 데이터 수집
    print(f"\n[2/4] 급식 데이터 수집 시작 (총 {len(saved)}개 학교)...")
    print("  ※ 학교당 약 1~2초, 전체 30~60분 예상")

    failed = []

    for school in tqdm(saved, desc="수집 중"):
        code = school["school_code"]
        try:
            meals, nutrition, origins = fetch_meal_data(code)
            if meals:
                save_meal_data(meals, nutrition, origins)
            time.sleep(0.5)  # API 과부하 방지
        except Exception as e:
            failed.append(code)
            print(f"\n  실패: {code} - {e}")

    print(f"\n✅ 수집 완료!")
    print(f"  성공: {len(saved) - len(failed)}개")
    print(f"  실패: {len(failed)}개 → {failed}")


if __name__ == "__main__":
    run()