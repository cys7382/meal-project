# test_collect.py
from collect import fetch_schools, save_schools, fetch_meal_data, save_meal_data

print("=== 테스트 모드: 학교 3개만 수집 ===")

schools = fetch_schools()
saved = save_schools(schools)

# 앞에서 3개만 테스트
test_schools = saved[:3]

for school in test_schools:
    code = school["school_code"]
    name = school["school_name"]
    print(f"\n수집 중: {name} ({code})")
    meals, nutrition, origins = fetch_meal_data(code)
    print(f"  메뉴: {len(meals)}건 / 영양: {len(nutrition)}건 / 원산지: {len(origins)}건")
    save_meal_data(meals, nutrition, origins)
    print(f"  → 저장 완료")

print("\n✅ 테스트 완료! Supabase에서 데이터 확인해보세요.")