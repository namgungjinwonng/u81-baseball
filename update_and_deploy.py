# -*- coding: utf-8 -*-
"""U-18 선수 데이터 갱신 + GitHub Pages 자동 배포"""
import subprocess
import shutil
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')

sys.stdout.reconfigure(encoding='utf-8')


def run(desc, cmd):
    print(f"\n[{desc}]")
    result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8')
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        print(f"오류: {result.stderr}")
        sys.exit(1)
    return result


def main():
    print("=" * 50)
    print("  U-18 선수 데이터 갱신 + 배포")
    print("=" * 50)

    # 1. Fetch data
    run("1/4 데이터 수집", [sys.executable, "fetch_u18_rosters.py"])

    # 2. Generate HTML
    run("2/4 HTML 생성", [sys.executable, "generate_html.py"])

    # 3. Copy to docs/
    print("\n[3/4 배포 파일 복사]")
    files = [
        ("u18_players.html", "index.html"),
        ("u18_app_data.js", "u18_app_data.js"),
        ("manifest.json", "manifest.json"),
        ("sw.js", "sw.js"),
        ("icon-192.png", "icon-192.png"),
        ("icon-512.png", "icon-512.png"),
    ]
    for src, dst in files:
        src_path = os.path.join(BASE_DIR, src)
        dst_path = os.path.join(DOCS_DIR, dst)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"  {src} -> docs/{dst}")

    # Fix paths for GitHub Pages (relative)
    index_path = os.path.join(DOCS_DIR, 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('href="/manifest.json"', 'href="./manifest.json"')
    html = html.replace('href="/icon-192.png"', 'href="./icon-192.png"')
    html = html.replace('src="u18_app_data.js"', 'src="./u18_app_data.js"')
    html = html.replace("register('/sw.js')", "register('./sw.js')")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("  경로 수정 완료")

    # 4. Git commit & push
    print("\n[4/4 Git 배포]")
    run("git add", ["git", "add", "docs/"])

    # Check if there are changes
    status = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BASE_DIR)
    if status.returncode == 0:
        print("  변경사항 없음 — 배포 불필요")
    else:
        from datetime import datetime
        msg = f"데이터 갱신: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        run("git commit", ["git", "commit", "-m", msg])
        run("git push", ["git", "push"])
        print("\n✅ 배포 완료! 1~2분 후 GitHub Pages에 반영됩니다.")

    print("\n" + "=" * 50)


if __name__ == '__main__':
    main()
