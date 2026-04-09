from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import json
from datetime import datetime, timedelta

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_week_number(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return date.isocalendar()[1]

def load_all_meals():
    print("급식 데이터 불러오는 중...")
    all_data = []
    page = 0
    while True:
        res = supabase.table("meals").select("school_code, dish_name, meal_date").range(page*1000, (page+1)*1000-1).execute()
        all_data.extend(res.data)
        if len(res.data) < 1000:
            break
        page += 1
        if page % 100 == 0:
            print(f"{len(all_data):,}건 불러옴...")
    print(f"총 {len(all_data):,}건 완료")
    return all_data

def load_ingredients():
    print("재료 데이터 불러오는 중...")
    all_data = []
    page = 0
    while True:
        res = supabase.table("dish_classification").select("dish_name_raw, ingredients_detail").not_.is_("ingredients_detail", "null").range(page*1000, (page+1)*1000-1).execute()
        all_data.extend(res.data)
        if len(res.data) < 1000:
            break
        page += 1
    print(f"재료 있는 메뉴 {len(all_data):,}개 완료")
    return {r["dish_name_raw"]: r["ingredients_detail"] for r in all_data}

def load_schools():
    res = supabase.table("schools").select("school_code, school_name, school_type, edu_office_code").execute()
    return {r["school_code"]: r for r in res.data}

def run():
    meals = load_all_meals()
    ingredients = load_ingredients()
    schools = load_schools()

    print("주간 수요 계산 중...")
    # week -> ingredient -> {amount, school_count, school_codes}
    weekly = {}

    for meal in meals:
        dish = meal["dish_name"]
        date = meal["meal_date"]
        school_code = meal["school_code"]

        if not date or dish not in ingredients:
            continue

        week = get_week_number(date)
        ing_raw = ingredients[dish]

        try:
            ing_list = json.loads(ing_raw) if isinstance(ing_raw, str) else ing_raw
        except:
            continue

        if week not in weekly:
            weekly[week] = {}

        for ing in ing_list:
            name = ing.get("name", "")
            amount_str = ing.get("amount", "0")
            if not name:
                continue
            try:
                amount = float(str(amount_str).replace("g", "").replace("ml", "").strip())
            except:
                continue

            if name not in weekly[week]:
                weekly[week][name] = {"total_amount": 0, "serving_count": 0}

            weekly[week][name]["total_amount"] += amount
            weekly[week][name]["serving_count"] += 1

    # Supabase에 저장
    print("Supabase 저장 중...")
    
    # supply_stats 테이블 필요 — SQL로 먼저 만들어야 함
    records = []
    for week, ings in weekly.items():
        for ing_name, data in ings.items():
            records.append({
                "week_number": week,
                "ingredient_name": ing_name,
                "total_amount_g": round(data["total_amount"], 2),
                "serving_count": data["serving_count"],
                "region": "서울"
            })

    for i in range(0, len(records), 500):
        supabase.table("supply_stats").upsert(records[i:i+500]).execute()
        print(f"{min(i+500, len(records)):,}/{len(records):,} 저장 완료")

    print(f"\n완료! 총 {len(records):,}개 주간 수요 데이터 저장")

if __name__ == "__main__":
    run()