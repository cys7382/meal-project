# test_classify.py
from classify import get_unique_dishes, classify_batch, save_classifications

print("=== 테스트 모드: 메뉴 20개만 분류 ===")

todo = get_unique_dishes()
test_batch = todo[:20]

print(f"\n테스트할 메뉴 20개:")
for d in test_batch:
    print(f"  - {d}")

print("\nClaude API 호출 중...")
results = classify_batch(test_batch)
save_classifications(results)

print("\n분류 결과:")
for r in results:
    print(f"  {r['dish_name_raw']} → {r['category']} / {r['ingredients']}")

print("\n✅ 테스트 완료! Supabase dish_classification 테이블 확인해보세요.")