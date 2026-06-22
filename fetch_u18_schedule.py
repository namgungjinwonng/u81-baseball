# -*- coding: utf-8 -*-
"""U-18(18세 이하부) 시즌 전체 경기 일정/결과 수집기.

calendar 페이지에서 월별 game_idx를 모은 뒤, box_score 페이지에서
날짜·시간·구장·양팀·점수·승패를 가져온다. 현재 연도를 자동 인식한다.
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
import sys
import concurrent.futures
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

sys.stdout.reconfigure(encoding='utf-8')

BASE = "https://www.korea-baseball.com"
CAL_URL = f"{BASE}/game/calendar"
BOX_URL = f"{BASE}/game/box_score"
KIND_CD = 31  # 18세 이하부

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}
session = requests.Session()
session.headers.update(HEADERS)


def collect_game_idxs(year, months):
    """월별 calendar에서 모든 game_idx 수집 (중복 제거)."""
    idxs = set()
    for m in months:
        try:
            r = session.get(CAL_URL, params={"month": m, "year": year, "kind_cd": KIND_CD}, timeout=20)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            found = 0
            for a in soup.select("a[href*='box_score']"):
                href = a.get("href", "")
                if "game_idx=" in href:
                    gid = href.split("game_idx=")[1].split("&")[0]
                    if gid.isdigit():
                        idxs.add(gid)
                        found += 1
            print(f"  {year}.{m:02d}월: game_idx {found}개")
            time.sleep(0.2)
        except Exception as e:
            print(f"  {year}.{m:02d}월 수집 실패: {e}")
    return sorted(idxs, key=int)


def parse_box_score(game_idx):
    """box_score 한 경기 파싱."""
    try:
        r = session.get(BOX_URL, params={"game_idx": game_idx}, timeout=20)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        # 날짜/시간/구장/라운드: "2026.05.02 09:30 / 목동야구장 / 예선전"
        date = time_ = venue = rnd = ""
        for dd in soup.find_all("dd"):
            t = dd.get_text(" ", strip=True)
            mdate = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", t)
            if mdate:
                date = f"{mdate.group(1)}-{int(mdate.group(2)):02d}-{int(mdate.group(3)):02d}"
                mtime = re.search(r"(\d{1,2}:\d{2})", t)
                time_ = mtime.group(1) if mtime else ""
                parts = [p.strip() for p in t.split("/")]
                if len(parts) >= 2:
                    venue = parts[1].strip()
                if len(parts) >= 3:
                    rnd = parts[2].strip()
                break

        # 양팀: .team 첫 2개가 "팀명 승/패 점수"
        teams = soup.select(".team")
        parsed = []
        for tel in teams[:2]:
            txt = tel.get_text(" ", strip=True)
            # "군산상일고 패 8" / "강릉고 승 9" / 예정이면 점수 없음
            m = re.match(r"^(.*?)\s*(승|패|무)?\s*(\d+)?$", txt)
            if m:
                name = m.group(1).strip()
                result = m.group(2) or ""
                score = m.group(3)
                parsed.append({"name": name, "result": result,
                               "score": int(score) if score is not None else None})
        if len(parsed) < 2:
            return None

        # 취소 여부: [경기취소] 등 빨간 라벨
        cancelled = False
        for dt in soup.find_all("dt", class_="font_red"):
            if "취소" in dt.get_text():
                cancelled = True
                break

        if cancelled:
            status = "취소"
        elif parsed[0]["score"] is not None and parsed[1]["score"] is not None:
            status = "완료"
        else:
            status = "예정"

        return {
            "game_idx": game_idx,
            "date": date,
            "time": time_,
            "venue": venue,
            "round": rnd,
            "status": status,
            "away": parsed[0],   # calendar 표기 첫 팀
            "home": parsed[1],   # 두 번째 팀
        }
    except Exception as e:
        print(f"    box_score {game_idx} 실패: {e}")
        return None


def main():
    year = datetime.now(KST).year
    months = list(range(1, 13))
    print(f"=== U-18 {year}시즌 일정/결과 수집 ===\n")
    print(f"[1/2] {year}년 월별 game_idx 수집 중...")
    idxs = collect_game_idxs(year, months)
    print(f"  총 {len(idxs)}경기 발견\n")

    print(f"[2/2] 경기 상세 수집 중... (구장/시간 포함)")
    total = len(idxs)
    games_by_idx = {}

    def collect_pass(idx_list, workers):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(parse_box_score, gid): gid for gid in idx_list}
            done = 0
            for fut in concurrent.futures.as_completed(futs):
                done += 1
                g = fut.result()
                if g:
                    games_by_idx[g["game_idx"]] = g
                if done % 50 == 0:
                    print(f"  {len(games_by_idx)}/{total} ...")

    # 1차 수집
    collect_pass(idxs, 12)

    # 누락분 재시도 (일시적 타임아웃 방지)
    for attempt in range(1, 11):
        missing = [g for g in idxs if g not in games_by_idx]
        if not missing:
            break
        print(f"  [재시도 {attempt}] 누락 {len(missing)}건 다시 수집...")
        time.sleep(5)
        collect_pass(missing, 4)

    missing = [g for g in idxs if g not in games_by_idx]
    if missing:
        print(f"  [경고] 최종 누락 {len(missing)}건: {missing[:20]}")

    games = list(games_by_idx.values())
    games.sort(key=lambda g: (g["date"] or "9999", g["time"] or ""))

    out = {
        "year": year,
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "games": games,
    }
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "u18_schedule.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    done_cnt = sum(1 for g in games if g["status"] == "완료")
    print(f"\n=== 완료 ===")
    print(f"연도: {year}")
    print(f"총 경기: {len(games)} (완료 {done_cnt} / 예정 {len(games)-done_cnt})")
    print(f"저장: {path}")


if __name__ == "__main__":
    main()
