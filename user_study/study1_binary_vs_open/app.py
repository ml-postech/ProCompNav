"""User Study H2 App — 5 sets × (session A + session B + set preference).

Phases:
  intro              : 안내
  tutorial           : 튜토리얼 안내
  tutorial_q         : 튜토리얼 예시 질문 (binary 버튼 시연)
  trial_intro        : 본 실험 시작
  session_question   : 현재 set 의 현재 session (A/B) 질문 (binary 버튼 or open text)
  session_gap        : 질문 사이 gap (~5s)
  session_transition : 세션 A → B 사이 (버튼 클릭)
  set_preference     : 현재 세트 종료 후 A vs B 선호
  set_gap            : 세트 사이 5s wait ("다음 세트 준비 중...")
  done               : 감사 페이지
"""
import os, random, time, secrets, string
import streamlit as st

import config
from logger import log
from stimulus import load_pool, assign_h2


st.set_page_config(page_title=config.APP_TITLE, page_icon="🤖", layout="centered")

# 3버튼 색상 + 모바일 가로 유지 + 라디오 폰트 크게 (H1 CSS 재사용)
st.markdown("""
<style>
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
[data-testid="column"], [data-testid="stColumn"] { min-width: 0 !important; }

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

[data-testid="stRadio"] label p { font-size: 1.15em !important; font-weight: 500 !important; }
</style>
""", unsafe_allow_html=True)


