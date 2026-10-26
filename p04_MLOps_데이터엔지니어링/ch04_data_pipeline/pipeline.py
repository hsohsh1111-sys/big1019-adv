"""날씨 데이터 ETL 파이프라인: Open-Meteo 공개 API(무료·키 불필요) → 검증·정제 → SQLite 적재(UPSERT) → 일별 리포트.

실행:
  python pipeline.py --days 7             # 최근 7일 서울 시간별 기온·습도·강수량
  python pipeline.py --days 7 --offline   # 인터넷 없이 샘플 데이터로
  python pipeline.py --clean-only         # 실습용 오염(결측·이상치·중복) 주입 없이 원본 그대로
"""
import argparse
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = Path(__file__).parent
DB = BASE / "weather.db"
API = "https://api.open-meteo.com/v1/forecast"
CITY = {"name": "서울", "latitude": 37.5665, "longitude": 126.9780}


# ---------------------------------------------------------------- Extract
def extract(days, offline=False):
    if offline:
        hours = pd.date_range(end=datetime.now().replace(minute=0, second=0, microsecond=0), periods=days * 24, freq="h")
        rng = np.random.default_rng(0)
        return pd.DataFrame({"time": hours.strftime("%Y-%m-%dT%H:%M"),
                             "temperature_2m": 12 + 6 * np.sin((hours.hour - 9) / 24 * 2 * np.pi) + rng.normal(0, 1, len(hours)),
                             "relative_humidity_2m": rng.integers(35, 90, len(hours)),
                             "precipitation": rng.choice([0, 0, 0, 0, 0.5, 2.0], len(hours))})
    params = {"latitude": CITY["latitude"], "longitude": CITY["longitude"], "timezone": "Asia/Seoul",
              "hourly": "temperature_2m,relative_humidity_2m,precipitation", "past_days": days, "forecast_days": 1}
    res = requests.get(API, params=params, timeout=15)
    res.raise_for_status()
    df = pd.DataFrame(res.json()["hourly"])
    return df[pd.to_datetime(df["time"]) <= datetime.now()]  # 미래 예보는 제외


def inject_dirty_data(df):
    """실습용: 실제 현장 데이터처럼 결측·이상치·중복·문자열 숫자를 일부러 섞는다."""
    df = df.copy()
    df.loc[df.sample(frac=0.03, random_state=1).index, "temperature_2m"] = np.nan
    df.loc[df.sample(n=2, random_state=2).index, "temperature_2m"] = 85.0  # 센서 오류
    df["relative_humidity_2m"] = df["relative_humidity_2m"].astype(object)
    df.loc[df.sample(n=3, random_state=3).index, "relative_humidity_2m"] = "N/A"
    return pd.concat([df, df.sample(n=5, random_state=4)])  # 중복 행


# ---------------------------------------------------------------- Transform
def transform(raw):
    report = {"입력 행": len(raw)}
    df = raw.rename(columns={"temperature_2m": "temp_c", "relative_humidity_2m": "humidity", "precipitation": "rain_mm"})
    df["time"] = pd.to_datetime(df["time"])
    df = df.drop_duplicates(subset="time").sort_values("time")
    report["중복 제거 후"] = len(df)

    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")  # "N/A" → NaN
    outliers = ~df["temp_c"].between(-40, 50) & df["temp_c"].notna()
    report["기온 이상치"] = int(outliers.sum())
    df.loc[outliers, "temp_c"] = np.nan
    report["결측치(보간 전)"] = int(df[["temp_c", "humidity"]].isna().sum().sum())
    df[["temp_c", "humidity"]] = df[["temp_c", "humidity"]].interpolate(limit_direction="both")
    df["rain_mm"] = df["rain_mm"].fillna(0)

    df["date"] = df["time"].dt.date.astype(str)  # 파생 변수
    df["hour"] = df["time"].dt.hour
    df["is_weekend"] = df["time"].dt.dayofweek >= 5
    df["time"] = df["time"].dt.strftime("%Y-%m-%d %H:%M")
    return df, report


def validate(df):
    errors = []
    if df.empty:
        errors.append("데이터가 없습니다")
    if not df["time"].is_unique:
        errors.append("시각 중복")
    if df[["temp_c", "humidity"]].isna().any().any():
        errors.append("결측치 남음")
    if not df["temp_c"].between(-40, 50).all():
        errors.append("기온 범위 이상")
    if errors:
        raise ValueError("데이터 품질 검증 실패: " + ", ".join(errors))


# ---------------------------------------------------------------- Load
def load(df):
    with closing(sqlite3.connect(DB)) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS weather_hourly (
            time TEXT PRIMARY KEY, city TEXT, temp_c REAL, humidity REAL, rain_mm REAL,
            date TEXT, hour INTEGER, is_weekend INTEGER, loaded_at TEXT)""")
        rows = [(r.time, CITY["name"], r.temp_c, r.humidity, r.rain_mm, r.date, r.hour, int(r.is_weekend),
                 datetime.now().isoformat(timespec="seconds")) for r in df.itertuples()]
        # UPSERT: 같은 시각이 이미 있으면 덮어쓰기 → 몇 번을 다시 실행해도 중복 없음(멱등성)
        conn.executemany("""INSERT INTO weather_hourly VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(time) DO UPDATE SET temp_c=excluded.temp_c, humidity=excluded.humidity,
            rain_mm=excluded.rain_mm, loaded_at=excluded.loaded_at""", rows)
        conn.commit()
        return conn.execute("SELECT COUNT(*) FROM weather_hourly").fetchone()[0]


def daily_report():
    with closing(sqlite3.connect(DB)) as conn:
        return pd.read_sql("""SELECT date AS 날짜, ROUND(MIN(temp_c),1) AS 최저기온, ROUND(MAX(temp_c),1) AS 최고기온,
            ROUND(AVG(temp_c),1) AS 평균기온, ROUND(AVG(humidity)) AS 평균습도, ROUND(SUM(rain_mm),1) AS 강수량
            FROM weather_hourly GROUP BY date ORDER BY date""", conn)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--clean-only", action="store_true")
    args = parser.parse_args()

    start = datetime.now()
    try:
        raw = extract(args.days, args.offline)
        source = "샘플(오프라인)" if args.offline else "Open-Meteo API"
    except requests.RequestException as e:
        print(f"API 호출 실패({e}) → 샘플 데이터로 대체")
        raw, source = extract(args.days, offline=True), "샘플(API 실패 대체)"
    print(f"[Extract]   {source}: {len(raw)}행")
    if not args.clean_only:
        raw = inject_dirty_data(raw)

    df, report = transform(raw)
    print("[Transform] " + " / ".join(f"{k} {v}" for k, v in report.items()))
    validate(df)
    print("[Validate]  통과")
    total = load(df)
    print(f"[Load]      {len(df)}행 적재 → {DB.name} (테이블 누적 {total}행)")

    out = daily_report()
    out.to_csv(BASE / "daily_report.csv", index=False, encoding="utf-8-sig")
    print(f"\n{CITY['name']} 일별 날씨 리포트 (소요 {(datetime.now() - start) / timedelta(seconds=1):.1f}초)")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
