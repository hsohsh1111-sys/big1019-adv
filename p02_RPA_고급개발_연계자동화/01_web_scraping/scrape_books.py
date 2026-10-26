"""연습용 서점 사이트(books.toscrape.com)에서 책 정보를 수집해 CSV·엑셀로 저장.

실행: python scrape_books.py --pages 3
- requests로 HTML 다운로드 → BeautifulSoup CSS 선택자로 추출
- 요청 간격(delay)과 재시도(retry)로 서버 배려 + 안정성 확보
"""
import argparse
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://books.toscrape.com/catalogue/"
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
HEADERS = {"User-Agent": "Mozilla/5.0 (edu-scraping-practice)"}
OUT = Path(__file__).parent / "output"


def fetch(url, retries=3, delay=1.0):
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            res.encoding = "utf-8"
            return res.text
        except requests.RequestException as e:
            print(f"  ! {url} 실패 ({attempt}/{retries}): {e}")
            time.sleep(delay * attempt)
    raise RuntimeError(f"{url} 수집 실패")


def parse_page(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        yield {
            "제목": link["title"],
            "가격(£)": float(card.select_one("p.price_color").text.strip().lstrip("£Â")),
            "평점": RATING.get(card.select_one("p.star-rating")["class"][1], 0),
            "재고": card.select_one("p.availability").text.strip(),
            "링크": urljoin(page_url, link["href"]),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=2, help="수집할 페이지 수 (1페이지 = 20권)")
    parser.add_argument("--delay", type=float, default=1.0, help="요청 간격(초)")
    args = parser.parse_args()

    books = []
    for page in range(1, args.pages + 1):
        url = urljoin(BASE, f"page-{page}.html")
        print(f"[{page}/{args.pages}] {url}")
        books.extend(parse_page(fetch(url), url))
        time.sleep(args.delay)  # 서버에 부담을 주지 않도록 간격 두기

    df = pd.DataFrame(books)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "books.csv", index=False, encoding="utf-8-sig")  # utf-8-sig: 엑셀에서 한글 깨짐 방지
    with pd.ExcelWriter(OUT / "books.xlsx") as writer:
        df.to_excel(writer, sheet_name="전체", index=False)
        stats = df.groupby("평점").agg(권수=("제목", "count"), 평균가격=("가격(£)", "mean")).round(2)
        stats.to_excel(writer, sheet_name="평점별")

    print(f"\n총 {len(df)}권 수집 → {OUT / 'books.xlsx'}")
    top = df.sort_values(["평점", "가격(£)"], ascending=[False, True]).head(5)
    print(top[["제목", "가격(£)", "평점"]].to_string(index=False))


if __name__ == "__main__":
    main()
