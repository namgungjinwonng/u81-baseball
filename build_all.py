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


def run(script):
    print(f"\n>>> {script} 실행")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, script)],
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


def main():
    print("=== U-18 전체 빌드 시작 ===")
    # 1) 데이터 수집 (선수 -> 일정 순서: 일정 정규화가 선수목록 사용)
    run("fetch_u18_rosters.py")
    run("fetch_u18_schedule.py")
    # 2) HTML 생성
    run("generate_html.py")
    run("generate_schedule.py")

    # 3) docs/ 반영
    docs = os.path.join(BASE_DIR, "docs")
    os.makedirs(docs, exist_ok=True)

    players = fix_paths(read("u18_players.html"))
    write_docs("index.html", players)
    write_docs("u18_players.html", players)

    schedule = fix_paths(read("u18_schedule.html"))
    write_docs("u18_schedule.html", schedule)

    for fname in ("u18_app_data.js", "u18_schedule_data.js", "sw.js"):
        shutil.copy2(os.path.join(BASE_DIR, fname), os.path.join(docs, fname))

    # manifest / 아이콘이 docs에 없으면(최초) 한 번 채워줌
    for fname in ("manifest.json", "icon-192.png", "icon-512.png"):
        dst = os.path.join(docs, fname)
        if not os.path.exists(dst) and os.path.exists(os.path.join(BASE_DIR, fname)):
            shutil.copy2(os.path.join(BASE_DIR, fname), dst)

    print("\n=== 빌드 완료: docs/ 반영됨 ===")


if __name__ == "__main__":
    main()
