import anthropic
import json
import time
from supabase import create_client
from config import CLAUDE_API_KEY, SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """너는 한국 요리 전문가야.
메뉴명 목록을 받으면 각각에 대해 일반적인 레시피 기준으로 아래 JSON 형식으로만 응답해.
다른 말은 절대 하지 말고 JSON 배열만 반환해.

응답 형식:
[
  {
    "dish_name": "메뉴명",
    "ingredients_detail": [
      {"name": "재료명", "amount": 숫자, "unit": "g 또는 ml"}
    ],
    "cooking_method": "조리법 한 줄 설명"
  }
]

규칙:
- 1인분 기준
- 고체 재료는 g, 액체는 ml
- 모르는 메뉴는 비슷한 요리로 추정
- 반드시 모든 메뉴에 대해 응답
- JSON 배열만 반환, 다른 텍스트 절대 금지"""

def get_unclassified():
    all_dishes = []
    page = 0
    while True:
        res = supabase.table("dish_classification").select("dish_name_raw").lte("id", 2160).is_("ingredients_detail", "null").range(page*1000, (page+1)*1000-1).execute()
        all_dishes.extend([r["dish_name_raw"] for r in res.data if r["dish_name_raw"]])
        if len(res.data) < 1000:
            break
        page += 1
    return all_dishes

def fill_batch(dishes):
    dish_list = "\n".join([f"- {d}" for d in dishes])
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"아래 메뉴들의 재료를 알려줘:\n{dish_list}"}]
    )
    text = message.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

def save_results(results):
    for r in results:
        ingredients = json.dumps(r.get("ingredients_detail", []), ensure_ascii=False)
        cooking = r.get("cooking_method", "")
        supabase.table("dish_classification").update({
            "ingredients_detail": ingredients,
            "cooking_method": cooking
        }).eq("dish_name_raw", r["dish_name"]).execute()

def run():
    todo = get_unclassified()
    print(f"재료 없는 메뉴: {len(todo)}개")

    failed = []
    for i in range(0, len(todo), 20):
        batch = todo[i:i+20]
        try:
            results = fill_batch(batch)
            save_results(results)
            print(f"{min(i+20, len(todo))}/{len(todo)} 완료")
            time.sleep(0.5)
        except Exception as e:
            print(f"실패: {e}")
            failed.append(batch)
            time.sleep(1)

    # 실패한 것 재시도
    if failed:
        print(f"\n실패 {len(failed)}묶음 재시도 중...")
        for batch in failed:
            try:
                results = fill_batch(batch)
                save_results(results)
                print(f"재시도 성공: {batch[0]} 외 {len(batch)-1}개")
            except Exception as e:
                print(f"재시도 실패: {e}")
            time.sleep(1)

    print("\n완료!")

if __name__ == "__main__":
    run()