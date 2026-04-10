from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import time

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

SEASON_MAP = {1:"winter",2:"winter",3:"spring",4:"spring",5:"spring",
              6:"summer",7:"summer",8:"summer",9:"fall",10:"fall",11:"fall",12:"winter"}

print("데이터 불러오는 중...")
all_meals = []
page = 0
while True:
    try:
        res = supabase.table("meals").select("dish_name, meal_date").range(page*1000, (page+1)*1000-1).execute().data
        all_meals.extend(res)
        if len(res) < 1000:
            break
        page += 1
        if page % 100 == 0:
            print(f"{len(all_meals):,}건 불러옴...")
    except Exception as e:
        print(f"페이지 {page} 실패, 2초 후 재시도...")
        time.sleep(2)
        continue

print(f"총 {len(all_meals):,}건 완료. 집계 중...")

stats = {}
for row in all_meals:
    name = row["dish_name"]
    date = row["meal_date"]
    if not name or not date:
        continue
    month = int(date[5:7])
    season = SEASON_MAP.get(month, "spring")
    if name not in stats:
        stats[name] = {"dish_name": name, "count": 0, "spring_count": 0, "summer_count": 0, "fall_count": 0, "winter_count": 0}
    stats[name]["count"] += 1
    stats[name][f"{season}_count"] += 1

records = list(stats.values())
print(f"총 {len(records):,}개 메뉴. Supabase 저장 중...")

for i in range(0, len(records), 500):
    try:
        supabase.table("menu_stats").upsert(records[i:i+500]).execute()
        print(f"{min(i+500, len(records)):,}/{len(records):,} 저장 완료")
    except Exception as e:
        print(f"저장 실패, 재시도 중... {e}")
        time.sleep(2)
        supabase.table("menu_stats").upsert(records[i:i+500]).execute()

print("완료!")