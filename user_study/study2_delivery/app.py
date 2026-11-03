"""User Study 메인 앱 — Streamlit.

Phases (session_state["phase"]):
  gate      : pid 인증
  intro     : 안내 페이지
  tutorial  : 1 ep 튜토리얼 (측정 X)
  trial     : H1 실제 trial (조건별 replay)
  likert    : 조건 종료 시 Likert
  preference: 세션 종료 시 강제 선호
  done      : 감사 페이지
"""
import base64, os, random, time, secrets, string
import streamlit as st


def play_chime():
    """페이지 로드 시 자동으로 벨소리 재생 (HTML5 audio autoplay)."""
    path = os.path.join(os.path.dirname(__file__), "data", "chime.wav")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f'<audio autoplay="true" src="data:audio/wav;base64,{b64}"></audio>',
        unsafe_allow_html=True,
    )

import config
from logger import log
from stimulus import load_pool, assign_h1


st.set_page_config(page_title=config.APP_TITLE, page_icon="🤖", layout="centered")

# 3버튼 (예/아니오/모름) 색상 + 모바일에서 가로 유지
st.markdown("""
<style>
/* 모바일에서도 columns 가로 유지 */
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
[data-testid="column"], [data-testid="stColumn"] { min-width: 0 !important; }

/* 3-버튼 색상: key prefix 로 매칭 (Streamlit 이 st-key-<key> 클래스 부여) */
.stApp [class*="st-key-y_"] button {
    background-color: #43a047 !important; color: #fff !important;
    border: 1px solid #388e3c !important;
}
.stApp [class*="st-key-n_"] button {
    background-color: #e53935 !important; color: #fff !important;
    border: 1px solid #c62828 !important;
}
.stApp [class*="st-key-u_"] button {
    background-color: #9e9e9e !important; color: #fff !important;
    border: 1px solid #757575 !important;
}
.stApp [class*="st-key-y_"] button:hover,
.stApp [class*="st-key-n_"] button:hover,
.stApp [class*="st-key-u_"] button:hover { filter: brightness(1.08); }

/* 라디오 옵션 폰트 크게 */
[data-testid="stRadio"] label p { font-size: 1.15em !important; font-weight: 500 !important; }
</style>
""", unsafe_allow_html=True)


