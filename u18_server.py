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

    def do_POST(self):
        if self.path == '/refresh':
            try:
                print("[갱신] 데이터 수집 시작...")
                result = subprocess.run(
                    [sys.executable, os.path.join(BASE_DIR, 'fetch_u18_rosters.py')],
                    capture_output=True, text=True, timeout=300,
                    cwd=BASE_DIR, encoding='utf-8'
                )
                if result.stdout:
                    print(result.stdout)
                if result.returncode != 0:
                    raise Exception(result.stderr or "fetch failed")

                print("[갱신] HTML 생성 중...")
                result2 = subprocess.run(
                    [sys.executable, os.path.join(BASE_DIR, 'generate_html.py')],
                    capture_output=True, text=True, timeout=60,
                    cwd=BASE_DIR, encoding='utf-8'
                )
                if result2.stdout:
                    print(result2.stdout)
                if result2.returncode != 0:
                    print(f"[경고] generate_html 오류: {result2.stderr}")
                    raise Exception(result2.stderr or "generate failed")

                # docs/ 폴더에도 복사 (모바일 배포용)
                print("[갱신] docs/ 폴더 업데이트 중...")
                docs_dir = os.path.join(BASE_DIR, 'docs')
                if os.path.isdir(docs_dir):
                    import shutil
                    # index.html 복사 (경로를 상대경로로 변환)
                    html_src = os.path.join(BASE_DIR, 'u18_players.html')
                    if os.path.exists(html_src):
                        with open(html_src, 'r', encoding='utf-8') as f:
                            html = f.read()
                        html = html.replace('href="/manifest.json"', 'href="./manifest.json"')
                        html = html.replace('href="/icon-192.png"', 'href="./icon-192.png"')
                        html = html.replace("register('/sw.js')", "register('./sw.js')")
                        html = html.replace('src="u18_app_data.js"', 'src="./u18_app_data.js"')
                        with open(os.path.join(docs_dir, 'index.html'), 'w', encoding='utf-8') as f:
                            f.write(html)
                    # JS 데이터 복사
                    js_src = os.path.join(BASE_DIR, 'u18_app_data.js')
                    if os.path.exists(js_src):
                        shutil.copy2(js_src, os.path.join(docs_dir, 'u18_app_data.js'))
                    # manifest, sw 복사
                    for fname in ['manifest.json', 'sw.js']:
                        src = os.path.join(BASE_DIR, fname)
                        if os.path.exists(src):
                            shutil.copy2(src, os.path.join(docs_dir, fname))
                    print("[갱신] docs/ 폴더 업데이트 완료!")

                with open(os.path.join(BASE_DIR, 'u18_data.json'), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                teams = len(data)
                players = sum(len(t['players']) for t in data)
                staff = sum(len(t['staff']) for t in data)

                body = json.dumps({
                    'success': True, 'teams': teams,
                    'players': players, 'staff': staff
                }).encode('utf-8')

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                print(f"[갱신] 완료! {teams}팀, {players}명, {staff}명 지도자")

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
