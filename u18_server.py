# -*- coding: utf-8 -*-
"""U-18 선수 데이터 뷰어 + 갱신 서버"""
import http.server
import json
import os
import subprocess
import sys

PORT = 9090
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class U18Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        kwargs['directory'] = BASE_DIR
        super().__init__(*args, **kwargs)

    def _run(self, script, timeout):
        print(f"[갱신] {script} 실행 중...")
        r = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, script)],
            capture_output=True, text=True, timeout=timeout,
            cwd=BASE_DIR, encoding='utf-8'
        )
        if r.stdout:
            print(r.stdout)
        if r.returncode != 0:
            raise Exception(r.stderr or f"{script} failed")

    def do_POST(self):
        if self.path == '/refresh':
            try:
                # 1) 선수 데이터 수집
                self._run('fetch_u18_rosters.py', 300)
                # 2) 경기 일정 수집 (구장/시간 포함, 수분 소요)
                self._run('fetch_u18_schedule.py', 600)
                # 3) HTML 생성 (선수 + 일정)
                self._run('generate_html.py', 60)
                self._run('generate_schedule.py', 60)

                # 4) docs/ 폴더 업데이트 (모바일 배포용)
                print("[갱신] docs/ 폴더 업데이트 중...")
                docs_dir = os.path.join(BASE_DIR, 'docs')
                if os.path.isdir(docs_dir):
                    import shutil

                    def fix_paths(html):
                        html = html.replace('href="/manifest.json"', 'href="./manifest.json"')
                        html = html.replace('href="/icon-192.png"', 'href="./icon-192.png"')
                        html = html.replace("register('/sw.js')", "register('./sw.js')")
                        html = html.replace('src="u18_app_data.js"', 'src="./u18_app_data.js"')
                        html = html.replace('src="u18_schedule_data.js"', 'src="./u18_schedule_data.js"')
                        return html

                    # 선수 페이지 -> index.html + u18_players.html (탭 링크용)
                    players_src = os.path.join(BASE_DIR, 'u18_players.html')
                    if os.path.exists(players_src):
                        with open(players_src, 'r', encoding='utf-8') as f:
                            html = fix_paths(f.read())
                        for name in ('index.html', 'u18_players.html'):
                            with open(os.path.join(docs_dir, name), 'w', encoding='utf-8') as f:
                                f.write(html)
                    # 일정 페이지
                    sched_src = os.path.join(BASE_DIR, 'u18_schedule.html')
                    if os.path.exists(sched_src):
                        with open(sched_src, 'r', encoding='utf-8') as f:
                            html = fix_paths(f.read())
                        with open(os.path.join(docs_dir, 'u18_schedule.html'), 'w', encoding='utf-8') as f:
                            f.write(html)
                    # 데이터 JS + sw.js 복사
                    for fname in ('u18_app_data.js', 'u18_schedule_data.js', 'sw.js'):
                        src = os.path.join(BASE_DIR, fname)
                        if os.path.exists(src):
                            shutil.copy2(src, os.path.join(docs_dir, fname))
                    print("[갱신] docs/ 폴더 업데이트 완료!")

                with open(os.path.join(BASE_DIR, 'u18_data.json'), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                teams = len(data)
                players = sum(len(t['players']) for t in data)
                staff = sum(len(t['staff']) for t in data)
                games = 0
                sched_path = os.path.join(BASE_DIR, 'u18_schedule.json')
                if os.path.exists(sched_path):
                    with open(sched_path, 'r', encoding='utf-8') as f:
                        games = len(json.load(f).get('games', []))

                body = json.dumps({
                    'success': True, 'teams': teams,
                    'players': players, 'staff': staff, 'games': games
                }).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                print(f"[갱신] 완료! {teams}팀, {players}명, 지도자 {staff}명, 경기 {games}건")

            except Exception as e:
                body = json.dumps({'success': False, 'error': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                print(f"[갱신 오류] {e}")
        else:
            self.send_error(404)


def main():
    print("=" * 50)
    print(f"  U-18 선수 현황 뷰어 서버")
    print(f"  http://localhost:{PORT}/u18_players.html")
    print("=" * 50)
    print("  [갱신 버튼] 클릭 시 자동 데이터 수집 + HTML 재생성")
    print("  종료: Ctrl+C")
    print("=" * 50)

    server = http.server.HTTPServer(('', PORT), U18Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료")
        server.server_close()


if __name__ == '__main__':
    main()
