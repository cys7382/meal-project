import streamlit as st
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=3600)
def query(table, columns="*", filters=None, limit=None):
    client = get_client()
    q = client.table(table).select(columns)
    if filters:
        for col, val in filters.items():
            q = q.eq(col, val)
    if limit:
        q = q.limit(limit)
    return q.execute().data

@st.cache_data(ttl=3600)
def query_all(table, columns="*", filters=None):
    client = get_client()
    all_data = []
    page = 0
    while True:
        q = client.table(table).select(columns)
        if filters:
            for col, val in filters.items():
                q = q.eq(col, val)
        q = q.range(page * 1000, (page + 1) * 1000 - 1)
        res = q.execute().data
        all_data.extend(res)
        if len(res) < 1000:
            break
        page += 1
    return all_data