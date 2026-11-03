/**
 * ProCompNav User Study — Data Ingestion Webhook
 *
 * 이 스크립트를 Google Sheets 의 Apps Script 에 붙여넣고 Web App 으로 배포하면,
 * Streamlit 앱이 매 응답을 이 URL 로 POST → Sheet 에 자동 append.
 *
 * === 세팅 절차 (약 5분) ===
 *
 * 1) 새 Google Sheets 생성.
 * 2) 상단 메뉴 Extensions → Apps Script 클릭.
 * 3) 열린 편집기의 코드를 전부 지우고 이 파일 전체 내용 붙여넣기.
 * 4) 저장 (Ctrl+S).
 * 5) 우측 상단 "Deploy" → "New deployment" 클릭.
 * 6) 톱니바퀴(Type) → "Web app" 선택.
 * 7) 아래 항목 설정:
 *      Description  : ProCompNav user study
 *      Execute as   : Me (본인 계정)
 *      Who has access: Anyone
 * 8) "Deploy" 클릭 → 권한 요청 승인 → "Web app URL" 복사.
 *    (URL 예: https://script.google.com/macros/s/AKfyc.../exec)
 *
 * 9) 복사한 URL 을 Streamlit Cloud secrets 에 추가:
 *      [webhook]
 *      url = "https://script.google.com/macros/s/AKfyc.../exec"
 *
 * 그러면 앱이 응답마다 자동으로 이 sheet 에 새 행을 append 합니다.
 */

// H1 + H2 통합 컬럼 세트
var COLUMNS = [
  "ts", "pid", "experiment", "event",
  // H1 trial-level + H2 session-level
  "trial_idx", "q_idx", "condition", "ep_id",
  // 질문/응답
  "property", "question_en", "question_ko",
  "response", "response_text", "response_length_chars", "response_time_sec",
  "n_q", "wait_sec",
  // H1 Likert (사용 안 함이지만 스키마 호환)
  "likert_score", "likert_question",
  // H1 최종 preference
  "preference", "preferred_session_ordinal",
  "trial1_condition", "trial2_condition",
  // H2 5-set 관련
  "set_idx", "session_letter",
  "preference_letter", "preference_condition",
  "session_A_condition", "session_B_condition",
  "raw_json"
];

function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    // 헤더가 없으면 자동 생성 (첫 실행)
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(COLUMNS);
    }

    var row = COLUMNS.map(function (col) {
      if (col === "raw_json") return JSON.stringify(payload);
      var v = payload[col];
      return (v === undefined || v === null) ? "" : v;
    });
    sheet.appendRow(row);

    return ContentService.createTextOutput(JSON.stringify({ok: true}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ok: false, err: String(err)}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// 브라우저에서 URL 접속 시 살아있는지 확인용
function doGet() {
  return ContentService.createTextOutput("alive");
}
