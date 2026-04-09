# classify.py
import anthropic
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from config import CLAUDE_API_KEY, SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """너는 학교 급식 메뉴 분류 전문가야.
메뉴명 목록을 받으면 각각에 대해 아래 JSON 형식으로만 응답해.
다른 말은 절대 하지 말고 JSON 배열만 반환해.

응답 형식:
[
  {
    "dish_name_raw": "원본메뉴명",
    "dish_name_clean": "정제된메뉴명 (오타수정, 특수문자제거, 표기통일)",
    "category": "아래 카테고리 중 하나",
    "is_special": true or false,
    "ingredients_detail": [
      {"name": "재료명", "amount": "양(g 또는 ml 또는 개)", "unit_price": 도매가1g당원가숫자}
    ],
    "cooking_method": "조리법",
    "cost_estimate": 원가숫자(원단위정수)
  }
]

카테고리 목록 (반드시 아래 중 하나만 선택):
- 밥
- 죽
- 빵
- 면
- 국·탕·찌개
- 주반찬
- 부반찬
- 샐러드·무침
- 김치·절임
- 후식·간식
- 음료·유제품
- 소스·양념

is_special: 특식(생일, 명절, 행사 등 특별한 날 메뉴)이면 true

ingredients_detail 작성 기준:
- 1인분 기준 실제 사용량으로 작성
- 고체 재료는 g, 액체는 ml, 달걀/두부 등은 개/모
- unit_price는 식재료 도매가 기준 1g(ml)당 원가
- 예시: 된장찌개 → [
    {"name": "된장", "amount": "15g", "unit_price": 3},
    {"name": "두부", "amount": "80g", "unit_price": 2},
    {"name": "감자", "amount": "50g", "unit_price": 1},
    {"name": "양파", "amount": "30g", "unit_price": 1},
    {"name": "대파", "amount": "10g", "unit_price": 2}
  ]

cost_estimate: ingredients_detail의 (amount × unit_price) 합산값
"""

# ─────────────────────────────────────────
# 1. 분류할 고유 메뉴명 가져오기
# ─────────────────────────────────────────
def get_unique_dishes():
    print("\n[1/3] 고유 메뉴명 추출 중...")
    all_dishes = set()
    page = 0
    page_size = 1000

    while True:
        res = supabase.table("meals")\
            .select("dish_name")\
            .range(page * page_size, (page + 1) * page_size - 1)\
            .execute()
        if not res.data:
            break
        for row in res.data:
            if row["dish_name"]:
                all_dishes.add(row["dish_name"].strip())
        if len(res.data) < page_size:
            break
        page += 1

    classified_res = supabase.table("dish_classification")\
        .select("dish_name_raw")\
        .execute()
    already_done = {r["dish_name_raw"] for r in classified_res.data}
    todo = list(all_dishes - already_done)

    print(f"  → 전체 고유 메뉴: {len(all_dishes)}개")
    print(f"  → 이미 분류됨: {len(already_done)}개")
    print(f"  → 분류 필요: {len(todo)}개")
    return todo


# ─────────────────────────────────────────
# 2. 배치 1개 분류
# ─────────────────────────────────────────
def classify_batch(dishes):
    dish_list = "\n".join([f"- {d}" for d in dishes])
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": f"아래 메뉴들을 분류해줘:\n{dish_list}"}],
        system=SYSTEM_PROMPT
    )
    response_text = message.content[0].text.strip()
    if "```" in response_text:
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    return json.loads(response_text)


def save_classifications(results):
    records = [{
        "dish_name_raw": r.get("dish_name_raw"),
        "dish_name_clean": r.get("dish_name_clean"),
        "category": r.get("category"),
        "ingredients_detail": json.dumps(r.get("ingredients_detail"), ensure_ascii=False) if r.get("ingredients_detail") else None,
        "cooking_method": r.get("cooking_method"),
        "cost_estimate": r.get("cost_estimate"),
    } for r in results]
    supabase.table("dish_classification").upsert(records).execute()


# ─────────────────────────────────────────
# 3. 병렬 처리 (20개 동시)
# ─────────────────────────────────────────
def process_batch(batch):
    try:
        results = classify_batch(batch)
        save_classifications(results)
        return len(results), None
    except Exception as e:
        return 0, str(e)


def run():
    todo = get_unique_dishes()
    if not todo:
        print("분류할 메뉴가 없어요!")
        return

    batch_size = 20
    batches = [todo[i:i+batch_size] for i in range(0, len(todo), batch_size)]
    total = len(batches)

    print(f"\n[2/3] Claude API 분류 시작 (총 {total}배치, 병렬 20개)...")
    print(f"  예상 시간: 약 {total // 20 * 25 // 60}분\n")

    success = 0
    failed_batches = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_batch, batch): batch for batch in batches}
        with tqdm(total=total, desc="분류 중") as pbar:
            for future in as_completed(futures):
                count, error = future.result()
                if error:
                    failed_batches.append(futures[future])
                else:
                    success += count
                pbar.update(1)

    if failed_batches:
        print(f"\n실패 배치 {len(failed_batches)}개 재시도 중...")
        for batch in tqdm(failed_batches, desc="재시도"):
            try:
                results = classify_batch(batch)
                save_classifications(results)
            except Exception as e:
                print(f"  재시도 실패: {e}")
            time.sleep(1)

    print(f"\n✅ 분류 완료! 성공: {success}개")


if __name__ == "__main__":
    run()