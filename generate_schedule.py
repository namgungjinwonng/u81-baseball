# -*- coding: utf-8 -*-
"""u18_schedule.json -> u18_schedule.html + u18_schedule_data.js 생성.

선수 현황 앱과 동일한 UX/MLB 스타일.
- 월별: 달력만 표시 -> 날짜 클릭 시 현황창(모달)에 그 날 경기 스크롤
- 학교별: 지역/이름 검색 -> 학교 카드 -> 클릭 시 현황창(모달)에 전적+경기(최근 내림차순)
팀-지역 매핑은 선수 데이터(u18_data.json)에서 가져온다.
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "u18_schedule.json"), "r", encoding="utf-8") as f:
    sched = json.load(f)

# 팀 -> 지역 매핑 (선수 데이터)
team_region = {}
roster_path = os.path.join(BASE_DIR, "u18_data.json")
if os.path.exists(roster_path):
    with open(roster_path, "r", encoding="utf-8") as f:
        roster = json.load(f)
    for t in roster:
        if t.get("team") and t.get("region"):
            team_region[t["team"]] = t["region"]

year = sched.get("year", "")
updated = sched.get("updated", "")

# ── 팀명 표기 정규화: 일정(box_score) 표기를 선수 목록 표기로 통일 ──
# 명시적 별칭 (확인된 케이스)
ALIAS_EXPLICIT = {
    "상우고": "상우고야구단",
}

def _core(s):
    """접미사 제거 후 핵심 이름."""
    for suf in ["(U-18)", "야구단", "BC", "고등학교"]:
        s = s.replace(suf, "")
    return s.strip()

roster_names = set(team_region.keys())
# roster 핵심이름 -> 정식이름 (충돌 시 자동매칭 제외)
core_to_roster, collisions = {}, set()
for rn in roster_names:
    c = _core(rn)
    if c and c in core_to_roster and core_to_roster[c] != rn:
        collisions.add(c)
    if c:
        core_to_roster[c] = rn

sched_names = set()
for g in sched["games"]:
    sched_names.add(g["away"]["name"])
    sched_names.add(g["home"]["name"])

alias = {}
for sn in sched_names:
    if sn in ALIAS_EXPLICIT:
        alias[sn] = ALIAS_EXPLICIT[sn]
    elif sn in roster_names:
        continue
    else:
        c = _core(sn)
        if c in core_to_roster and c not in collisions:
            alias[sn] = core_to_roster[c]

# 적용
applied = 0
for g in sched["games"]:
    for side in ("away", "home"):
        n = g[side]["name"]
        if n in alias:
            g[side]["name"] = alias[n]
            applied += 1

if alias:
    print("팀명 정규화 매핑:")
    for k, v in sorted(alias.items()):
        print(f"  {k} -> {v}")
    print(f"  (총 {applied}건 적용)")

with open(os.path.join(BASE_DIR, "u18_schedule_data.js"), "w", encoding="utf-8") as f:
    f.write(f"const scheduleData = {json.dumps(sched, ensure_ascii=False)};\n")
    f.write(f"const teamRegionMap = {json.dumps(team_region, ensure_ascii=False)};\n")

HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>KBSA U-18 경기 일정</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#002D62">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/icon-192.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Montserrat','Malgun Gothic','Apple SD Gothic Neo',sans-serif; background: #F4F6F8; color: #111111; }

.header { background: #002D62; color: white; padding: 22px 20px 0; text-align: center; }
.header h1 { font-size: 26px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }
.header .subtitle { font-size: 14px; opacity: 0.85; margin-top: 6px; }
.header .update-info { font-size: 12px; opacity: 0.6; margin-top: 4px; }
.refresh-spacer { height: 88px; }
.tabs { display: flex; justify-content: center; gap: 0; margin-top: 16px; }
.tab { padding: 11px 26px; font-size: 14px; font-weight: 800; letter-spacing: 0.5px; color: rgba(255,255,255,0.6);
    background: transparent; border: none; border-bottom: 4px solid transparent; cursor: pointer; text-decoration: none; }
.tab.active { color: #fff; border-bottom-color: #BA0C2F; }
.tab:hover { color: #fff; }
.reload-btn {
    margin-top: 10px; padding: 8px 22px; border: 2px solid rgba(255,255,255,0.5);
    background: rgba(255,255,255,0.1); color: white; border-radius: 25px;
    font-size: 12px; font-weight: 700; cursor: pointer; transition: all 0.3s;
    letter-spacing: 1px;
}
.reload-btn:hover { background: rgba(255,255,255,0.25); border-color: white; }
.install-btn {
    display: none; margin-top: 10px; padding: 10px 28px; border: 2px solid #4CAF50;
    background: #4CAF50; color: white; border-radius: 25px;
    font-size: 14px; font-weight: 700; cursor: pointer; transition: all 0.3s; letter-spacing: 1px;
}
.install-btn:hover { background: #45a049; border-color: #45a049; }

.viewbar-spacer { height: 20px; }
.viewbar { background: #fff; border-bottom: 4px solid #BA0C2F; padding: 34px 12px; display: flex; justify-content: center; gap: 8px; align-items: center; }
.view-btn { padding: 8px 22px; border: 2px solid #002D62; border-radius: 2px; background: #fff; color: #002D62; font-size: 13px; font-weight: 700; cursor: pointer; }
.view-btn.active { background: #002D62; color: #fff; }

.container { max-width: 760px; margin: 0 auto; padding: 16px; }

.month-nav { display: flex; justify-content: space-between; align-items: center; background: #002D62; border-radius: 2px; padding: 10px 14px; margin-bottom: 12px; }
.month-nav .nav-btn { font-size: 14px; font-weight: 800; color: #fff; cursor: pointer; background: none; border: none; padding: 4px 8px; }
.month-nav .nav-btn:disabled { color: rgba(255,255,255,0.3); cursor: default; }
.month-nav .cur { font-size: 17px; font-weight: 800; color: #fff; }

.cal { background: #fff; border: 2px solid #002D62; border-radius: 2px; padding: 10px; }
.cal-wd-row { display: grid; grid-template-columns: repeat(7,1fr); gap: 4px; margin-bottom: 4px; }
.cal-grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 4px; grid-auto-rows: 46px; }
.cal-wd { text-align: center; font-size: 11px; font-weight: 700; padding: 4px 0; color: #888; }
.cal-wd.sun { color: #C8102E; } .cal-wd.sat { color: #2E6E9E; }
.cal-day { display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px solid transparent; border-radius: 2px; font-size: 14px; font-weight: 700; color: #ccc; overflow: hidden; }
.cal-day.empty { visibility: hidden; }
.cal-day.has { background: #fff; border-color: #cdd3da; cursor: pointer; color: #002D62; }
.cal-day.has:hover { border-color: #BA0C2F; background: #fdeef1; }
.cal-day .cnt { font-size: 9px; font-weight: 700; color: #BA0C2F; margin-top: 2px; }

/* 학교 검색 (선수 페이지와 동일 톤) */
.filters { background: #fff; border-radius: 2px; padding: 16px; margin-bottom: 16px; border: 2px solid #002D62; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filters label { font-size: 13px; font-weight: 700; color: #002D62; }
.filters select, .filters input { padding: 8px 12px; border: 2px solid #cdd3da; border-radius: 2px; font-size: 13px; outline: none; }
.filters select:focus, .filters input:focus { border-color: #002D62; }
.filters input { flex: 1; min-width: 120px; }
.sbtn { padding: 9px 20px; border: none; border-radius: 2px; background: #002D62; color: #fff; font-size: 13px; font-weight: 700; cursor: pointer; }
.sbtn:hover { background: #BA0C2F; }
.sbtn.clr { background: #666; }
.result-count { width: 100%; font-size: 13px; color: #888; font-weight: 600; }

.team-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px,1fr)); gap: 10px; }
.team-card { background: #fff; border: 2px solid #002D62; border-radius: 2px; overflow: hidden; cursor: pointer; transition: transform 0.2s, border-color 0.2s; }
.team-card:hover { transform: translateY(-3px); border-color: #BA0C2F; }
.team-card-header { background: #002D62; color: #fff; padding: 10px 12px; border-bottom: 3px solid #BA0C2F; display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.team-card-header h3 { font-size: 14px; font-weight: 800; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.team-card-header .region { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 2px; white-space: nowrap; flex-shrink: 0; }
.team-card-body { padding: 10px 12px; display: flex; gap: 6px; }
.team-card-body .rc { flex: 1; text-align: center; }
.team-card-body .rc .n { font-size: 18px; font-weight: 800; }
.team-card-body .rc .l { font-size: 10px; color: #888; font-weight: 700; }

/* 경기 카드 */
.game { background: #fff; border: 2px solid #002D62; border-radius: 2px; padding: 12px 13px; margin-bottom: 8px; cursor: pointer; transition: border-color 0.15s; }
.game:hover { border-color: #BA0C2F; }
/* 상단: 대회명 + 단계 칩 */
.game .gc-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 12px; }
.game .comp { font-size: 11.5px; font-weight: 700; color: #002D62; line-height: 1.35; }
.game .stage { font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 2px; white-space: nowrap; flex-shrink: 0; }
.game .stage.league { background: #EEF1F4; color: #44586B; }
.game .stage.cup { background: #FBE9EC; color: #A8344B; }
.game .stage.sched { background: #EEF1F4; color: #9AA0A6; }
/* 점수 한 줄: 학교명 점수 승 : 패 점수 학교명 */
.game .score-line { display: flex; justify-content: center; align-items: center; gap: 14px; flex-wrap: wrap; }
.game .side { display: flex; align-items: center; gap: 10px; }
.game .side .nm { font-size: 16px; font-weight: 600; letter-spacing: 0.5px; }
.game .side .sc { font-size: 20px; font-weight: 800; }
.game .side.win .nm { font-weight: 800; color: #002D62; }
.game .side.win .sc { color: #002D62; }
.game .side.lose .nm { color: #777; }
.game .side.lose .sc { color: #999; }
.game .colon { font-size: 18px; font-weight: 800; color: #BA0C2F; }
.game .meta { font-size: 11px; color: #888; margin-top: 12px; display: flex; justify-content: space-between; gap: 8px; border-top: 1px solid #eee; padding-top: 7px; }
.game .meta .rec-link { color: #BA0C2F; font-weight: 700; white-space: nowrap; }
.rbadge { display: inline-block; font-size: 10px; font-weight: 700; color: #fff; padding: 1px 6px; border-radius: 2px; vertical-align: 1px; }
.r-win { background: #1A7A4C; } .r-lose { background: #C8102E; } .r-draw { background: #9AA0A6; } .r-sched { background: #9AA0A6; } .r-cancel { background: #5C6B7A; }

/* 모달 (선수 현황창과 동일) */
.modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; padding: 40px 20px; overflow-y: auto; }
.modal-overlay.show { display: flex; }
.modal { background: #fff; border-radius: 2px; width: 100%; max-width: 600px; max-height: 85vh; overflow: hidden; border: 2px solid #002D62; display: flex; flex-direction: column; }
.modal-header { background: #002D62; border-bottom: 4px solid #BA0C2F; color: #fff; padding: 18px 20px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.modal-header h2 { font-size: 19px; font-weight: 800; display: flex; align-items: center; gap: 8px; }
.modal-header .region { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 2px; }
.modal-close { width: 34px; height: 34px; border-radius: 50%; border: none; background: rgba(255,255,255,0.2); color: #fff; font-size: 18px; cursor: pointer; flex-shrink: 0; }
.modal-close:hover { background: rgba(255,255,255,0.3); }
.modal-body { padding: 16px; overflow-y: auto; }
.record-summary { display: flex; gap: 6px; margin-bottom: 14px; }
.record-summary .rec { flex: 1; text-align: center; background: #fff; border: 2px solid #002D62; border-radius: 2px; padding: 10px; }
.record-summary .rec .num { font-size: 22px; font-weight: 800; }
.record-summary .rec .lbl { font-size: 11px; font-weight: 700; color: #888; margin-top: 2px; }
.date-group { font-size: 13px; font-weight: 800; color: #BA0C2F; margin: 14px 0 8px; border-left: 4px solid #BA0C2F; padding-left: 8px; }
.date-group:first-child { margin-top: 0; }
.empty { text-align: center; color: #888; padding: 30px 0; font-size: 14px; }

@media (max-width: 768px) {
  .header h1 { font-size: 18px; letter-spacing: 1px; }
  .header .subtitle { font-size: 11px; }
  .header .update-info { font-size: 9px; }
  .refresh-spacer { height: 25px; }
  .container { padding: 10px; }
  .cal-grid { grid-auto-rows: 40px; }
  .cal-day { font-size: 13px; }
  .filters { flex-direction: column; align-items: stretch; }
  .filters input, .filters select { width: 100%; }
  .team-grid { grid-template-columns: repeat(2,1fr); gap: 8px; }
  .modal-overlay { padding: 16px; }
  .modal { max-height: 90vh; }
  .game .teamrow { font-size: 13px; }
}
</style>
</head>
<body>

<div class="header">
  <h1>KBSA U-18 SCHEDULE</h1>
  <div class="subtitle">__YEAR__ 시즌 18세 이하부 경기 일정 · 결과</div>
  <div class="subtitle" style="margin-top:4px">출처: 대한야구소프트볼협회 (korea-baseball.com)</div>
  <div class="subtitle update-info" style="margin-top:6px">마지막 갱신: __UPDATED__</div>
  <div class="subtitle update-info" style="margin-top:4px">본 앱은 비상업적 목적으로 운영되며, 모든 데이터 권한은 대한야구소프트볼협회에 있습니다.</div>
  <button class="reload-btn" onclick="reloadPage()">&#x21bb; 새로고침</button>
  <button class="install-btn" id="installBtn" onclick="installApp()">&#x1F4F2; 앱 설치</button>
  <div class="refresh-spacer"></div>
  <div class="tabs">
    <a class="tab" href="u18_players.html">선수 현황</a>
    <a class="tab active" href="u18_schedule.html">경기 일정</a>
  </div>
  <div class="viewbar-spacer"></div>
</div>

<div class="viewbar">
  <button class="view-btn active" id="vbMonth" onclick="setView('month')">월별 일정</button>
  <button class="view-btn" id="vbTeam" onclick="setView('team')">학교별</button>
</div>

<div class="container">
  <div id="monthView">
    <div class="month-nav">
      <button class="nav-btn" id="prevMonth" onclick="changeMonth(-1)">‹ 이전</button>
      <span class="cur" id="curMonth"></span>
      <button class="nav-btn" id="nextMonth" onclick="changeMonth(1)">다음 ›</button>
    </div>
    <div class="cal">
      <div class="cal-wd-row">
        <div class="cal-wd sun">일</div><div class="cal-wd">월</div><div class="cal-wd">화</div><div class="cal-wd">수</div><div class="cal-wd">목</div><div class="cal-wd">금</div><div class="cal-wd sat">토</div>
      </div>
      <div class="cal-grid" id="calGrid"></div>
    </div>
  </div>

  <div id="teamView" style="display:none">
    <div class="filters">
      <label>지역</label>
      <select id="regionFilter" onchange="doSchoolSearch()"></select>
      <input type="text" id="teamSearch" placeholder="학교명 검색" onkeydown="if(event.key==='Enter')doSchoolSearch()" autocomplete="off">
      <button class="sbtn" onclick="doSchoolSearch()">검색</button>
      <button class="sbtn clr" onclick="clearSchool()">초기화</button>
      <div class="result-count" id="schoolCount"></div>
    </div>
    <div class="team-grid" id="teamGrid"></div>
  </div>
</div>

<div class="modal-overlay" id="schedModal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-header"><h2 id="modalTitle"></h2><button class="modal-close" onclick="closeModal()">&times;</button></div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>

<script src="u18_schedule_data.js"></script>
<script>
const GAMES = scheduleData.games || [];
const TR = (typeof teamRegionMap!=='undefined') ? teamRegionMap : {};
const BOX_URL = "https://www.korea-baseball.com/game/box_score?game_idx=";
const WD = ['일','월','화','수','목','금','토'];
const regionColors = {
  '서울':['#E6F0FA','#1A5694'],'경기':['#E2F2EE','#137A5E'],'인천':['#E9F5FB','#11688A'],
  '강원':['#E8ECF0','#44586B'],'충북':['#EAF3DE','#4A6D11'],'충남':['#F0F0DC','#6B6410'],
  '세종':['#E1F3EC','#0F7A52'],'대전':['#E6F4E6','#2E7D32'],'경북':['#FBEFD9','#9A6512'],
  '경남':['#FBF0CC','#8A6A0A'],'대구':['#FBEAE0','#99431D'],'부산':['#FBE9EC','#A8344B'],
  '울산':['#FAE8E2','#A03D22'],'전북':['#EFE9F7','#5B3E8E'],'전남':['#F1E9F5','#6E3E84'],
  '광주':['#EBE9F7','#473E8E'],'제주':['#FBEAF0','#9E335E']
};
function regBadge(reg){ if(!reg) return ''; const c=regionColors[reg]||['#E8ECF0','#44586B']; return `<span class="region" style="background:${c[0]};color:${c[1]}">${reg}</span>`; }
function openGame(idx){ window.open(BOX_URL+idx,'_blank'); }
function fmtDateHeader(d){ const dt=new Date(d+'T00:00:00'); return `${dt.getMonth()+1}/${dt.getDate()} (${WD[dt.getDay()]})`; }
function rb(r){ if(r==='승')return '<span class="rbadge r-win">승</span>'; if(r==='패')return '<span class="rbadge r-lose">패</span>'; if(r==='무')return '<span class="rbadge r-draw">무</span>'; return ''; }
// 카드용 짧은 대회명: 맨 앞 연도만 제거 (청룡기·황금사자기 등 이름은 유지)
function shortTitle(t){ return (t||'').replace(/^\s*\d{4}\s*/, '').trim(); }
// 단계 칩 색: 토너먼트(결승/강 등)=cup, 리그/예선=league
function stageCls(rnd){ return /결승|준결|[0-9]+강|왕중왕|플레이오프|토너/.test(rnd||'') ? 'cup' : 'league'; }
function gameCard(g, hideComp){
  const a=g.away,h=g.home;
  const aWin=a.result==='승',hWin=h.result==='승';
  const aCls=aWin?'win':(g.status==='완료'?'lose':''), hCls=hWin?'win':(g.status==='완료'?'lose':'');
  const aScore=a.score===null?'-':a.score,hScore=h.score===null?'-':h.score;
  // hideComp: 모달이 이미 대회명으로 그룹핑된 경우 카드 내 중복 대회명 제거 (단계 칩은 유지)
  const comp=(!hideComp && g.title)?`<span class="comp">${shortTitle(g.title)}</span>`:'<span class="comp"></span>';
  let stage='';
  if(g.round) stage=`<span class="stage ${stageCls(g.round)}">${g.round}</span>`;
  else if(g.status==='예정') stage='<span class="stage sched">예정</span>';
  else if(g.status==='취소') stage='<span class="stage cup">취소</span>';
  const sched=g.status==='예정'?'예정 · ':(g.status==='취소'?'취소 · ':'');
  const metaLeft=sched+[g.time,g.venue].filter(Boolean).join(' · ');
  return `<div class="game" onclick="openGame('${g.game_idx}')">
    <div class="gc-top">${comp}${stage}</div>
    <div class="score-line">
      <span class="side ${aCls}"><span class="nm">${a.name}</span><span class="sc">${aScore}</span>${rb(a.result)}</span>
      <span class="colon">:</span>
      <span class="side ${hCls}">${rb(h.result)}<span class="sc">${hScore}</span><span class="nm">${h.name}</span></span>
    </div>
    <div class="meta"><span>${metaLeft}</span><span class="rec-link">기록 ›</span></div>
  </div>`;
}

/* ===== 모달 ===== */
function openModal(){ document.getElementById('schedModal').classList.add('show'); document.body.style.overflow='hidden'; }
function closeModal(){ document.getElementById('schedModal').classList.remove('show'); document.body.style.overflow=''; document.getElementById('modalBody').scrollTop=0; }
document.addEventListener('keydown', e=>{ if(e.key==='Escape')closeModal(); });

function openDateModal(ds){
  // 대회(전체이름)별로 묶고, 그 안에서 시간순
  const list=GAMES.filter(g=>g.date===ds).sort((x,y)=>
    ((x.title||'').localeCompare(y.title||''))||((x.time||'').localeCompare(y.time||'')));
  document.getElementById('modalTitle').innerHTML=`${fmtDateHeader(ds)} <span style="font-size:13px;opacity:0.8">${list.length}경기</span>`;
  let html='', lastT=null;
  list.forEach(g=>{ const t=g.title||'기타'; if(t!==lastT){ html+=`<div class="date-group">${t}</div>`; lastT=t; } html+=gameCard(g, true); });
  document.getElementById('modalBody').innerHTML=list.length?html:'<div class="empty">경기가 없습니다.</div>';
  openModal();
}

function openTeamModal(name){
  const list=GAMES.filter(g=>g.away.name===name||g.home.name===name)
                  .sort((x,y)=>(y.date+(y.time||'')).localeCompare(x.date+(x.time||'')));
  let w=0,l=0,d=0,played=0;
  list.forEach(g=>{ if(g.status!=='완료')return; played++; const me=g.away.name===name?g.away:g.home;
    if(me.result==='승')w++; else if(me.result==='패')l++; else if(me.result==='무')d++; });
  const reg=TR[name]||'';
  document.getElementById('modalTitle').innerHTML=`${name} ${regBadge(reg)}`;
  let html=`<div class="record-summary">
     <div class="rec"><div class="num" style="color:#002D62">${played}</div><div class="lbl">경기</div></div>
     <div class="rec"><div class="num" style="color:#1A7A4C">${w}</div><div class="lbl">승</div></div>
     <div class="rec"><div class="num" style="color:#C8102E">${l}</div><div class="lbl">패</div></div>
     ${d?`<div class="rec"><div class="num" style="color:#888">${d}</div><div class="lbl">무</div></div>`:''}</div>`;
  let lastDate='';
  list.forEach(g=>{ if(g.date!==lastDate){ html+=`<div class="date-group">${fmtDateHeader(g.date)}</div>`; lastDate=g.date; } html+=gameCard(g); });
  document.getElementById('modalBody').innerHTML=html||'<div class="empty">경기가 없습니다.</div>';
  openModal();
}

/* ===== 월별 달력 ===== */
const months=[...new Set(GAMES.filter(g=>g.date).map(g=>g.date.slice(0,7)))].sort();
let curMonthIdx=0;
function renderCalendar(){
  const ym=months[curMonthIdx];
  document.getElementById('curMonth').textContent=ym?ym.replace('-','. '):'-';
  document.getElementById('prevMonth').disabled=curMonthIdx<=0;
  document.getElementById('nextMonth').disabled=curMonthIdx>=months.length-1;
  const [y,m]=ym.split('-').map(Number);
  const firstWd=new Date(y,m-1,1).getDay(), daysIn=new Date(y,m,0).getDate();
  const counts={}; GAMES.forEach(g=>{ if(g.date&&g.date.slice(0,7)===ym)counts[g.date]=(counts[g.date]||0)+1; });
  let html='';
  for(let i=0;i<firstWd;i++)html+=`<div class="cal-day empty"></div>`;
  for(let dd=1;dd<=daysIn;dd++){
    const ds=`${y}-${String(m).padStart(2,'0')}-${String(dd).padStart(2,'0')}`;
    const n=counts[ds]||0;
    html+= n ? `<div class="cal-day has" onclick="openDateModal('${ds}')">${dd}<span class="cnt">${n}</span></div>`
             : `<div class="cal-day none">${dd}</div>`;
  }
  document.getElementById('calGrid').innerHTML=html;
}
function changeMonth(d){ curMonthIdx=Math.max(0,Math.min(months.length-1,curMonthIdx+d)); renderCalendar(); }

/* ===== 학교별 ===== */
const teams=[...new Set(GAMES.flatMap(g=>[g.away.name,g.home.name]))].filter(Boolean).sort((a,b)=>a.localeCompare(b,'ko'));
const teamRecord={};
teams.forEach(t=>teamRecord[t]={played:0,w:0,l:0});
GAMES.forEach(g=>{ if(g.status!=='완료')return; ['away','home'].forEach(s=>{ const me=g[s]; if(!teamRecord[me.name])return; teamRecord[me.name].played++; if(me.result==='승')teamRecord[me.name].w++; else if(me.result==='패')teamRecord[me.name].l++; }); });

function fillRegions(){
  const regs=[...new Set(teams.map(t=>TR[t]).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'ko'));
  document.getElementById('regionFilter').innerHTML='<option value="">전체</option>'+regs.map(r=>`<option value="${r}">${r}</option>`).join('');
}
function schoolCard(name){
  const reg=TR[name]||''; const r=teamRecord[name]||{played:0,w:0,l:0};
  return `<div class="team-card" onclick="openTeamModal('${name.replace(/'/g,"\\'")}')">
    <div class="team-card-header"><h3>${name}</h3>${regBadge(reg)}</div>
    <div class="team-card-body">
      <div class="rc"><div class="n" style="color:#002D62">${r.played}</div><div class="l">경기</div></div>
      <div class="rc"><div class="n" style="color:#1A7A4C">${r.w}</div><div class="l">승</div></div>
      <div class="rc"><div class="n" style="color:#C8102E">${r.l}</div><div class="l">패</div></div>
    </div></div>`;
}
function doSchoolSearch(){
  const reg=document.getElementById('regionFilter').value;
  const q=document.getElementById('teamSearch').value.trim().toLowerCase();
  let list=teams;
  if(reg) list=list.filter(t=>TR[t]===reg);
  if(q) list=list.filter(t=>t.toLowerCase().includes(q));
  document.getElementById('schoolCount').textContent=`${list.length}개 학교`;
  document.getElementById('teamGrid').innerHTML=list.length?list.map(schoolCard).join(''):'<div class="empty">검색 결과가 없습니다.</div>';
}
function clearSchool(){ document.getElementById('teamSearch').value=''; document.getElementById('regionFilter').value=''; doSchoolSearch(); }

function setView(v){
  document.getElementById('monthView').style.display=v==='month'?'':'none';
  document.getElementById('teamView').style.display=v==='team'?'':'none';
  document.getElementById('vbMonth').classList.toggle('active',v==='month');
  document.getElementById('vbTeam').classList.toggle('active',v==='team');
}

(function init(){
  const today=new Date().toISOString().slice(0,7);
  let idx=months.indexOf(today);
  if(idx<0){ idx=months.findIndex(m=>m>=today); if(idx<0)idx=months.length-1; }
  curMonthIdx=Math.max(0,idx);
  renderCalendar();
  fillRegions();
  doSchoolSearch();
})();

async function reloadPage() {
  try {
    if (window.caches) {
      const ks = await caches.keys();
      for (const k of ks) await caches.delete(k);
    }
    // HTTP 캐시까지 우회해 최신 데이터 파일을 강제로 다시 받음
    await Promise.all(['u18_schedule_data.js', 'u18_schedule.html'].map(
      u => fetch(u, {cache: 'reload'}).catch(() => {})));
  } catch (e) {}
  location.reload();
}

if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js').catch(()=>{}); }

// PWA 설치 버튼: 설치 가능할 때만 노출, 이미 설치(standalone)면 숨김
let deferredPrompt;
window.addEventListener('beforeinstallprompt', function(e){
  e.preventDefault(); deferredPrompt = e;
  document.getElementById('installBtn').style.display = 'inline-block';
});
function installApp(){
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then(function(c){
    if (c.outcome === 'accepted') document.getElementById('installBtn').style.display = 'none';
    deferredPrompt = null;
  });
}
window.addEventListener('appinstalled', function(){ document.getElementById('installBtn').style.display = 'none'; });
if (window.matchMedia('(display-mode: standalone)').matches || navigator.standalone) {
  document.getElementById('installBtn').style.display = 'none';
}
</script>
</body>
</html>"""

HTML = HTML.replace("__YEAR__", str(year)).replace("__UPDATED__", updated)
with open(os.path.join(BASE_DIR, "u18_schedule.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"일정 HTML 생성 완료 ({len(sched['games'])}경기, 팀-지역 {len(team_region)}개)")
