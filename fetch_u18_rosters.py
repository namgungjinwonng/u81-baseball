# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import json
import time
import concurrent.futures
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://www.korea-baseball.com"
TEAM_LIST_URL = f"{BASE_URL}/info/team/team_list"
TEAM_PLAYER_URL = f"{BASE_URL}/info/team/team_player"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_all_teams():
    """Fetch all U-18 teams from all pages."""
    teams = []
    for page in range(1, 5):
        print(f"  팀 목록 {page}페이지 수집 중...")
        resp = session.get(TEAM_LIST_URL, params={"kind_cd": 31, "page": page})
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        for a_tag in soup.select("a[href*='team_player?club_idx=']"):
            href = a_tag.get("href", "")
            if "club_idx=" in href:
                try:
                    club_idx = href.split("club_idx=")[1].split("&")[0]
                    team_name = a_tag.get_text(strip=True)
                    if team_name and club_idx:
                        # Parse dl/dt/dd structure
                        dl = a_tag.find_parent("dl", class_="items")
                        region = ""
                        manager = ""
                        if dl:
                            dts = dl.find_all("dt")
                            dds = dl.find_all("dd")
                            field_map = {}
                            for dt, dd in zip(dts, dds):
                                field_map[dt.get_text(strip=True)] = dd.get_text(strip=True)
                            region = field_map.get("지역", "")
                            manager = field_map.get("감독", "")
                        teams.append({
                            "club_idx": club_idx,
                            "name": team_name,
                            "region": region,
                            "manager": manager,
                        })
                except Exception as e:
                    print(f"    Error: {e}")
        time.sleep(0.3)

    print(f"  총 {len(teams)}개 팀 발견")
    return teams


def _clean_text(text):
    """Collapse whitespace."""
    return re.sub(r'\s+', ' ', text or '').strip()


# 세부 포지션을 5개 주요 카테고리로 매핑
POSITION_MAP = {
    # 내야수 그룹
    '유격수': '내야수',
    '1루수': '내야수',
    '2루수': '내야수',
    '3루수': '내야수',
    # 외야수 그룹
    '중견수': '외야수',
    '우익수': '외야수',
    '좌익수': '외야수',
}


def _normalize_position(pos):
    """세부 포지션을 주요 카테고리로 정규화."""
    if not pos:
        return ''
    return POSITION_MAP.get(pos, pos)


def _normalize_hw(text):
    """Normalize 'NNNcm /   NN                                    kg' → 'NNNcm / NNkg'."""
    if not text:
        return ""
    t = _clean_text(text)
    # cm 와 kg 사이의 공백 제거: "182cm / 80 kg" -> "182cm / 80kg"
    t = re.sub(r'(\d)\s*kg', r'\1kg', t)
    t = re.sub(r'(\d)\s*cm', r'\1cm', t)
    # "cm/  80" 형태도 정리
    t = re.sub(r'\s*/\s*', ' / ', t)
    return t.strip()


def _normalize_grade(text):
    """Extract grade number from '1                학년' style text."""
    if not text:
        return ""
    t = _clean_text(text)
    # "1 학년" or "1학년" → "1"
    m = re.search(r'(\d+)\s*학년', t)
    if m:
        return m.group(1)
    # 숫자만 있는 경우
    m = re.search(r'(\d+)', t)
    return m.group(1) if m else ""


def parse_player_li(li, team_name, club_idx, region):
    """Parse a single li element to extract player/staff info."""
    dl = li.find("dl", class_="items")
    if not dl:
        return None

    # dt-dd 라벨 기반 매핑 (안전한 방식)
    dts = dl.find_all("dt")
    dds = dl.find_all("dd")
    if not dds:
        return None

    field_map = {}
    for dt, dd in zip(dts, dds):
        # dt 안의 span(name 등)은 제거하고 순수 라벨만 추출
        dt_copy = dt.__copy__()
        for sp in dt_copy.find_all("span"):
            sp.decompose()
        label = _clean_text(dt_copy.get_text())
        # 라벨 통일: '백넘버 /' → '백넘버'
        label = label.rstrip('/').strip()
        field_map[label] = dd

    # 첫 dd (백넘버/성명)
    first_dd = dds[0]
    number_span = first_dd.find("span", class_="number")
    name_span = first_dd.find("span", class_="name")
    if not name_span:
        return None

    name = name_span.get_text(strip=True)
    # 번호: 빈 span 이면 빈 문자열 처리
    number = ""
    if number_span:
        num_text = number_span.get_text(strip=True).rstrip(".")
        if num_text and num_text.isdigit():
            number = num_text

    # person_no, gubun
    link = li.find("a", href=lambda h: h and "player_view" in h)
    person_no = ""
    gubun = ""
    if link:
        href = link.get("href", "")
        if "person_no=" in href:
            person_no = href.split("person_no=")[1].split("&")[0]
        if "gubun=" in href:
            gubun = href.split("gubun=")[1].split("&")[0]

    # 라벨 기반 추출 (없으면 빈값)
    def get_field(label):
        dd = field_map.get(label)
        return _clean_text(dd.get_text()) if dd else ""

    position = _normalize_position(get_field("선수구분"))
    grade_raw = get_field("학년")
    hw_raw = get_field("신장 / 체중") or get_field("신장/체중")
    throw_bat = get_field("투타")

    # 지도자 (gubun=T) 또는 dt 라벨 기준
    is_staff = (gubun == "T") or (len(dds) == 2 and not grade_raw)

    if is_staff:
        return {
            "type": "staff",
            "name": name,
            "role": position,  # 지도자는 '선수구분' 자리에 역할
            "person_no": person_no,
        }
    else:
        return {
            "type": "player",
            "number": number,
            "name": name,
            "position": position,
            "grade": _normalize_grade(grade_raw),
            "height_weight": _normalize_hw(hw_raw),
            "throw_bat": throw_bat,
            "person_no": person_no,
            "team": team_name,
            "team_idx": club_idx,
            "region": region,
        }


