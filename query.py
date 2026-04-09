from db import get_conn

def query_by_ingredient(ingredient_name: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT d.name_clean, d.category, d.season
        FROM dishes d
        JOIN dish_ingredients di ON d.id = di.dish_id
        JOIN ingredients i ON di.ingredient_id = i.id
        WHERE i.name LIKE ?
    """, (f"%{ingredient_name}%",))
    rows = c.fetchall()
    conn.close()

    print(f"\n[{ingredient_name}] 이 들어간 요리:")
    for name, cat, season in rows:
        print(f"  - {name} ({cat}) | 계절: {season}")

def query_by_season(season: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT name_clean, category, season
        FROM dishes
        WHERE season LIKE ?
        ORDER BY category
    """, (f"%{season}%",))
    rows = c.fetchall()
    conn.close()

    print(f"\n[{season}] 제철 메뉴:")
    for name, cat, season in rows:
        print(f"  - {name} ({cat})")

def query_top_ingredients(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT i.name, i.category, COUNT(*) as cnt
        FROM ingredients i
        JOIN dish_ingredients di ON i.id = di.ingredient_id
        GROUP BY i.id
        ORDER BY cnt DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()

    print(f"\n자주 쓰이는 식자재 Top {limit}:")
    for name, cat, cnt in rows:
        print(f"  {cnt:3d}회 | {name} ({cat})")

if __name__ == "__main__":
    query_by_ingredient("감자")
    query_by_season("봄")
    query_top_ingredients()