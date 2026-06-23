# -*- coding: utf-8 -*-
"""로컬 자동 일정 수집기 (PC 실행용).

- 시작 시 1회 수집 → 이후 30분마다 자동 수집.
- 오늘(KST) 경기가 있고 09:00~21:00 일 때만 수집(시작 직후 1회는 즉시 실행).
- 수집 = 저장소 루트의 build_all.py --incremental (일정 증분 + docs 반영).
- 수집 후 변경된 일정 파일을 git commit & push 로 GitHub 에 반영.
- 단순 제어 웹페이지 제공([종료] 버튼). 브라우저를 닫아도 종료 전까지 백그라운드로 동작.

기존 스크립트/워크플로우와 독립적이며, 이 폴더(local_runner) 안에서만 동작한다.
"""
import http.server
import json
import os
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
PORT = 9091
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)                # 상위 폴더 = 저장소 루트
INTERVAL_MIN = 30                           # 갱신 주기(분)
START_HOUR, END_HOUR = 9, 21                # 자동 수집 허용 시간대 (09~21시)
COMMIT_FILES = [
    "u18_schedule.json", "u18_schedule.html", "u18_schedule_data.js",
    "docs/u18_schedule.html", "docs/u18_schedule_data.js",
]

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

state = {
    "running": True, "busy": False,
    "today": "", "today_games": 0,
    "last_run": "-", "last_result": "-", "next_run": "-",
    "log": [],
}
_stop = threading.Event()
_lock = threading.Lock()


def now_kst():
    return datetime.now(KST)


def log(msg):
    line = f"[{now_kst().strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    state["log"].insert(0, line)
    del state["log"][40:]


def count_today_games():
    path = os.path.join(REPO, "u18_schedule.json")
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        today = now_kst().strftime("%Y-%m-%d")
        return sum(1 for g in data.get("games", []) if g.get("date") == today)
    except Exception as e:
        log(f"경기 수 확인 실패: {e}")
        return 0


def _git(*args, timeout=120):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                          text=True, encoding="utf-8", timeout=timeout)


def collect_and_push():
    """build_all.py --incremental 실행 후 변경분 commit & push."""
    if state["busy"]:
        log("이미 수집 중 - 건너뜀")
        return
    with _lock:
        state["busy"] = True
        state["last_run"] = now_kst().strftime("%H:%M:%S")
        try:
            # 1) 원격 최신을 기준으로 동기화 (빌드는 깨끗한 트리에서, 분기/충돌 방지)
            log("원격 최신 동기화")
            _git("fetch", "origin", "main")
            rs = _git("reset", "--hard", "origin/main")
            if rs.returncode != 0:
                log("동기화 경고: " + (rs.stderr or "")[-200:])

            # 2) 증분 수집 (원격 최신 데이터 기준으로 빌드)
            log("증분 수집 시작 (build_all.py --incremental)")
            r = subprocess.run([sys.executable, os.path.join(REPO, "build_all.py"), "--incremental"],
                               cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=1800)
            if r.returncode != 0:
                state["last_result"] = "수집 실패"
                log("수집 실패: " + (r.stderr or "")[-300:])
                return

            # 3) 변경분 커밋 (없으면 종료)
            _git("add", *COMMIT_FILES)
            if _git("diff", "--staged", "--quiet").returncode == 0:
                state["last_result"] = "변경 없음"
                log("변경 없음 - 커밋 생략")
                return
            msg = "로컬 일정 갱신 (" + now_kst().strftime("%Y-%m-%d %H:%M KST") + ")"
            _git("commit", "-m", msg)

            # 4) push (커밋 후 시도, 원격이 그새 바뀌면 rebase 후 1회 재시도)
            if _git("push", "origin", "main").returncode == 0:
                state["last_result"] = "성공(푸시됨)"
                log("GitHub push 완료")
                return
            log("push 거부됨 - 원격 변경 반영 후 재시도")
            rb = _git("pull", "--rebase", "origin", "main")
            if rb.returncode != 0:
                _git("rebase", "--abort")
                state["last_result"] = "충돌(다음 주기 재시도)"
                log("원격과 충돌 - 이번 주기 건너뜀 (다음 30분 후 재시도)")
                return
            if _git("push", "origin", "main").returncode == 0:
                state["last_result"] = "성공(푸시됨)"
                log("재시도 push 완료")
            else:
                state["last_result"] = "push 실패"
                log("재시도 push 실패")
        except subprocess.TimeoutExpired:
            state["last_result"] = "시간초과"
            log("수집 시간초과")
        except Exception as e:
            state["last_result"] = "오류"
            log(f"오류: {e}")
        finally:
            state["busy"] = False
            state["next_run"] = (now_kst() + timedelta(minutes=INTERVAL_MIN)).strftime("%H:%M")


