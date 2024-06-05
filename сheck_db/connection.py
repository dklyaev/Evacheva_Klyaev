from fastapi import FastAPI, Response, status
import psycopg2
import os
from contextlib import contextmanager
from typing import Generator

app = FastAPI()

@contextmanager
def get_database_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    try:
        conn = psycopg2.connect(
            dbname=os.environ['POSTGRES_DB'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            port=5432,
            host=os.environ['POSTGRES_HOST']
        )
        yield conn
    finally:
        conn.close()

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(response: Response):
    try:
        with get_database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                conn.commit()
        response.headers["X-Database-Status"] = "Alive"
    except psycopg2.OperationalError:
        response.headers["X-Database-Status"] = "Dead"
    return {}