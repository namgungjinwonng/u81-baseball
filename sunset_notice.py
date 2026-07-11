# 서비스 종료(2026-07-31) 안내 팝업 스니펫 — generate_html.py / generate_schedule.py 공용.
# </body> 직전에 삽입한다. 오늘 하루 보지 않기 = localStorage 'u18SunsetHideDate'.
# 2026-08-01(KST)부터는 닫을 수 없는 차단 화면으로 전환(안내만 표시).
# 차단 화면 미리보기: URL 에 ?sunset_ended=1 을 붙이면 날짜와 무관하게 강제 표시.

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
/* 앱 이름 강조: 볼드 + 본문보다 1pt 크게 + 블랙 */
#sunsetCard .body b.app { color: #000; font-size: 15px; font-weight: 800; }
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
#sunsetCard button.go { border: 0; cursor: pointer; font-family: inherit; }
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
#sunsetCard .del-note { font-size: 13px; color: #222; margin-top: 12px; padding: 10px 12px; background: #F4F6F8; border-radius: 2px; }
/* 종료일 이후: 닫기 불가 차단 화면 — 푸터(닫기/오늘 하루 보지 않기) 숨김 */
#sunsetOverlay.sunset-ended .foot { display: none; }
#sunsetOverlay.sunset-ended #sunsetCard { border-color: #BA0C2F; }
</style>
<div id="sunsetOverlay">
    <div id="sunsetCard" role="alertdialog" aria-label="서비스 종료 및 통합 안내">
        <div class="head">[서비스 종료 및 통합 안내]</div>
        <div class="body">
            <div id="sunsetMsgPre">
                안녕하세요, <b class="app">__MERGE_NAME__</b>을(를) 이용해 주셔서 감사합니다.<br>
                <b class="app">__MERGE_NAME__</b> 서비스가 <b>__SUNSET_DATE__</b>부로 종료될 예정입니다.<br><br>
                지속적인 서비스 이용을 위해 새로워진 <b class="app">__BASE_NAME__</b>을(를) 설치하여 이용해 주시기 바랍니다.
                기존에 이용하시던 서비스는 <b class="app">__BASE_NAME__</b>에서 더욱 편리하게 이어 나가실 수 있습니다.
            </div>
            <div id="sunsetMsgEnded" style="display:none">
                <b class="app">__MERGE_NAME__</b> 서비스가 <b>__SUNSET_DATE__</b>부로 종료되었습니다.<br>
                그동안 이용해 주셔서 감사합니다.<br><br>
                새로워진 <b class="app">__BASE_NAME__</b>에서 서비스를 계속 이용하실 수 있습니다.
            </div>
            <div class="date">서비스 종료일: __SUNSET_DATE__</div>
            <button class="go" type="button" onclick="openBaseInstall()">__BASE_NAME__ 설치하러 가기</button>
            <div class="inapp-note" id="sunsetOpenResult" role="status"></div>
            <div class="del-note">※ <b class="app">__BASE_NAME__</b> 설치 후, 기존 <b class="app">__MERGE_NAME__</b> 앱은 홈 화면에서 아이콘을 길게 눌러 직접 삭제해 주세요.</div>
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
    var BASE_URL = '__BASE_URL__';
    function copyBaseUrl() {
        var done = function () {
            document.getElementById('sunsetOpenResult').textContent = '설치 주소를 복사했습니다. Safari 주소창에 붙여넣어 열어 주세요.';
        };
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(BASE_URL).then(done).catch(copyFallback);
        } else {
            copyFallback();
        }
        function copyFallback() {
            var input = document.createElement('textarea');
            input.value = BASE_URL;
            input.setAttribute('readonly', '');
            input.style.position = 'fixed'; input.style.opacity = '0';
            document.body.appendChild(input); input.select();
            try { document.execCommand('copy'); done(); }
            catch (e) { document.getElementById('sunsetOpenResult').textContent = 'Safari에서 다음 주소를 열어 주세요: ' + BASE_URL; }
            document.body.removeChild(input);
        }
    }
    window.openBaseInstall = function () {
        var ua = navigator.userAgent || '';
        if (/Android/i.test(ua)) {
            var path = BASE_URL.replace(/^https?:\/\//, '');
            location.href = 'intent://' + path + '#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url=' + encodeURIComponent(BASE_URL) + ';end';
            return;
        }
        if (/iPad|iPhone|iPod/i.test(ua)) {
            copyBaseUrl();
            return;
        }
        window.open(BASE_URL, '_blank', 'noopener');
    };
    // 2026-08-01 00:00 KST 부터 차단 화면 (닫기 불가, 안내만). ?sunset_ended=1 = 미리보기.
    var ended = Date.now() >= new Date('2026-08-01T00:00:00+09:00').getTime()
        || /[?&]sunset_ended=1/.test(location.search);
    var overlay = document.getElementById('sunsetOverlay');
    if (ended) {
        document.getElementById('sunsetMsgPre').style.display = 'none';
        document.getElementById('sunsetMsgEnded').style.display = 'block';
        overlay.classList.add('show', 'sunset-ended');
        document.body.style.overflow = 'hidden'; // 뒤 화면 스크롤 차단
        return;
    }
    var hidden = null;
    try { hidden = localStorage.getItem(KEY); } catch (e) {}
    if (hidden !== today()) {
        overlay.classList.add('show');
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