def scheduler():
    state["today"] = now_kst().strftime("%Y-%m-%d")
    state["today_games"] = count_today_games()
    log(f"오늘({state['today']}) 경기 {state['today_games']}건")
    # 시작 직후 1회 (경기 있으면 즉시)
    if state["today_games"] > 0:
        collect_and_push()
    else:
        log("오늘 경기 없음 - 대기")
    # 이후 30분 주기
    while not _stop.wait(INTERVAL_MIN * 60):
        state["today"] = now_kst().strftime("%Y-%m-%d")
        state["today_games"] = count_today_games()
        h = now_kst().hour
        if state["today_games"] > 0 and START_HOUR <= h < END_HOUR:
            collect_and_push()
        else:
            reason = "경기 없음" if state["today_games"] == 0 else f"{h}시 (09~21시 밖)"
            log(f"건너뜀 - {reason}")


PAGE = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>U-18 로컬 자동 수집기</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Malgun Gothic',sans-serif;background:#F4F6F8;color:#111;padding:18px;max-width:560px;margin:0 auto}
h1{font-size:18px;color:#002D62;margin-bottom:12px}
.card{background:#fff;border:2px solid #002D62;border-radius:4px;padding:14px;margin-bottom:12px}
.row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #eee;font-size:14px}
.row:last-child{border-bottom:none}
.row .k{color:#666;font-weight:700}
.row .v{font-weight:800;color:#002D62}
.btns{display:flex;gap:8px;margin-bottom:12px}
button{flex:1;padding:11px;border:none;border-radius:4px;font-size:14px;font-weight:800;cursor:pointer}
.run{background:#002D62;color:#fff}
.stop{background:#BA0C2F;color:#fff}
#log{background:#0c1320;color:#9fe1cb;font-size:12px;border-radius:4px;padding:10px;height:220px;overflow:auto;white-space:pre-wrap;line-height:1.5}
.badge{font-size:12px;font-weight:700;padding:2px 8px;border-radius:10px}
.on{background:#E1F5EE;color:#0F6E56}.off{background:#FBE9EC;color:#A8344B}
</style></head><body>
<h1>U-18 로컬 자동 일정 수집기</h1>
<div class="card">
  <div class="row"><span class="k">상태</span><span class="v"><span id="st" class="badge on">동작중</span></span></div>
  <div class="row"><span class="k">오늘 날짜</span><span class="v" id="today">-</span></div>
  <div class="row"><span class="k">오늘 경기 수</span><span class="v" id="games">-</span></div>
  <div class="row"><span class="k">마지막 수집</span><span class="v" id="last">-</span></div>
  <div class="row"><span class="k">마지막 결과</span><span class="v" id="result">-</span></div>
  <div class="row"><span class="k">다음 예정</span><span class="v" id="next">-</span></div>
  <div class="row"><span class="k">주기</span><span class="v">30분 (09~21시)</span></div>
</div>
<div class="btns">
  <button class="run" onclick="runNow()">지금 수집</button>
  <button class="stop" onclick="shutdown()">종료</button>
</div>
<div id="log"></div>
<script>
async function tick(){
  try{
    const r=await fetch('/status'); const s=await r.json();
    document.getElementById('today').textContent=s.today;
    document.getElementById('games').textContent=s.today_games+'건';
    document.getElementById('last').textContent=s.last_run+(s.busy?' (수집중...)':'');
    document.getElementById('result').textContent=s.last_result;
    document.getElementById('next').textContent=s.next_run;
    const st=document.getElementById('st');
    st.textContent=s.running?(s.busy?'수집중':'동작중'):'종료됨';
    st.className='badge '+(s.running?'on':'off');
    document.getElementById('log').textContent=(s.log||[]).join('\\n');
  }catch(e){
    document.getElementById('st').textContent='연결끊김(종료됨)';
    document.getElementById('st').className='badge off';
  }
}
async function runNow(){ await fetch('/run',{method:'POST'}); setTimeout(tick,500); }
async function shutdown(){ if(confirm('자동 수집을 종료할까요?')){ try{await fetch('/shutdown',{method:'POST'});}catch(e){} document.getElementById('st').textContent='종료됨'; } }
setInterval(tick,2000); tick();
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self._send(200, PAGE, "text/html")
        elif self.path == "/status":
            self._send(200, json.dumps(state, ensure_ascii=False))
        else:
            self._send(404, "{}")

    def do_POST(self):
        if self.path == "/run":
            threading.Thread(target=collect_and_push, daemon=True).start()
            self._send(200, '{"ok":true}')
        elif self.path == "/shutdown":
            self._send(200, '{"ok":true}')
            log("종료 요청 수신")
            state["running"] = False
            _stop.set()
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self._send(404, "{}")

    def log_message(self, *args):
        pass


def main():
    print("=" * 52)
    print("  U-18 로컬 자동 일정 수집기")
    print(f"  제어 페이지: http://localhost:{PORT}/")
    print(f"  주기: {INTERVAL_MIN}분 / 시간대: {START_HOUR}~{END_HOUR}시 / 저장소: {REPO}")
    print("  종료: 웹페이지 [종료] 버튼 또는 이 창에서 Ctrl+C")
    print("=" * 52)
    threading.Thread(target=scheduler, daemon=True).start()
    try:
        webbrowser.open(f"http://localhost:{PORT}/")
    except Exception:
        pass
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _stop.set()
        print("\n서버 종료")


if __name__ == "__main__":
    main()
