"""응답 로거 — Google Apps Script webhook (기본) + 로컬 SQLite fallback.

Webhook POST 는 백그라운드 daemon thread 에서 fire-and-forget → 버튼 클릭 → rerun 사이
네트워크 대기 없음. 실패는 stderr 로만 확인.
"""
import json, os, sqlite3, threading, time
from datetime import datetime, timezone, timedelta
import urllib.request, urllib.error

KST = timezone(timedelta(hours=9))

try:
    import streamlit as st
except Exception:
    st = None


def _get_webhook_url():
    """secrets.toml 의 [webhook] url 이 우선, 없으면 config.DATA_WEBHOOK_URL."""
    if st is not None:
        try:
            return st.secrets["webhook"]["url"]
        except Exception:
            pass
    import config
    return config.DATA_WEBHOOK_URL


def _post_webhook_sync(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        print(f"[logger] webhook post failed: {e}")
        return False


def _post_webhook_async(url, payload):
    """백그라운드 스레드로 fire-and-forget POST. UI 는 대기하지 않음."""
    t = threading.Thread(
        target=_post_webhook_sync,
        args=(url, payload),
        daemon=True,
    )
    t.start()


def _write_sqlite(payload):
    import config
    db_path = config.LOCAL_FALLBACK_SQLITE
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            ts TEXT, pid TEXT, event TEXT, payload TEXT
        )
    """)
    con.execute(
        "INSERT INTO responses VALUES (?,?,?,?)",
        (payload.get("ts"), payload.get("pid"), payload.get("event"), json.dumps(payload)),
    )
    con.commit()
    con.close()


def log(pid: str, event: str, **fields):
    """모든 로그 이벤트의 유일한 진입점.

    event 종류:
      session_start, tutorial_done, trial_start, question_shown,
      response_submitted, trial_done, likert_submitted, preference_submitted,
      session_done
    """
    payload = {
        "ts":    datetime.now(KST).isoformat(),
        "pid":   pid,
        "event": event,
        **fields,
    }
    url = _get_webhook_url()
    if url:
        # non-blocking: 성공/실패 여부는 stderr 로만
        _post_webhook_async(url, payload)
    else:
        # URL 없으면 로컬 SQLite (컨테이너 재시작 시 소실됨을 유의)
        _write_sqlite(payload)
    return payload