def hide_qa_buttons():
    """비-질문 phase 에서 잔존 Y/N/U 버튼을 CSS 로 강제 은닉."""
    st.markdown("""
    <style>
    [class*="st-key-y_"], [class*="st-key-n_"], [class*="st-key-u_"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


def loading_spinner():
    """대기 화면용 spinning loader (CSS 애니메이션)."""
    st.markdown("""
    <style>
    @keyframes _pcn_spin { from {transform: rotate(0deg);} to {transform: rotate(360deg);} }
    .pcn_loader {
        border: 8px solid #d0e8d1;
        border-top: 8px solid #43a047;
        border-radius: 50%;
        width: 90px; height: 90px;
        animation: _pcn_spin 1s linear infinite;
        margin: 1.5em auto;
    }
    </style>
    <div class="pcn_loader"></div>
    """, unsafe_allow_html=True)


# ---------------- 헬퍼 ----------------
def _new_pid():
    """랜덤 12자 익명 참가자 ID."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(12))


def gate_pid():
    """첫 접속 시 자동 uuid 발급 + URL 업데이트. 세션 안에서 재사용."""
    qp = st.query_params
    pid = qp.get("pid")
    if isinstance(pid, list):
        pid = pid[0] if pid else None
    if not pid:
        pid = _new_pid()
        # URL 에 pid 심어 새로고침·복사 시 세션 유지
        st.query_params["pid"] = pid
    return pid


def init_session():
    if "phase" not in st.session_state:
        st.session_state.phase = "intro"
    if "trial_idx" not in st.session_state:
        st.session_state.trial_idx = 0
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "cond_switched" not in st.session_state:
        # 조건 A→B (또는 B→A) 전환 시 조건별 Likert 삽입 여부
        st.session_state.cond_switched = False
    if "trials" not in st.session_state:
        st.session_state.trials = None
    if "condition_history" not in st.session_state:
        st.session_state.condition_history = []


def top_bar(pid, condition=None, trial_idx=None, total=None, target_img=None):
    with st.container():
        cols = st.columns([2, 1])
        with cols[0]:
            if target_img:
                st.image(target_img, caption="찾고 있는 대상 물체", width=280)
        with cols[1]:
            st.caption(f"참가자: `{pid[:4]}...`")
            if trial_idx is not None and total is not None:
                st.progress((trial_idx) / total, text=f"진행 {trial_idx}/{total}")


# ---------------- Phase: intro ----------------
def render_intro(pid):
    st.title(config.APP_TITLE)
    st.markdown(config.INTRO_TEXT)
    if st.button("동의하고 시작", type="primary", use_container_width=True):
        log(pid, "session_start")
        # Assignment 미리 뽑기
        pool = load_pool()
        st.session_state.trials = assign_h1(pid, pool)
        st.session_state.phase = "tutorial"
        st.rerun()


# ---------------- Phase: tutorial ----------------
def render_tutorial(pid):
    st.title("튜토리얼")
    st.markdown(config.TUTORIAL_TEXT)
    st.info(
        "💡 실제 실험에서 로봇은 세션 방식에 따라 **약 57초 ~ 2분 55초** 탐색 후 사용자에게 질문합니다. "
        "튜토리얼에서는 이 대기 시간을 5초로 짧게 줄였습니다."
    )
    if st.button("튜토리얼 시작", type="primary", use_container_width=True):
        log(pid, "tutorial_start")
        st.session_state.tutorial_started_at = time.time()
        st.session_state.phase = "tutorial_wait"
        st.rerun()


def render_tutorial_wait(pid):
    st.title("로봇이 열심히 탐색 중입니다...")
    st.image("data/tutorial_target.png",
             caption="예시 · 찾고 있는 대상 물체", width=280)
    st.info(
        "실제 실험에서는 예상 소요 시간 범위만 안내됩니다. "
        "지금은 튜토리얼이라 **5초** 로 짧게 진행합니다."
    )
    loading_spinner()
    remaining = 5 - (time.time() - st.session_state.tutorial_started_at)
    if remaining > 0:
        time.sleep(remaining)
    st.session_state.phase = "tutorial_q"
    st.session_state.tutorial_q_shown_at = time.time()
    st.rerun()


def render_tutorial_q(pid):
    st.markdown(
        '<style>[data-testid="stAppViewContainer"] { background-color: #e8f5e9 !important; }</style>',
        unsafe_allow_html=True,
    )
    st.title("튜토리얼 질문")
    st.markdown("### 🔔 로봇이 준비되었습니다!")
    play_chime()
    st.image("data/tutorial_target.png",
             caption="예시 · 찾고 있는 대상 물체", width=280)
    st.markdown("---")
    st.markdown("#### **연습 질문**: 이 **수납장** 은 **갈색** 인가요?")
    st.caption("실제 실험에서도 이렇게 답변하시면 됩니다.")
    cols = st.columns(3)
    if cols[0].button("예", use_container_width=True, key="y_tut"):
        st.session_state.phase = "trial_intro"; st.rerun()
    if cols[1].button("아니오", use_container_width=True, key="n_tut"):
        st.session_state.phase = "trial_intro"; st.rerun()
    if cols[2].button("잘 모르겠음", use_container_width=True, key="u_tut"):
        st.session_state.phase = "trial_intro"; st.rerun()


def render_trial_intro(pid):
    hide_qa_buttons()
    st.title("본 실험 시작")
    st.markdown(
        f"이제 본 실험이 시작됩니다. 총 **{len(st.session_state.trials)}개 세션** 을 진행합니다.\n\n"
        "매 세션마다 로봇이 대상 물체를 찾기 위해 **3개의 예 / 아니오 질문** 을 합니다.\n\n"
        "**대상 물체 이미지는 화면 상단에 항상 표시**됩니다.\n"
        "탐색 중에는 창을 켜두시고 다른 일을 하셔도 되며, 알림 소리 🔔 가 울리면 질문을 확인해주세요."
    )
    if st.button("시작", type="primary", use_container_width=True):
        log(pid, "trials_start")
        st.session_state.phase = "trial_wait"
        st.session_state.trial_started_at = time.time()
        st.session_state.q_idx = 0
        st.rerun()


# ---------------- Phase: trial (H1) ----------------
def current_trial():
    return st.session_state.trials[st.session_state.trial_idx]


def get_target_path(ep):
    # data/target_images/ep<ID>_target.png
    return f"data/target_images/ep{ep['ep_id']}_target.png"


def render_trial_wait(pid):
    """Pre-question 초기 대기 (조건별 시간 다름)."""
    hide_qa_buttons()
    trial = current_trial()
    ep = trial["ep"]
    top_bar(pid, target_img=get_target_path(ep),
            trial_idx=st.session_state.trial_idx, total=len(st.session_state.trials))
    _letter = chr(ord('A') + st.session_state.trial_idx)
    _total  = len(st.session_state.trials)
    st.markdown(
        f'<div style="text-align:center;margin:0.3em 0 0.2em 0;">'
        f'<span style="font-size:5.5em;font-weight:900;letter-spacing:0.05em;">세션 {_letter}</span>'
        f'<div style="font-size:1.05em;opacity:0.65;margin-top:-0.3em;">총 {_total}개 세션 중</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.title("로봇이 열심히 탐색 중입니다...")

    if "wait_target_sec" not in st.session_state:
        if trial["condition"] == "batched":
            wait = random.uniform(config.BATCHED_INIT_MIN_SEC, config.BATCHED_INIT_MAX_SEC)
        else:
            wait = random.uniform(config.INTERLEAVED_INIT_MIN_SEC, config.INTERLEAVED_INIT_MAX_SEC)
        st.session_state.wait_target_sec = wait
        log(pid, "trial_start",
            trial_idx=st.session_state.trial_idx,
            condition=trial["condition"],
            ep_id=ep["ep_id"], n_q=ep["n_binary_q"],
            wait_sec=round(wait, 2))

    hint = (config.BATCHED_WAIT_HINT if trial["condition"] == "batched"
            else config.INTERLEAVED_WAIT_HINT)
    st.markdown(f"## ⏳ 예상 소요 시간: **{hint}**")
    st.markdown(
        '<div style="font-size:2em;font-weight:600;line-height:1.4;'
        'padding:0.8em 1em;background:#e7f3fe;border-left:6px solid #2196f3;'
        'border-radius:6px;margin:0.6em 0;">'
        '<strong>편하게 다른 업무 보시고 천천히 오셔도 됩니다.</strong><br>'
        '준비되면 화면에서 알림음 (🔔) 이 울립니다.'
        '</div>',
        unsafe_allow_html=True,
    )
    loading_spinner()
    remaining = st.session_state.wait_target_sec - (time.time() - st.session_state.trial_started_at)
    if remaining > 0:
        time.sleep(remaining)
    st.session_state.phase = "trial_question"
    st.session_state.q_idx = 0
    st.session_state.q_shown_at = time.time()
    del st.session_state.wait_target_sec
    st.rerun()


def render_trial_question(pid):
    # 질문 페이지 파스텔 초록 배경 (탐색 완료 상태 시각화)
    st.markdown(
        '<style>[data-testid="stAppViewContainer"] { background-color: #e8f5e9 !important; }</style>',
        unsafe_allow_html=True,
    )
    trial = current_trial()
    ep = trial["ep"]
    top_bar(pid, target_img=get_target_path(ep),
            trial_idx=st.session_state.trial_idx, total=len(st.session_state.trials))
    _letter = chr(ord('A') + st.session_state.trial_idx)
    _total  = len(st.session_state.trials)
    st.markdown(
        f'<div style="text-align:center;margin:0.2em 0 0.1em 0;">'
        f'<span style="font-size:4em;font-weight:900;letter-spacing:0.05em;">세션 {_letter}</span>'
        f'<div style="font-size:0.9em;opacity:0.6;">총 {_total}개 세션 중</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    q = ep["binary_qs"][st.session_state.q_idx]

    # 매 질문마다 알림음 (batched/interleaved 모두)
    st.markdown("### 🔔 로봇이 질문합니다")
    play_chime()

    cat_ko = ep.get("category_ko", ep["category"])
    prop_ko = q.get("prop_ko", q["prop"])
    st.markdown(f"#### 이 **{cat_ko}**, {prop_ko}")
    st.caption(f"세션 {st.session_state.trial_idx + 1} / {len(st.session_state.trials)} · "
               f"질문 {st.session_state.q_idx + 1} / {len(ep['binary_qs'])}")

    if "q_shown_at" not in st.session_state:
        st.session_state.q_shown_at = time.time()
    log_shown_key = f"logged_shown_{st.session_state.trial_idx}_{st.session_state.q_idx}"
    if not st.session_state.get(log_shown_key):
        log(pid, "question_shown",
            trial_idx=st.session_state.trial_idx,
            q_idx=st.session_state.q_idx,
            condition=trial["condition"],
            ep_id=ep["ep_id"], property=q["prop"])
        st.session_state[log_shown_key] = True

    cols = st.columns(3)
    picked = None
    tk = f"{st.session_state.trial_idx}_{st.session_state.q_idx}"
    if cols[0].button("예", use_container_width=True, key=f"y_{tk}"):
        picked = "Yes"
    if cols[1].button("아니오", use_container_width=True, key=f"n_{tk}"):
        picked = "No"
    if cols[2].button("잘 모르겠음", use_container_width=True, key=f"u_{tk}"):
        picked = "Unclear"

    if picked:
        rt = time.time() - st.session_state.q_shown_at
        log(pid, "response_submitted",
            trial_idx=st.session_state.trial_idx,
            q_idx=st.session_state.q_idx,
            condition=trial["condition"],
            ep_id=ep["ep_id"], property=q["prop"],
            response=picked, response_time_sec=round(rt, 3))
        st.session_state.q_idx += 1
        # 다음 질문 or 다음 trial
        if st.session_state.q_idx < len(ep["binary_qs"]):
            st.session_state.phase = "trial_gap"
            st.session_state.gap_started_at = time.time()
            if trial["condition"] == "interleaved":
                st.session_state.gap_target = random.uniform(
                    config.INTERLEAVED_GAP_MIN_SEC, config.INTERLEAVED_GAP_MAX_SEC
                )
            else:
                st.session_state.gap_target = random.uniform(
                    config.BATCHED_GAP_MIN_SEC, config.BATCHED_GAP_MAX_SEC
                )
        else:
            log(pid, "trial_done",
                trial_idx=st.session_state.trial_idx,
                condition=trial["condition"], ep_id=ep["ep_id"])
            st.session_state.condition_history.append(trial["condition"])
            next_idx = st.session_state.trial_idx + 1
            if next_idx < len(st.session_state.trials):
                st.session_state.phase = "between_trials"
            else:
                st.session_state.phase = "preference"
        st.rerun()


def render_between_trials(pid):
    """세션 간 쉼 페이지 — 다음 세션 시작 버튼."""
    hide_qa_buttons()
    done_idx = st.session_state.trial_idx  # 방금 끝난 세션 index
    next_idx = done_idx + 1
    total    = len(st.session_state.trials)
    done_letter = chr(ord('A') + done_idx)
    next_letter = chr(ord('A') + next_idx)
    st.markdown(
        f'<div style="text-align:center;margin:0.5em 0;">'
        f'<div style="font-size:2em;">✅</div>'
        f'<span style="font-size:5em;font-weight:900;letter-spacing:0.05em;">세션 {done_letter}</span>'
        f'<div style="font-size:1.5em;font-weight:600;margin-top:0.2em;">완료</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"### 총 {total}개 세션 중 **{done_idx + 1}개** 완료")
    st.info(
        f"이제 **세션 {next_letter}** 가 시작됩니다. "
        "새 대상 물체에 대해 로봇이 다시 탐색 후 질문합니다.\n\n"
        "잠깐 쉬셔도 되고, 준비되시면 아래 버튼을 눌러주세요."
    )
    if st.button(f"세션 {next_letter} 시작", type="primary", use_container_width=True,
                 key="start_next_trial"):
        st.session_state.trial_idx = next_idx
        st.session_state.trial_started_at = time.time()
        st.session_state.q_idx = 0
        st.session_state.phase = "trial_wait"
        st.rerun()


def render_trial_gap(pid):
    hide_qa_buttons()
    trial = current_trial()
    ep = trial["ep"]
    top_bar(pid, target_img=get_target_path(ep),
            trial_idx=st.session_state.trial_idx, total=len(st.session_state.trials))
    _letter = chr(ord('A') + st.session_state.trial_idx)
    _total  = len(st.session_state.trials)
    st.markdown(
        f'<div style="text-align:center;margin:0.2em 0 0.1em 0;">'
        f'<span style="font-size:4em;font-weight:900;letter-spacing:0.05em;">세션 {_letter}</span>'
        f'<div style="font-size:0.9em;opacity:0.6;">총 {_total}개 세션 중</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if trial["condition"] == "interleaved":
        st.title("로봇이 다시 열심히 탐색 중입니다...")
        st.markdown(f"## ⏳ 예상 소요 시간: **{config.INTERLEAVED_GAP_HINT}**")
        st.markdown(
            '<div style="font-size:2em;font-weight:600;line-height:1.4;'
            'padding:0.8em 1em;background:#e7f3fe;border-left:6px solid #2196f3;'
            'border-radius:6px;margin:0.6em 0;">'
            '<strong>편하게 다른 업무 보시고 천천히 오셔도 됩니다.</strong><br>'
            '화면에서 알림음 (🔔) 과 함께 다음 질문이 나타납니다.'
            '</div>',
            unsafe_allow_html=True,
        )
        loading_spinner()
    else:
        st.title("다음 질문 준비 중...")
        st.markdown(f"## ⏳ 예상 소요 시간: **{config.BATCHED_GAP_HINT}**")
        loading_spinner()
    remaining = st.session_state.gap_target - (time.time() - st.session_state.gap_started_at)
    if remaining > 0:
        time.sleep(remaining)
    st.session_state.phase = "trial_question"
    st.session_state.q_shown_at = time.time()
    st.rerun()


# ---------------- Phase: preference (final) ----------------
def render_preference(pid):
    hide_qa_buttons()
    # 선지 라디오 폰트 크게 (preference 페이지 전용)
    st.markdown("""
    <style>
    [data-testid="stRadio"] label p { font-size: 1.7em !important; font-weight: 500 !important; line-height: 1.5 !important; }
    </style>
    """, unsafe_allow_html=True)
    st.title("마지막 질문")
    # 안내 문구 — 2배 크기, 검정색
    st.markdown(
        '<p style="font-size: 1.7em; color: #000; font-weight: 500; margin: 0.5em 0 1em 0;">'
        '두 방식 모두 경험하셨습니다. 반드시 하나를 선택해주세요.'
        '</p>',
        unsafe_allow_html=True,
    )

    trials = st.session_state.trials
    trial1_cond = trials[0]["condition"]
    trial2_cond = trials[1]["condition"]
    # 참가자 recall aid: 어느 세션이 어떤 방식이었는지 짧게 상기
    st.markdown("---")
    st.markdown(
        f'<div style="font-size:1.1em;line-height:1.6;padding:0.8em 1em;'
        f'background:#f5f5f5;border-radius:6px;margin:0.6em 0;">'
        f'· <b>세션 A</b>: {config.COND_STYLE_KO[trial1_cond]}<br>'
        f'· <b>세션 B</b>: {config.COND_STYLE_KO[trial2_cond]}'
        f'</div>',
        unsafe_allow_html=True,
    )
    ordinal_labels = {trial1_cond: "세션 A", trial2_cond: "세션 B"}
    opts = [trial1_cond, trial2_cond]

    st.markdown(f"##### {config.PREFERENCE_Q1}")
    choice = st.radio(
        "선택", options=opts,
        format_func=lambda k: ordinal_labels[k],
        index=None, label_visibility="collapsed",
    )

    if st.button("제출", type="primary", use_container_width=True,
                 disabled=(choice is None), key="pref_submit"):
        # log 에는 조건명 + 세션 순서 함께 저장
        preferred_ordinal = 1 if choice == trial1_cond else 2
        log(pid, "preference_submitted",
            preference=choice,
            preference_q1=choice,
            preference_q1_text=config.PREFERENCE_Q1,
            preferred_session_ordinal=preferred_ordinal,
            trial1_condition=trial1_cond,
            trial2_condition=trial2_cond)
        log(pid, "session_done")
        st.session_state.phase = "done"
        st.rerun()


# ---------------- Phase: done ----------------
def render_done(pid):
    st.title("완료")
    st.markdown(config.DONE_TEXT)


# ---------------- Router ----------------
def main():
    pid = gate_pid()
    init_session()
    p = st.session_state.phase
    # 페이지 슬롯: 이전 phase 렌더링을 원자적으로 교체 (잔상 방지)
    slot = st.empty()
    with slot.container():
        if p == "intro":            render_intro(pid)
        elif p == "tutorial":       render_tutorial(pid)
        elif p == "tutorial_wait":  render_tutorial_wait(pid)
        elif p == "tutorial_q":     render_tutorial_q(pid)
        elif p == "trial_intro":    render_trial_intro(pid)
        elif p == "trial_wait":     render_trial_wait(pid)
        elif p == "trial_question": render_trial_question(pid)
        elif p == "trial_gap":      render_trial_gap(pid)
        elif p == "between_trials": render_between_trials(pid)
        elif p == "preference":     render_preference(pid)
        elif p == "done":           render_done(pid)
        else:
            st.error(f"알 수 없는 phase: {p}")


if __name__ == "__main__":
    main()
