# db.py
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_tables():
    """Supabase에 테이블 생성 (SQL 직접 실행)"""
    print("Supabase 대시보드에서 아래 SQL을 실행해주세요.")
    print("=" * 60)
    sql = """
-- 학교 정보 테이블
CREATE TABLE IF NOT EXISTS schools (
    school_code TEXT PRIMARY KEY,
    school_name TEXT,
    school_type TEXT,
    address TEXT,
    edu_office_code TEXT
);

-- 급식 메뉴 테이블
CREATE TABLE IF NOT EXISTS meals (
    id BIGSERIAL PRIMARY KEY,
    school_code TEXT,
    meal_date DATE,
    meal_type TEXT,
    dish_name TEXT,
    allergy_info TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 영양정보 테이블
CREATE TABLE IF NOT EXISTS nutrition (
    id BIGSERIAL PRIMARY KEY,
    school_code TEXT,
    meal_date DATE,
    meal_type TEXT,
    calories FLOAT,
    carbohydrate FLOAT,
    protein FLOAT,
    fat FLOAT,
    calcium FLOAT,
    iron FLOAT,
    vitamin_a FLOAT,
    vitamin_c FLOAT,
    niacin FLOAT,
    riboflavin FLOAT,
    thiamine FLOAT
);

-- 원산지 정보 테이블
CREATE TABLE IF NOT EXISTS origins (
    id BIGSERIAL PRIMARY KEY,
    school_code TEXT,
    meal_date DATE,
    meal_type TEXT,
    origin_info TEXT
);

-- Claude 분류 결과 테이블 (나중에 사용)
CREATE TABLE IF NOT EXISTS dish_classification (
    id BIGSERIAL PRIMARY KEY,
    dish_name_raw TEXT UNIQUE,
    dish_name_clean TEXT,
    category TEXT,
    ingredients TEXT,
    cooking_method TEXT,
    cost_estimate FLOAT,
    classified_at TIMESTAMPTZ DEFAULT NOW()
);
    """
    print(sql)
    print("=" * 60)

if __name__ == "__main__":
    init_tables()