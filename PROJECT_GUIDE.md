# U-18 야구 프로젝트 참고서

> **목적**: 새 대화에서 프로젝트 재분석 없이 즉시 작업할 수 있도록 정리한 참고 문서.
> 코드를 수정했다면 이 문서도 함께 갱신해 정합성을 유지할 것.

---

## 1. 한 줄 요약
한국 **18세 이하부(고교/유스 클럽) 야구**의 **선수 명단**과 **경기 일정·결과**를 `korea-baseball.com`에서 크롤링해, 정적 HTML+PWA로 빌드하고 **GitHub Pages(`docs/`)** 로 배포하는 파이프라인.

- Repo: `https://github.com/namgungjinwonng/u81-baseball` (폴더명은 `U-18 Baseball`)
- 호스팅: GitHub Pages — `docs/` 폴더가 곧 사이트 루트
- 자동화: GitHub Actions 3종(스케줄+수동) + 로컬 러너(`local_runner/`)

---

## 2. 기술 스택
- **언어**: Python 3.11 (수집·빌드), 순수 HTML/CSS/JS(브라우저)
- **의존성** (`requirements.txt`): `requests`, `beautifulsoup4`
- **프런트**: 빌드된 단일 HTML + 외부 JS 데이터 파일(`u18_app_data.js`, `u18_schedule_data.js`)
- **PWA**: `manifest.json` + `sw.js`(network-first 캐싱, `CACHE_NAME = 'u18-baseball-v4'`)
- **DB 없음**: 모든 데이터는 JSON 파일에 평탄화 저장

---

## 3. 데이터 출처 & 파이프라인

### 출처 (대한야구소프트볼협회 사이트)
- 팀 목록: `https://www.korea-baseball.com/info/team/team_list?kind_cd=31&page=N`
- 팀 선수: `.../info/team/team_player?club_idx=...`
- 일정 캘린더: `.../game/calendar?month=M&year=Y&kind_cd=31`
- 박스 스코어: `.../game/box_score?game_idx=...`
- `kind_cd=31` = **18세 이하부** 고정

### 빌드 파이프라인 (`build_all.py`가 오케스트레이션)
```
fetch_u18_rosters.py  ──► u18_data.json       (팀+선수+스태프)
fetch_u18_schedule.py ──► u18_schedule.json   (시즌 전체 경기)
        │
        ▼
generate_html.py     ──► u18_players.html  + u18_app_data.js
generate_schedule.py ──► u18_schedule.html + u18_schedule_data.js
        │
        ▼
docs/ 반영 (fix_paths로 절대경로 → 상대경로 치환)
  ├─ index.html (= u18_players.html 사본)
  ├─ u18_players.html
  ├─ u18_schedule.html
  ├─ u18_app_data.js
  ├─ u18_schedule_data.js
  ├─ sw.js (매빌드 갱신)
  └─ manifest.json, icon-*.png (없을 때만 최초 복사)
```

### `build_all.py` 빌드 모드 (CLI 플래그)
| 플래그 | 동작 | 호출되는 스크립트 |
|---|---|---|
| (없음) | 전체 빌드 | rosters → schedule → html → schedule_html |
| `--rosters-only` | 선수만 | rosters → html |
| `--schedule-only` | 일정 전체 재수집 | schedule → schedule_html |
| `--incremental` | 일정 증분 | `fetch_u18_schedule.py --incremental` → schedule_html |

**증분 갱신 규칙**: 상태=`완료`인 경기는 보존, 예정/미확정/누락만 재수집해 병합. → 완료 경기 정정은 `--schedule-only` 또는 전체 빌드로만 수정됨.

---

## 4. 파일 맵

### 루트 — Python 소스
| 파일 | 줄수 | 역할 |
|---|---:|---|
| `build_all.py` | 132 | 빌드 오케스트레이션. 4가지 모드. `docs/` 반영과 `fix_paths()` 담당 |
| `fetch_u18_rosters.py` | 321 | 팀 목록(4페이지) → 팀별 선수/스태프 크롤. `concurrent.futures` 병렬. 결과 = `u18_data.json` |
| `fetch_u18_schedule.py` | 300 | 월별 calendar → game_idx 수집 → box_score 병렬 파싱. `--incremental` 시 완료 경기 보존. 결과 = `u18_schedule.json` |
| `generate_html.py` | 890 | `u18_data.json` → 선수 페이지(`u18_players.html`)+데이터JS(`u18_app_data.js`). MLB 스타일 UI, 지역/팀/포지션 필터 |
| `generate_schedule.py` | 728 | `u18_schedule.json` + `u18_data.json`(팀-지역 매핑) → 일정 페이지+데이터JS. 월별 캘린더 뷰 / 학교별 뷰 모달 |
| `u18_server.py` | — | **로컬 뷰어 서버** (포트 9090). `POST /refresh`로 수동 재수집 트리거 |
| `generate_icons.py` | — | PWA 아이콘 생성 유틸 (재실행 거의 없음) |

