# -*- coding: utf-8 -*-
"""서버 없이 전체 빌드: 선수+일정 수집 -> HTML 생성 -> docs/ 반영.

로컬에서도, GitHub Actions(자동 갱신)에서도 동일하게 사용한다.
manifest.json / 아이콘은 docs/에 이미 있는 것을 유지(상대경로)하므로 덮어쓰지 않는다.
"""
import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def run(script, *args):
    print(f"\n>>> {script} {' '.join(args)} 실행".rstrip())
    subprocess.run([sys.executable, os.path.join(BASE_DIR, script), *args],
                   check=True, cwd=BASE_DIR)


def fix_paths(html):
    html = html.replace('href="/manifest.json"', 'href="./manifest.json"')
    html = html.replace('href="/icon-192.png"', 'href="./icon-192.png"')
    html = html.replace("register('/sw.js')", "register('./sw.js')")
    html = html.replace('src="u18_app_data.js"', 'src="./u18_app_data.js"')
    html = html.replace('src="u18_schedule_data.js"', 'src="./u18_schedule_data.js"')
    return html


def read(name):
    with open(os.path.join(BASE_DIR, name), "r", encoding="utf-8") as f:
        return f.read()


def write_docs(name, content):
    with open(os.path.join(BASE_DIR, "docs", name), "w", encoding="utf-8") as f:
        f.write(content)


def copy_to_docs(fname):
    shutil.copy2(os.path.join(BASE_DIR, fname), os.path.join(BASE_DIR, "docs", fname))


def reflect_schedule():
    """일정 페이지/데이터를 docs/에 반영."""
    schedule = fix_paths(read("u18_schedule.html"))
    write_docs("u18_schedule.html", schedule)
    copy_to_docs("u18_schedule_data.js")


def reflect_players():
    """선수 페이지/데이터를 docs/에 반영 (index.html 겸용)."""
    players = fix_paths(read("u18_players.html"))
    write_docs("index.html", players)
    write_docs("u18_players.html", players)
    copy_to_docs("u18_app_data.js")


def ensure_static():
    """sw.js 갱신 + manifest/아이콘이 docs에 없으면(최초) 한 번 채움."""
    copy_to_docs("sw.js")
    docs = os.path.join(BASE_DIR, "docs")
    for fname in ("manifest.json", "icon-192.png", "icon-512.png"):
        dst = os.path.join(docs, fname)
        if not os.path.exists(dst) and os.path.exists(os.path.join(BASE_DIR, fname)):
            shutil.copy2(os.path.join(BASE_DIR, fname), dst)


def build_full():
    print("=== U-18 전체 빌드 시작 ===")
    # 1) 데이터 수집 (선수 -> 일정 순서: 일정 정규화가 선수목록 사용)
    run("fetch_u18_rosters.py")
    run("fetch_u18_schedule.py")
    # 2) HTML 생성
    run("generate_html.py")
    run("generate_schedule.py")
    # 3) docs/ 반영
    os.makedirs(os.path.join(BASE_DIR, "docs"), exist_ok=True)
    reflect_players()
    reflect_schedule()
    ensure_static()
    print("\n=== 빌드 완료: docs/ 반영됨 (전체) ===")


def build_rosters_only():
    print("=== U-18 선수 전용 빌드 시작 ===")
    # 선수만 수집 → 선수 페이지 생성/반영 (일정은 건드리지 않음)
    run("fetch_u18_rosters.py")
    run("generate_html.py")
    os.makedirs(os.path.join(BASE_DIR, "docs"), exist_ok=True)
    reflect_players()
    print("\n=== 빌드 완료: docs/ 반영됨 (선수만) ===")


def build_schedule_only():
    print("=== U-18 일정 전용 빌드 시작 ===")
    # 일정 전체 수집 (팀-지역 매핑은 저장소의 기존 u18_data.json 재사용)
    run("fetch_u18_schedule.py")
    run("generate_schedule.py")
    # docs/ 반영: 일정 파일만
    os.makedirs(os.path.join(BASE_DIR, "docs"), exist_ok=True)
    reflect_schedule()
    print("\n=== 빌드 완료: docs/ 반영됨 (일정 전체) ===")


def build_incremental():
    print("=== U-18 일정 증분 빌드 시작 ===")
    # 완료 경기는 보존, 예정·신규(누락 포함)만 재수집해 병합
    run("fetch_u18_schedule.py", "--incremental")
    run("generate_schedule.py")
    # docs/ 반영: 일정 파일만
    os.makedirs(os.path.join(BASE_DIR, "docs"), exist_ok=True)
    reflect_schedule()
    print("\n=== 빌드 완료: docs/ 반영됨 (일정 증분) ===")


def main():
    if "--rosters-only" in sys.argv:
        build_rosters_only()
    elif "--incremental" in sys.argv:
        build_incremental()
    elif "--schedule-only" in sys.argv:
        build_schedule_only()
    else:
        build_full()


if __name__ == "__main__":
    main()
