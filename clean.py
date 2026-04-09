import re
import sqlite3
from db import get_conn

NORMALIZE = {
    "된장찌게": "된장찌개",
    "김치찌게": "김치찌개",
    "부대찌게": "부대찌개",
    "제육볶음": "제육볶음",
    "떡볶기":   "떡볶이",
}

def clean_dish_name(raw: str) -> str:
    # 1. 알레르기 번호 제거: (1.2.3) 형태
    name = re.sub(r'\([\d\.]+\)', '', raw)
    # 2. 앞에 붙은 숫자+점+공백 제거: "1. " 형태
    name = re.sub(r'^\d+\.\s*', '', name)
    # 3. 앞에 붙은 숫자만 제거: "0감자" 형태
    name = re.sub(r'^\d+', '', name)
    # 4. 앞뒤 특수문자 제거
    name = re.sub(r'^[^\w가-힣]+', '', name)
    name = re.sub(r'[^\w가-힣]+$', '', name)
    # 5. 공백 정리
    name = name.strip()
    # 6. 오타 통합
    name = NORMALIZE.get(name, name)
    return name

def parse_dish_list(raw_dish_names: str) -> list:
    dishes = re.split(r'<br\s*/?>', raw_dish_names)
    cleaned = []
    for d in dishes:
        name = clean_dish_name(d)
        if name:
            cleaned.append(name)
    return cleaned

def get_unique_dishes() -> list:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT dish_names FROM raw_meals")
    rows = c.fetchall()
    conn.close()

    all_dishes = set()
    for (raw,) in rows:
        for dish in parse_dish_list(raw):
            all_dishes.add(dish)

    print(f"고유 요리 {len(all_dishes)}개 추출")
    return list(all_dishes)

if __name__ == "__main__":
    dishes = get_unique_dishes()
    for d in sorted(dishes)[:20]:
        print(d)