### 루트 — 데이터/정적 파일
- `u18_data.json` — 팀 배열. 각 팀에 `team, club_idx, region, manager, players[], staff[], player_count`
- `u18_schedule.json` — `{year, updated, games[]}`. 각 game: `game_idx, title, date, time, venue, round, status, away/home: {name, result, score}`
- `u18_app_data.js` — `const allPlayers = [...]` (선수 평탄화 배열)
- `u18_schedule_data.js` — `const scheduleData = {...}`
- `u18_players.html`, `u18_schedule.html` — 빌드 결과 (절대경로 버전)
- `manifest.json`, `icon-192.png`, `icon-512.png`, `sw.js` — PWA 자산
- `requirements.txt` — `requests` + `beautifulsoup4`만

### `docs/` — GitHub Pages 배포 산출물 (수동 편집 금지)
- `index.html` = `u18_players.html` 사본 (PWA `start_url`은 `/u18_players.html`이지만 루트 진입도 선수 페이지)
- `u18_players.html`, `u18_schedule.html` — 상대경로 버전
- `u18_app_data.js`, `u18_schedule_data.js`
- `sw.js`, `manifest.json`, `icon-*.png`

### `local_runner/` — PC 자동화 도구 (메인 파이프라인과 독립)
- `u18_auto.py` (278줄) — 30분마다 `build_all.py --incremental` 실행 후 git commit & push. KST 09~21시 + 오늘 경기 있을 때만 작동. 포트 9091에 제어 페이지 제공
- `run.bat` — 더블클릭 진입점
- `README.md` — 사용법
- 커밋 대상: `u18_schedule.json`, `u18_schedule.html`, `u18_schedule_data.js`, `docs/u18_schedule.{html,js}` (선수 파일은 건드리지 않음)
- push 전 `git pull --rebase`로 GitHub Actions와의 충돌 방지

### `.github/workflows/`
| 워크플로우 | 트리거 | 실행 | concurrency 그룹 |
|---|---|---|---|
| `update.yml` (1) | 수동만 | `build_all.py` (전체) | `u18-update` |
| `update_rosters.yml` (2) | `cron: 17 1 * * *` (매일 10:17 KST) + 수동 | `build_all.py --rosters-only` | `u18-update` |
| `update_schedule.yml` (3) | `cron: 17 3,9,12 * * *` (12:17/18:17/21:17 KST) + 수동 | `build_all.py --incremental` | `u18-update` |

> 모든 워크플로우는 같은 `u18-update` 그룹 → 동시 실행 방지(push 충돌 회피).
> 커밋 메시지 패턴: `자동 데이터 갱신 (YYYY-MM-DD HH:MM KST)` / `일정 증분 갱신 (...)` / `선수 데이터 갱신 (...)`.

### `.claude/`
- `launch.json` — `python -m http.server 8080` 디버그 설정 (`.gitignore`에 `settings.local.json`만 무시)

---

## 5. 데이터 스키마

### `u18_data.json` (선수)
```json
[{
  "team": "GD챌린저스BC(U-18)",
  "club_idx": "1702",
  "region": "서울",
  "manager": "송구홍",
  "player_count": 30,
  "players": [
    {"type":"player","number":"13","name":"기재혁","position":"외야수",
     "grade":"1","height_weight":"182cm / 80kg","throw_bat":"우투우타",
     "person_no":"...","team":"...","team_idx":"1702","region":"서울"}
  ],
  "staff": [
    {"type":"staff","name":"...","role":"감독","person_no":"..."}
  ]
}]
```

### `u18_schedule.json` (일정)
```json
{
  "year": 2026,
  "updated": "2026-06-27 15:13",
  "games": [{
    "game_idx": "36897",
    "title": "2026 고교야구 주말리그 전반기(충청권)",
    "date": "2026-03-07", "time": "09:30",
    "venue": "공주 시립야구장", "round": "리그전",
    "status": "완료",
    "away": {"name":"공주고","result":"승","score":35},
    "home": {"name":"아산BC(U-18)","result":"패","score":...}
  }]
}
```

`status` 값: `완료` / `예정` / 그 외(취소·연기 등). 증분 갱신은 `완료`만 보존하고 나머지를 재수집.

### 팀명 정규화 (`generate_schedule.py`)
- 박스스코어상 표기와 선수 명단 표기가 다를 수 있어 매핑 로직 존재:
  - 명시적: `ALIAS_EXPLICIT = {"상우고": "상우고야구단"}`
  - 자동: 접미사(`(U-18)`, `야구단`, `BC`, `고등학교`) 제거한 핵심이름으로 매칭, 충돌 시 매칭 제외
