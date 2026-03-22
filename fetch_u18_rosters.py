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


def parse_player_li(li, team_name, club_idx, region):
    """Parse a single li element to extract player/staff info."""
    dl = li.find("dl", class_="items")
    if not dl:
        return None

    dds = dl.find_all("dd")
    if not dds:
        return None

    # Get number and name from first dd
    first_dd = dds[0]
    number_span = first_dd.find("span", class_="number")
    name_span = first_dd.find("span", class_="name")

    if not name_span:
        return None

    name = name_span.get_text(strip=True)
    number = number_span.get_text(strip=True).rstrip(".") if number_span else ""

    # Get person link
    link = li.find("a", href=lambda h: h and "player_view" in h)
    person_no = ""
    gubun = ""
    if link:
        href = link.get("href", "")
        if "person_no=" in href:
            person_no = href.split("person_no=")[1].split("&")[0]
        if "gubun=" in href:
            gubun = href.split("gubun=")[1].split("&")[0]

    # Parse remaining dd fields
    dd_texts = []
    for dd in dds[1:]:
        text = dd.get_text(strip=True)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        dd_texts.append(text)

    # Staff (gubun=T) vs Player (gubun=P)
    is_staff = gubun == "T"

    if is_staff:
        role = dd_texts[0] if len(dd_texts) > 0 else ""
        return {
            "type": "staff",
            "name": name,
            "role": role,
            "person_no": person_no,
        }
    else:
        position = dd_texts[0] if len(dd_texts) > 0 else ""
        grade_text = dd_texts[1] if len(dd_texts) > 1 else ""
        height_weight = dd_texts[2] if len(dd_texts) > 2 else ""
        throw_bat = dd_texts[3] if len(dd_texts) > 3 else ""

        # Clean grade
        grade = re.sub(r'[^0-9]', '', grade_text.split('학년')[0]) if grade_text else ""

        # Clean height/weight
        hw = height_weight.replace(" ", "")

        return {
            "type": "player",
            "number": number,
            "name": name,
            "position": position,
            "grade": grade,
            "height_weight": hw,
            "throw_bat": throw_bat,
            "person_no": person_no,
            "team": team_name,
            "team_idx": club_idx,
            "region": region,
        }


def fetch_team_roster(team):
    """Fetch roster for a single team."""
    club_idx = team["club_idx"]
    team_name = team["name"]

    try:
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
    except Exception as e:
        print(f"    Error fetching {team_name}: {e}")
        return {
            "team": team_name,
            "club_idx": club_idx,
            "region": team["region"],
            "manager": team["manager"],
            "staff": [],
            "players": [],
            "player_count": 0,
            "error": str(e),
        }


def fetch_all_rosters(teams):
    """Fetch rosters for all teams with concurrent requests."""
    results = []
    total = len(teams)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_team = {executor.submit(fetch_team_roster, team): team for team in teams}

        for i, future in enumerate(concurrent.futures.as_completed(future_to_team)):
            team = future_to_team[future]
            try:
                result = future.result()
                results.append(result)
                print(f"  [{i+1}/{total}] {result['team']}: {result['player_count']}명")
            except Exception as e:
                print(f"  [{i+1}/{total}] {team['name']}: ERROR - {e}")

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