def fetch_team_roster(team):
    """Fetch roster for a single team. 실패 시 예외를 던져 재시도 대상이 됨."""
    club_idx = team["club_idx"]
    team_name = team["name"]

    resp = session.get(TEAM_PLAYER_URL, params={
        "club_idx": club_idx,
        "season": 2026,
        "kind_cd": 31,
    }, timeout=15)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    players = []
    staff = []

    team_list_ul = soup.find("ul", class_="team_list")
    if team_list_ul:
        lis = team_list_ul.find_all("li", recursive=False)
        for li in lis:
            result = parse_player_li(li, team_name, club_idx, team["region"])
            if result:
                if result["type"] == "staff":
                    staff.append(result)
                else:
                    players.append(result)

    return {
        "team": team_name,
        "club_idx": club_idx,
        "region": team["region"],
        "manager": team["manager"],
        "staff": staff,
        "players": players,
        "player_count": len(players),
    }


def fetch_all_rosters(teams):
    """Fetch rosters for all teams with concurrent requests + 누락 재시도."""
    total = len(teams)
    by_idx = {}

    def do_pass(team_list, workers):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futs = {executor.submit(fetch_team_roster, t): t for t in team_list}
            for future in concurrent.futures.as_completed(futs):
                t = futs[future]
                try:
                    r = future.result()
                    # 완전히 비어있으면(선수0+지도자0) 일시 실패로 보고 재시도 대상
                    if r["player_count"] > 0 or len(r["staff"]) > 0:
                        by_idx[t["club_idx"]] = r
                        print(f"  [{len(by_idx)}/{total}] {r['team']}: {r['player_count']}명")
                except Exception as e:
                    print(f"    실패(재시도예정): {t['name']} - {e}")

    # 1차
    do_pass(teams, 8)
    # 누락 재시도 (최대 3회)
    for attempt in range(1, 4):
        missing = [t for t in teams if t["club_idx"] not in by_idx]
        if not missing:
            break
        print(f"  [재시도 {attempt}] 누락 {len(missing)}개 팀 다시 수집...")
        time.sleep(1.5)
        do_pass(missing, 4)

    # 최종 누락은 빈 항목으로라도 유지(구조 보존) + 경고
    for t in teams:
        if t["club_idx"] not in by_idx:
            print(f"  [경고] 최종 누락: {t['name']}")
            by_idx[t["club_idx"]] = {
                "team": t["name"], "club_idx": t["club_idx"],
                "region": t["region"], "manager": t["manager"],
                "staff": [], "players": [], "player_count": 0, "error": "failed",
            }

    results = list(by_idx.values())
    results.sort(key=lambda x: x["team"])
    return results


def main():
    print("=== U-18 대한야구소프트볼협회 선수 데이터 수집기 ===\n")

    print("[1/3] 팀 목록 수집 중...")
    teams = fetch_all_teams()

    if not teams:
        print("팀을 찾을 수 없습니다!")
        return

    print(f"\n[2/3] {len(teams)}개 팀 로스터 수집 중...")
    rosters = fetch_all_rosters(teams)

    print(f"\n[3/3] 데이터 저장 중...")
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "u18_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rosters, f, ensure_ascii=False, indent=2)

    total_players = sum(r["player_count"] for r in rosters)
    total_staff = sum(len(r["staff"]) for r in rosters)
    print(f"\n=== 완료 ===")
    print(f"팀: {len(rosters)}개")
    print(f"선수: {total_players}명")
    print(f"지도자: {total_staff}명")
    print(f"저장 위치: {output_path}")


if __name__ == "__main__":
    main()
