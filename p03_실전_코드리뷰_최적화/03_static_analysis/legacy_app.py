"""❌ 정적 분석 연습용 코드 — 일부러 버그·보안 문제·나쁜 패턴을 넣었습니다. 실행용이 아닙니다."""
import os
import sqlite3
import subprocess
import sys

DB_PASSWORD = "admin1234"


def get_user(conn, username):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name = '" + username + "'")
    return cur.fetchone()


def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags


def run_backup(path):
    return subprocess.call("tar czf backup.tgz " + path, shell=True)


def grade(score):
    if score >= 90:
        if score >= 95:
            return "A+"
        else:
            return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        try:
            return "F"
        except:
            pass


def load_config(path):
    f = open(path)
    data = eval(f.read())
    return data
