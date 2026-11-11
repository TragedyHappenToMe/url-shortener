from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import psycopg2
import os
import random
import string

app = FastAPI()

# Koneksi ke database
def get_db():
    conn = psycopg2.connect(
    host = os.getenv("DB-HOST", "db"),
    database = os.getenv("DB_NAME", "shortener"),
    user = os.getenv("DB_USER", "user"),
    password = os.getenv("DB_PASSWORD", "password")
    )
    return conn

# Buat tabel kalau belum ada
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS urls (
    short_code VARCHAR(10) PRIMARY KEY,
    original_url TEXT NOT NULL
    )
    """)
    conn.commit()
    cur.close()
    conn.close()
    
# Jalanakan init saat app start
@app.on_event("startup")
def startup():
    init_db()

# Generate random short code
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Model request
class URLRequest(BaseModel):
    url:str
    
# Endpoint 1: Shorten URL
@app.post("/shorten")
def shorten_url(request: URLRequest):
    code = generate_code()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO urls (short_code, original_url) VALUES (%s, %s)", (code, request.url))
    conn.commit()
    cur.close()
    conn.close()
    return {"short_code": code, "short_url": f"http://localhost:8000/{code}"}

# Endpoint 2: redirect
@app.get("/{short_code}")
def redirect_url(short_code: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT original_url FROM urls WHERE short_code = %s", (short_code,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="URL tidak ditemukan")
    return RedirectResponse(url=result[0])

