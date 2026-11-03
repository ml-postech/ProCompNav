"""User Study App — 전역 설정값 (자주 tweak 하는 것들 여기 모음)"""

# --- 실험 이름 ---
APP_TITLE = "로봇 상호작용 방식 설문"

# --- 참가자 세션 ---
TRIALS_PER_PARTICIPANT_H1 = 2   # 조건 A 1 ep + 조건 B 1 ep (각 3Q)

# --- H1 조건별 초기 대기 ---
# 원칙: 로봇 탐색 속도 2× 향상 (탐색 시간 절반) + LLM 쿼리 시간(BATCHED_GAP)은 유지·모든 첫질문에 포함
# Batched INIT:     탐색 절반(305~335 / 2 = 152~168) + LLM(4.75~5.25) ≈ 157~173s
# Interleaved INIT: 탐색 절반(105~115 / 2 =  52~58) + LLM(4.75~5.25) ≈ 57~63s
BATCHED_INIT_MIN_SEC     = 157
BATCHED_INIT_MAX_SEC     = 173
INTERLEAVED_INIT_MIN_SEC = 57
INTERLEAVED_INIT_MAX_SEC = 63

# --- H1 조건별 질문 사이 gap ---
# Batched GAP:     LLM 만 (탐색 없음) — 유지, val_seen median 4.8s ±5%
# Interleaved GAP: 탐색 절반 + LLM = 57~63s (INIT 와 동일)
BATCHED_GAP_MIN_SEC      = 4.75
BATCHED_GAP_MAX_SEC      = 5.25
INTERLEAVED_GAP_MIN_SEC  = 57
INTERLEAVED_GAP_MAX_SEC  = 63

# 화면 hint (실제 range 와 정확히 일치)
BATCHED_WAIT_HINT     = "약 2분 40초 ~ 2분 55초"
INTERLEAVED_WAIT_HINT = "약 57 ~ 63 초"
BATCHED_GAP_HINT      = "약 5 초"
INTERLEAVED_GAP_HINT  = "약 57 ~ 63 초"

# 조건별 표시명 (사용자 대상) — 중립적·구체 워딩
COND_NAME_KO = {
    "batched":     "일괄 질문",
    "interleaved": "분산 질문",
}
# preference 페이지 선지용 (긴 서술)
COND_STYLE_KO = {
    "batched":     "긴 대기 후, 여러 질문을 연속해서 받는 방식",
    "interleaved": "짧은 대기 후, 여러 질문을 일정한 시간 간격으로 받는 방식",
}

# 대기 화면 서버 tick 간격 (짧으면 부드럽지만 리소스 소모)
WAIT_TICK_SEC = 3

# --- UI ---
CHIME_URL = None                 # None 이면 텍스트 알림만
SHOW_TIMER = True                # 대기 중 timer 표시

# --- 최종 선호 ---
PREFERENCE_Q1 = "방금 경험하신 두 방식 중 어느 것을 더 선호하십니까?"
# Preference option 라벨은 참가자의 실제 세션 순서에 따라 동적으로 생성 (render_preference 참고)
PREFERENCE_OPTIONS = {
    "batched":     "일괄 질문 방식",
    "interleaved": "분산 질문 방식",
}

# --- Intro / 안내 ---
INTRO_TEXT = """\
### 실험 안내

본 실험은 로봇이 참가자께 질문을 하는 **두 가지 방식** 을 비교하는 실험입니다.
두 방식은 각각 **별도의 세션** 에서 진행됩니다.

---

**🎯 실험의 목적**
- 로봇이 사용자에게 질문하는 **두 가지 상호작용 방식** 중 어느 것이 심리적으로 더 편안한지 조사하는 실험입니다.

---

**⚠️ 주의 사항**
- 본 실험은 **PC 에서만** 진행해주세요. (모바일은 지원하지 않습니다.) **헤드셋/이어폰 착용** 을 권장합니다 (알림음 확인용).
- 로봇의 질문에는 정확하게 답하지 않으셔도 되며, **편하게** 답해주시면 됩니다. (응답이 틀려도 무방합니다.)
- 도중에 창을 닫으시면 이어서 하실 수 없습니다. **가능하시면 한 번에 완료** 해주세요.
- **대기 시간 안내**: 본 실험은 페이지 내에서 로봇의 탐색을 기다리는 시간이 있습니다. 편하게 다른 업무를 보시면서 여유롭게 진행하셔도 되며, 로봇이 질문할 준비가 되면 화면에서 알림음 (🔔) 이 울립니다.

---

**⏱️ 예상 소요 시간**: 약 **8 분**

---

**📋 진행 방식**
- 총 **2개 세션** 을 진행합니다. 세션마다 로봇이 방을 잠시 탐색한 뒤 대상 물체에 대해 **3개의 예 / 아니오 질문** 을 드립니다.
- 매 세션마다 로봇이 대상 물체를 찾기 위해 질문합니다.
- 로봇이 탐색하는 동안에는 **자유롭게 다른 일을 하셔도 됩니다.** 알림음이 들리면 로봇의 질문이 화면에 표시됩니다.
- 세션 상단에 항상 **대상 물체 이미지** 가 표시됩니다. 이미지를 보시고 각 질문에 **예 / 아니오 / 잘 모르겠음** 중 하나로 답변해주세요.
- 두 세션이 끝나면 두 방식에 대한 짧은 설문을 작성하시고 종료됩니다.

---

**참고**
- **데이터**: 익명 ID 와 응답만 저장됩니다. 개인 식별 정보는 수집하지 않습니다.
- 응답의 정답 여부는 채점하지 않습니다.
"""

TUTORIAL_TEXT = """\
### 튜토리얼

시작 전 잠깐 방식에 익숙해질 수 있는 짧은 시연 세션이 있습니다.

- 로봇이 방을 탐색하는 동안에는 화면에 대기 안내가 표시됩니다.
- 로봇이 준비되면 알림음과 함께 질문이 나타납니다.
- **예 / 아니오** 버튼 중 하나를 눌러 답변합니다.

준비되시면 아래 버튼을 눌러주세요.
"""

DONE_TEXT = """\
### 참여해주셔서 감사합니다.

응답은 저장되었으며 창을 닫으셔도 됩니다.
"""

# --- 데이터 저장 ---
# Google Apps Script Web App URL. Streamlit secrets 에서도 override 가능.
DATA_WEBHOOK_URL = None  # secrets.toml 의 [webhook] url 이 우선
LOCAL_FALLBACK_SQLITE = "responses_local.db"  # dev 용

# --- 데이터 파일 ---
STIMULUS_JSON = "data/stimulus_pool.json"