def hide_qa_buttons():
    """비-질문 phase 에서 Y/N/U 버튼 잔상 강제 은닉."""
    st.markdown("""
    <style>
    [class*="st-key-y_"], [class*="st-key-n_"], [class*="st-key-u_"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


def loading_spinner():
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
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(12))


def gate_pid():
    qp = st.query_params
    pid = qp.get("pid")
    if isinstance(pid, list):
        pid = pid[0] if pid else None
    if not pid:
        pid = _new_pid()
        st.query_params["pid"] = pid
    return pid


def init_session():
    # Stale schema 방어: intro 아닌데 sets 미채워졌으면 (이전 버전 상태) 전체 리셋
    phase = st.session_state.get("phase")
    sets_present = st.session_state.get("sets") is not None
    if phase and phase != "intro" and not sets_present:
        for k in list(st.session_state.keys()):
            del st.session_state[k]
    if "phase" not in st.session_state:
        st.session_state.phase = "intro"
    if "set_idx" not in st.session_state:
        st.session_state.set_idx = 0
    if "session_letter" not in st.session_state:
        st.session_state.session_letter = "A"
    if "q_idx" not in st.session_state:
        st.session_state.q_idx = 0
    if "sets" not in st.session_state:
        st.session_state.sets = None


def get_target_path(ep):
    return f"data/{ep['target_img']}"


def top_bar(pid, target_img=None):
    with st.container():
        cols = st.columns([2, 1])
        with cols[0]:
            if target_img:
                st.image(target_img, caption="찾고 있는 대상 물체", width=280)
        with cols[1]:
            st.caption(f"참가자: `{pid[:4]}...`")


def current_set():
    return st.session_state.sets[st.session_state.set_idx]


def current_session():
    s = current_set()
    return s["session_A"] if st.session_state.session_letter == "A" else s["session_B"]


def big_session_label(set_display, n_sets, letter, size_em=4):
    st.markdown(
        f'<div style="text-align:center;margin:0.2em 0;">'
        f'<span style="font-size:{size_em}em;font-weight:900;letter-spacing:0.05em;">세션 {letter}</span>'
        f'<div style="font-size:0.9em;opacity:0.65;">세트 {set_display} / {n_sets}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------- Phase: intro ----------------
def render_intro(pid):
    hide_qa_buttons()
    st.title(config.APP_TITLE)
    st.markdown(config.INTRO_TEXT)
    if st.button("동의하고 시작", type="primary", use_container_width=True):
        log(pid, "session_start", experiment="H2")
        pool = load_pool()
        st.session_state.sets = assign_h2(pid, pool)
        st.session_state.phase = "tutorial"
        st.rerun()


# ---------------- Phase: tutorial ----------------
def render_tutorial(pid):
    hide_qa_buttons()
    st.title("튜토리얼")
    st.markdown(config.TUTORIAL_TEXT)
    if st.button("튜토리얼 시작", type="primary", use_container_width=True):
        log(pid, "tutorial_start", experiment="H2")
        st.session_state.phase = "tutorial_q"
        st.rerun()


def _render_tutorial_page(page_num, condition, next_phase):
    """튜토리얼 페이지 렌더링 (조건에 따라 binary or open UI)."""
    st.markdown(
        '<style>[data-testid="stAppViewContainer"] { background-color: #e8f5e9 !important; }</style>',
        unsafe_allow_html=True,
    )
    st.title(f"튜토리얼 질문 ({page_num}/2)")
    st.image(f"data/{config.TUTORIAL_TARGET_IMG}",
             caption="예시 · 찾고 있는 대상 물체", width=280)
    st.markdown("---")
    if condition == "binary":
        st.markdown(
            f"#### **연습 질문**: 이 **{config.TUTORIAL_CAT_KO}**, **{config.TUTORIAL_BINARY_QUESTION_KO}**"
        )
        st.caption("아래 세 버튼 중 하나를 눌러 답변해주세요.")
        cols = st.columns(3)
        if cols[0].button("예", use_container_width=True, key=f"y_tut{page_num}"):
            st.session_state.phase = next_phase; st.rerun()
        if cols[1].button("아니오", use_container_width=True, key=f"n_tut{page_num}"):
            st.session_state.phase = next_phase; st.rerun()
        if cols[2].button("잘 모르겠음", use_container_width=True, key=f"u_tut{page_num}"):
            st.session_state.phase = next_phase; st.rerun()
    else:  # open
        st.markdown(f"#### **연습 질문**: {config.TUTORIAL_OPEN_QUESTION_KO}")
        st.caption("아래 입력창에 답변 (1자 이상) 을 입력한 후 제출해주세요.")
        answer = st.text_input(
            "답변",
            placeholder="답변을 입력해주세요...",
            key=f"tut{page_num}_answer",
        )
        disabled = (not answer) or (len(answer.strip()) < config.MIN_RESPONSE_CHARS)
        if st.button("제출", type="primary", use_container_width=True,
                     disabled=disabled, key=f"tut{page_num}_submit"):
            st.session_state.phase = next_phase; st.rerun()


def render_tutorial_q(pid):
    """튜토리얼 1페이지: 참가자의 세션 A 조건에 맞는 UI 시연."""
    a_cond = st.session_state.sets[0]["session_A"]["condition"]
    _render_tutorial_page(page_num=1, condition=a_cond, next_phase="tutorial_q2")


def render_tutorial_q2(pid):
    """튜토리얼 2페이지: 참가자의 세션 B 조건에 맞는 UI 시연."""
    b_cond = st.session_state.sets[0]["session_B"]["condition"]
    _render_tutorial_page(page_num=2, condition=b_cond, next_phase="trial_intro")


# ---------------- Phase: trial_intro ----------------
def render_trial_intro(pid):
    hide_qa_buttons()
    st.title("본 실험 시작")
    st.markdown(
        f"이제 본 실험이 시작됩니다. 총 **{config.SETS_PER_PARTICIPANT_H2}개 세트** 를 진행합니다.\n\n"
        "각 세트는 다음 순서로 진행됩니다:\n"
        "1. **세션 A** — 대상 물체에 대해 여러 질문에 답변\n"
        "2. **세션 B** — 같은 대상 물체에 대해 다른 방식으로 답변\n"
        "3. 어느 방식이 더 편했는지 선택\n\n"
        "**대상 물체 이미지는 화면 상단에 항상 표시**됩니다."
    )
    if st.button("시작", type="primary", use_container_width=True):
        log(pid, "trials_start", experiment="H2")
        st.session_state.set_idx = 0
        st.session_state.session_letter = "A"
        st.session_state.q_idx = 0
        st.session_state.q_shown_at = time.time()
        st.session_state.phase = "session_question"
        st.rerun()


# ---------------- Phase: session_question ----------------
def _n_q_for(sess):
    ep = sess["ep"]
    return len(ep["binary_qs"]) if sess["condition"] == "binary" else len(ep["open_qs"])


def render_session_question(pid):
    st.markdown(
        '<style>[data-testid="stAppViewContainer"] { background-color: #e8f5e9 !important; }</style>',
        unsafe_allow_html=True,
    )
    sess = current_session()
    ep = sess["ep"]
    condition = sess["condition"]
    top_bar(pid, target_img=get_target_path(ep))
    set_display = st.session_state.set_idx + 1
    n_sets = config.SETS_PER_PARTICIPANT_H2
    big_session_label(set_display, n_sets, sess["letter"], size_em=3.5)

    n_q = _n_q_for(sess)
    q_idx = st.session_state.q_idx

    if condition == "binary":
        q = ep["binary_qs"][q_idx]
        prop_ko = q.get("prop_ko", q["prop"])
        cat_ko = ep.get("category_ko", ep["category"])
        st.markdown("### 로봇이 질문합니다")
        st.markdown(f"#### 이 **{cat_ko}**, {prop_ko}")
        st.caption(f"질문 {q_idx + 1} / {n_q}")
    else:
        q_ko = ep["open_qs_ko"][q_idx]
        st.markdown("### 로봇이 질문합니다")
        st.markdown(f"#### {q_ko}")
        st.caption(f"질문 {q_idx + 1} / {n_q}")

    # 로그: question_shown (idempotent)
    shown_key = f"logged_shown_{st.session_state.set_idx}_{sess['letter']}_{q_idx}"
    if not st.session_state.get(shown_key):
        payload = {
            "experiment": "H2",
            "set_idx": st.session_state.set_idx,
            "session_letter": sess["letter"],
            "q_idx": q_idx,
            "condition": condition,
            "ep_id": ep["ep_id"],
            "n_q": n_q,
        }
        if condition == "binary":
            payload["property"] = q["prop"]
        else:
            payload["question_en"] = ep["open_qs"][q_idx]
            payload["question_ko"] = ep["open_qs_ko"][q_idx]
        log(pid, "question_shown", **payload)
        st.session_state[shown_key] = True
        st.session_state.q_shown_at = time.time()

    # 응답 UI
    tk = f"{st.session_state.set_idx}_{sess['letter']}_{q_idx}"
    if condition == "binary":
        cols = st.columns(3)
        picked = None
        if cols[0].button("예", use_container_width=True, key=f"y_{tk}"):
            picked = "Yes"
        if cols[1].button("아니오", use_container_width=True, key=f"n_{tk}"):
            picked = "No"
        if cols[2].button("잘 모르겠음", use_container_width=True, key=f"u_{tk}"):
            picked = "Unclear"
        if picked:
            rt = time.time() - st.session_state.q_shown_at
            log(pid, "response_submitted",
                experiment="H2",
                set_idx=st.session_state.set_idx,
                session_letter=sess["letter"],
                q_idx=q_idx,
                condition=condition,
                ep_id=ep["ep_id"],
                property=q["prop"],
                response=picked,
                response_time_sec=round(rt, 3))
            _advance_after_response(pid)
    else:
        answer = st.text_input(
            "답변",
            placeholder="답변을 입력해주세요... (1자 이상)",
            key=f"answer_{tk}",
        )
        submit_disabled = (not answer) or (len(answer.strip()) < config.MIN_RESPONSE_CHARS)
        if st.button("제출", type="primary", use_container_width=True,
                     disabled=submit_disabled, key=f"submit_{tk}"):
            rt = time.time() - st.session_state.q_shown_at
            text = answer.strip()
            log(pid, "response_submitted",
                experiment="H2",
                set_idx=st.session_state.set_idx,
                session_letter=sess["letter"],
                q_idx=q_idx,
                condition=condition,
                ep_id=ep["ep_id"],
                question_en=ep["open_qs"][q_idx],
                question_ko=ep["open_qs_ko"][q_idx],
                response_text=text,
                response_length_chars=len(text),
                response_time_sec=round(rt, 3))
            _advance_after_response(pid)


def _advance_after_response(pid):
    sess = current_session()
    ep = sess["ep"]
    n_q = _n_q_for(sess)
    st.session_state.q_idx += 1
    if st.session_state.q_idx < n_q:
        st.session_state.phase = "session_gap"
        st.session_state.gap_started_at = time.time()
        st.session_state.gap_target = random.uniform(config.GAP_MIN_SEC, config.GAP_MAX_SEC)
    else:
        log(pid, "session_done_in_set",
            experiment="H2",
            set_idx=st.session_state.set_idx,
            session_letter=sess["letter"],
            condition=sess["condition"],
            ep_id=ep["ep_id"])
        if sess["letter"] == "A":
            st.session_state.phase = "session_transition"
        else:
            st.session_state.phase = "set_preference"
    st.rerun()


def render_session_gap(pid):
    hide_qa_buttons()
    sess = current_session()
    ep = sess["ep"]
    top_bar(pid, target_img=get_target_path(ep))
    set_display = st.session_state.set_idx + 1
    n_sets = config.SETS_PER_PARTICIPANT_H2
    big_session_label(set_display, n_sets, sess["letter"], size_em=3.5)
    st.title("다음 질문 준비 중...")
    st.markdown(f"## ⏳ 예상 소요 시간: **{config.GAP_HINT}**")
    loading_spinner()
    remaining = st.session_state.gap_target - (time.time() - st.session_state.gap_started_at)
    if remaining > 0:
        time.sleep(remaining)
    st.session_state.phase = "session_question"
    st.rerun()


def render_session_transition(pid):
    """세션 A 완료 → 세션 B 시작 버튼."""
    hide_qa_buttons()
    set_display = st.session_state.set_idx + 1
    n_sets = config.SETS_PER_PARTICIPANT_H2
    st.markdown(
        f'<div style="text-align:center;margin:0.5em 0;">'
        f'<div style="font-size:1.5em;">✅</div>'
        f'<span style="font-size:4em;font-weight:900;">세션 A 완료</span>'
        f'<div style="font-size:1em;opacity:0.6;margin-top:0.3em;">세트 {set_display} / {n_sets}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.info("이제 **세션 B** 가 시작됩니다. 같은 대상 물체에 다른 방식으로 답변해주세요.")
    if st.button("세션 B 시작", type="primary", use_container_width=True, key="start_B"):
        st.session_state.session_letter = "B"
        st.session_state.q_idx = 0
        st.session_state.q_shown_at = time.time()
        st.session_state.phase = "session_question"
        st.rerun()


def render_set_preference(pid):
    """현재 세트 A vs B 선호 (선지 짧게)."""
    hide_qa_buttons()
    set_display = st.session_state.set_idx + 1
    n_sets = config.SETS_PER_PARTICIPANT_H2
    st.title(f"세트 {set_display} / {n_sets} 마무리")
    st.markdown(f"##### {config.PREFERENCE_Q_PER_SET}")

    labels = {"A": "세션 A 방식", "B": "세션 B 방식"}
    choice = st.radio(
        "선택",
        options=["A", "B"],
        format_func=lambda k: labels[k],
        index=None,
        label_visibility="collapsed",
        key=f"pref_radio_{st.session_state.set_idx}",
    )
    if st.button("제출", type="primary", use_container_width=True,
                 disabled=(choice is None),
                 key=f"pref_submit_{st.session_state.set_idx}"):
        s = current_set()
        chosen_condition = s["session_A"]["condition"] if choice == "A" else s["session_B"]["condition"]
        preferred_ordinal = 1 if choice == "A" else 2  # A=first, B=second
        log(pid, "set_preference_submitted",
            experiment="H2",
            set_idx=st.session_state.set_idx,
            preference_letter=choice,
            preference_condition=chosen_condition,
            session_A_condition=s["session_A"]["condition"],
            session_B_condition=s["session_B"]["condition"],
            ep_id=s["ep"]["ep_id"],
            # H1 스키마 호환 필드 (별도 컬럼에 자동 저장)
            preference=chosen_condition,
            preferred_session_ordinal=preferred_ordinal,
            trial1_condition=s["session_A"]["condition"],
            trial2_condition=s["session_B"]["condition"])
        next_set = st.session_state.set_idx + 1
        if next_set < config.SETS_PER_PARTICIPANT_H2:
            st.session_state.set_idx = next_set
            st.session_state.session_letter = "A"
            st.session_state.q_idx = 0
            st.session_state.phase = "set_gap"
            st.session_state.set_gap_started_at = time.time()
        else:
            log(pid, "session_done", experiment="H2")
            st.session_state.phase = "done"
        st.rerun()


def render_set_gap(pid):
    hide_qa_buttons()
    st.title("다음 세트를 준비 중입니다...")
    loading_spinner()
    remaining = config.SET_GAP_SEC - (time.time() - st.session_state.set_gap_started_at)
    if remaining > 0:
        time.sleep(remaining)
    st.session_state.phase = "session_question"
    st.session_state.q_shown_at = time.time()
    st.rerun()


def render_done(pid):
    hide_qa_buttons()
    st.title("완료")
    st.markdown(config.DONE_TEXT)


# ---------------- Router ----------------
def main():
    pid = gate_pid()
    init_session()
    p = st.session_state.phase
    slot = st.empty()
    with slot.container():
        if p == "intro":               render_intro(pid)
        elif p == "tutorial":          render_tutorial(pid)
        elif p == "tutorial_q":        render_tutorial_q(pid)
        elif p == "tutorial_q2":       render_tutorial_q2(pid)
        elif p == "trial_intro":       render_trial_intro(pid)
        elif p == "session_question":  render_session_question(pid)
        elif p == "session_gap":       render_session_gap(pid)
        elif p == "session_transition":render_session_transition(pid)
        elif p == "set_preference":    render_set_preference(pid)
        elif p == "set_gap":           render_set_gap(pid)
        elif p == "done":              render_done(pid)
        else:
            st.error(f"알 수 없는 phase: {p}")


if __name__ == "__main__":
    main()
