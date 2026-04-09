import requests
import time
from datetime import datetime
from tqdm import tqdm
from config import NEIS_API_KEY, SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
ATPT_CODE = "C10"  # 부산
TARGET_YEAR = "2024"
BASE_URL = "https://open.neis.go.kr/hub"

def fetch_schools():
    schools = []
    page = 1
    while True:
        params = {"KEY": NEIS_API_KEY, "Type": "json", "pIndex": page, "pSize": 1000, "ATPT_OFCDC_SC_CODE": ATPT_CODE}
        res = requests.get(f"{BASE_URL}/schoolInfo", params=params)
        data = res.json()
        if "schoolInfo" not in data:
            break
        rows = data["schoolInfo"][1]["row"]
        schools.extend(rows)
        if len(rows) < 1000:
            break
        page += 1
    return schools

def save_schools(schools):
    records = [{"school_code": s.get("SD_SCHUL_CODE"), "school_name": s.get("SCHUL_NM"), "school_type": s.get("SCHUL_KND_SC_NM"), "address": s.get("ORG_RDNMA"), "edu_office_code": s.get("ATPT_OFCDC_SC_CODE")} for s in schools]
    for i in range(0, len(records), 1000):
        supabase.table("schools").upsert(records[i:i+1000], on_conflict="school_code", ignore_duplicates=True).execute()
    return records

def fetch_meal_data(school_code):
    all_meals, all_nutrition, all_origins = [], [], []
    page = 1
    while True:
        params = {"KEY": NEIS_API_KEY, "Type": "json", "pIndex": page, "pSize": 1000, "ATPT_OFCDC_SC_CODE": ATPT_CODE, "SD_SCHUL_CODE": school_code, "MLSV_YMD": TARGET_YEAR}
        try:
            res = requests.get(f"{BASE_URL}/mealServiceDietInfo", params=params, timeout=10)
            data = res.json()
        except:
            break
        if "mealServiceDietInfo" not in data:
            break
        rows = data["mealServiceDietInfo"][1]["row"]
        for row in rows:
            date = row.get("MLSV_YMD", "")
            meal_type = row.get("MMEAL_SC_NM", "")
            dish_raw = row.get("DDISH_NM", "")
            dishes = [d.strip() for d in dish_raw.split("<br/>") if d.strip()]
            for dish in dishes:
                if "(" in dish:
                    dish_name = dish[:dish.rfind("(")].strip()
                    allergy = dish[dish.rfind("("):].strip()
                else:
                    dish_name = dish.strip()
                    allergy = ""
                all_meals.append({"school_code": school_code, "meal_date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "meal_type": meal_type, "dish_name": dish_name, "allergy_info": allergy})
            def safe_float(val):
                try:
                    return float(str(val).replace(",", "").strip())
                except:
                    return None
            ntr = row.get("NTR_INFO", "")
            ntr_parts = ntr.split("<br/>")
            def get_ntr(idx):
                try:
                    return safe_float(ntr_parts[idx].split(":")[1])
                except:
                    return None
            all_nutrition.append({"school_code": school_code, "meal_date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "meal_type": meal_type, "calories": safe_float(row.get("CAL_INFO")), "carbohydrate": get_ntr(0), "protein": get_ntr(1), "fat": get_ntr(2), "calcium": get_ntr(3), "iron": get_ntr(4), "vitamin_a": get_ntr(5), "vitamin_c": get_ntr(6), "niacin": get_ntr(7), "riboflavin": get_ntr(8), "thiamine": get_ntr(9)})
            origin = row.get("ORPLC_INFO", "")
            if origin:
                all_origins.append({"school_code": school_code, "meal_date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "meal_type": meal_type, "origin_info": origin})
        if len(rows) < 1000:
            break
        page += 1
    return all_meals, all_nutrition, all_origins

def save_meal_data(meals, nutrition, origins):
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

def run():
    print("부산 학교 수집 중...")
    schools = fetch_schools()
    saved = save_schools(schools)
    print(f"부산 학교 {len(saved)}개 저장 완료")
    failed = []
    for school in tqdm(saved, desc="급식 수집 중"):
        code = school["school_code"]
        try:
            meals, nutrition, origins = fetch_meal_data(code)
            if meals:
                save_meal_data(meals, nutrition, origins)
            time.sleep(0.3)
        except Exception as e:
            failed.append(code)
    print(f"완료! 성공: {len(saved)-len(failed)}개 / 실패: {len(failed)}개")

if __name__ == "__main__":
    run()