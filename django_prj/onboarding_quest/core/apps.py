from django.apps import AppConfig
import sqlite3
import os

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'


# init_db.py


def enable_wal_mode():
    """SQLite WAL 모드 활성화"""
    db_path = 'db.sqlite3'
    
    try:
        conn = sqlite3.connect(db_path)
        result = conn.execute('PRAGMA journal_mode=WAL;').fetchone()
        conn.close()
        
        print(f"SQLite WAL 모드 활성화 완료: {result[0]}")
    except Exception as e:
        print(f"WAL 모드 활성화 중 오류: {e}")

if __name__ == "__main__":
    enable_wal_mode()
