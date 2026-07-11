# 서비스 종료(2026-07-31) 안내 팝업 스니펫 — generate_html.py / generate_schedule.py 공용.
# </body> 직전에 삽입한다. 오늘 하루 보지 않기 = localStorage 'u18SunsetHideDate'.

BASE_APP_NAME = "U-18 Player Stats"
BASE_APP_URL = "https://namgungjinwonng.github.io/U18-baseball-player-Stats/"
MERGE_APP_NAME = "U-18 Roster"
SUNSET_DATE = "2026년 7월 31일"

SUNSET_HTML = """
<!-- 서비스 종료 안내 팝업 -->
<style>
#sunsetOverlay {
    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.55); z-index: 10000;
    justify-content: center; align-items: center; padding: 24px 16px;
}
#sunsetOverlay.show { display: flex; }
#sunsetCard {
    background: #fff; width: 100%; max-width: 420px; border-radius: 2px;
    border: 2px solid #002D62; overflow: hidden;
}
#sunsetCard .head {
    background: #002D62; border-bottom: 4px solid #BA0C2F; color: #fff;
    padding: 16px 20px; font-size: 17px; font-weight: 800;
}
#sunsetCard .body { padding: 20px; font-size: 14px; line-height: 1.65; color: #222; }
#sunsetCard .body b { color: #002D62; }
#sunsetCard .date {
    margin: 14px 0; padding: 10px 12px; background: #F4F6F8; border-left: 3px solid #BA0C2F;
    font-weight: 700; font-size: 14px;
}
#sunsetCard .go {
    display: block; width: 100%; box-sizing: border-box; text-align: center;
    background: #002D62; color: #fff; text-decoration: none; font-weight: 800;
    font-size: 15px; padding: 13px 0; border-radius: 2px; margin-top: 4px;
}
#sunsetCard .go:active { background: #001f45; }
#sunsetCard .foot {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 20px 16px; font-size: 13px; color: #555;
}
#sunsetCard .foot label { display: flex; align-items: center; gap: 6px; cursor: pointer; }
#sunsetCard .foot button {
    border: 1px solid #ccc; background: #fff; padding: 7px 16px; font-size: 13px;
    border-radius: 2px; cursor: pointer;
}
#sunsetCard .inapp-note { font-size: 12px; color: #777; margin-top: 10px; }
</style>
<div id="sunsetOverlay">
    <div id="sunsetCard" role="alertdialog" aria-label="서비스 종료 및 통합 안내">
        <div class="head">[서비스 종료 및 통합 안내]</div>
        <div class="body">
            안녕하세요, <b>__MERGE_NAME__</b>을(를) 이용해 주셔서 감사합니다.<br>
            <b>__MERGE_NAME__</b> 서비스가 <b>__SUNSET_DATE__</b>부로 종료될 예정입니다.<br><br>
            지속적인 서비스 이용을 위해 새로워진 <b>__BASE_NAME__</b>을(를) 설치하여 이용해 주시기 바랍니다.
            기존에 이용하시던 서비스는 <b>__BASE_NAME__</b>에서 더욱 편리하게 이어 나가실 수 있습니다.
            <div class="date">서비스 종료일: __SUNSET_DATE__</div>
            <a class="go" href="__BASE_URL__" target="_blank" rel="noopener">__BASE_NAME__ 설치하러 가기</a>
            <div class="inapp-note">※ 카카오톡·네이버 등 인앱 브라우저에서는 앱 설치가 불가하니, Chrome/Safari 등 기본 브라우저로 열어 설치해 주세요.</div>
        </div>
        <div class="foot">
            <label><input type="checkbox" id="sunsetHideToday"> 오늘 하루 보지 않기</label>
            <button type="button" onclick="closeSunsetNotice()">닫기</button>
        </div>
    </div>
</div>
<script>
(function () {
    var KEY = 'u18SunsetHideDate';
    function today() {
        var d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }
    window.closeSunsetNotice = function () {
        if (document.getElementById('sunsetHideToday').checked) {
            try { localStorage.setItem(KEY, today()); } catch (e) {}
        }
        document.getElementById('sunsetOverlay').classList.remove('show');
    };
    var hidden = null;
    try { hidden = localStorage.getItem(KEY); } catch (e) {}
    if (hidden !== today()) {
        document.getElementById('sunsetOverlay').classList.add('show');
    }
})();
</script>
"""

SUNSET_HTML = (
    SUNSET_HTML
    .replace("__MERGE_NAME__", MERGE_APP_NAME)
    .replace("__BASE_NAME__", BASE_APP_NAME)
    .replace("__BASE_URL__", BASE_APP_URL)
    .replace("__SUNSET_DATE__", SUNSET_DATE)
)