- 새 별칭 충돌이 발견되면 `ALIAS_EXPLICIT`에 추가.

---

## 6. 로컬 실행

### 빌드
```bash
pip install -r requirements.txt
python build_all.py                  # 전체
python build_all.py --rosters-only   # 선수만
python build_all.py --incremental    # 일정 증분
python build_all.py --schedule-only  # 일정 전체 재수집
```

### 미리보기
```bash
# 옵션 A: 단순 정적 서버
python -m http.server 8080
# → http://localhost:8080/u18_players.html

# 옵션 B: 갱신 트리거 가능한 서버
python u18_server.py                 # 포트 9090, POST /refresh 지원

# 옵션 C: 자동 증분 + 자동 push
local_runner/run.bat                 # 포트 9091, 30분마다 자동
```

> **테스트는 항상 `docs/` 가 아닌 루트 파일로 한 뒤, `build_all.py`로 `docs/`에 반영**. `docs/`를 직접 편집하면 다음 빌드에 덮어쓰임.

---

## 7. 중요 컨벤션 & 주의사항

1. **시즌 연도 자동 인식**: `SEASON = datetime.now(KST).year`. 연말/연초 전환 시 별도 작업 불필요.
2. **인코딩**: 모든 파이썬 스크립트 첫머리에 `sys.stdout.reconfigure(encoding='utf-8')`. Windows 콘솔 깨짐 방지 — 새 스크립트 추가 시 동일 패턴 유지.
3. **HTML 경로 치환**: 루트 HTML은 절대경로(`/manifest.json`, `/sw.js`, …) 기준. `docs/`에 복사할 때 `build_all.py:fix_paths()`가 상대경로로 변환. **새 절대경로 추가 시 `fix_paths()`에 항목을 추가**해야 GitHub Pages에서 404 안 남.
4. **PWA 캐시 무효화**: 정적 자산 구조를 바꿨다면 `sw.js`의 `CACHE_NAME` 버전 번호(`v4` → `v5`)를 올려야 사용자 브라우저가 새 자산을 가져옴.
5. **GitHub Pages는 `docs/`만 본다**: 루트 변경은 사이트에 영향 없음. 반드시 `docs/`에 반영해야 배포됨.
6. **로컬 push와 Actions 충돌**: 같은 `u18-update` concurrency 그룹으로 워크플로우 끼리는 직렬화되지만, 로컬 러너는 별개. `local_runner`는 push 전에 `git pull --rebase`로 자동 처리하지만, 수동 작업 시에도 pull부터 할 것.
7. **`docs/` 직접 커밋 금지**: 빌드 산출물이므로 소스 수정 → `build_all.py` 재실행 흐름만 사용.
8. **요청 부하 관리**: `fetch_u18_schedule.py`는 calendar 실패 시 지수 백오프 재시도(5,10,20,40초). 차단 우려 시 동시성 낮출 것.

---

## 8. 자주 하는 작업 → 어디를 만지나

| 하고 싶은 것 | 만질 파일 |
|---|---|
| 선수 페이지 UI/필터 수정 | `generate_html.py` → 빌드 |
| 일정 페이지 UI 수정 | `generate_schedule.py` → 빌드 |
| 새 팀명 별칭 매핑 | `generate_schedule.py`의 `ALIAS_EXPLICIT` |
| 수집 스케줄 변경 | `.github/workflows/update_*.yml`의 `cron` |
| 로컬 자동 갱신 주기 변경 | `local_runner/u18_auto.py`의 `INTERVAL_MIN`, `START_HOUR/END_HOUR` |
| PWA 아이콘/이름 변경 | `manifest.json` + `generate_icons.py` |
| 새 정적 자산 추가 | 루트에 두고 `build_all.py:ensure_static()` 또는 `fix_paths()` 갱신 + `sw.js` ASSETS 추가 + `CACHE_NAME` 버전업 |
| 데이터 출처 사이트 변경 대응 | `fetch_u18_rosters.py` / `fetch_u18_schedule.py`의 셀렉터 |

---

## 9. 작업 흐름 체크리스트
- [ ] 소스 코드 수정 (루트의 `.py` 또는 템플릿 부분)
- [ ] 해당하는 `build_all.py` 모드로 빌드
- [ ] `docs/` 산출물 변경 확인 (`git status`)
- [ ] 로컬 미리보기 (`python -m http.server` 또는 `u18_server.py`)
- [ ] 정적 자산을 바꿨다면 `sw.js` `CACHE_NAME` 버전업
- [ ] 커밋 → push → GitHub Pages 반영 대기(보통 1~2분)
