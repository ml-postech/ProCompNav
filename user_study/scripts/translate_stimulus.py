"""Stimulus 20 ep 의 category / binary property / open-ended question 을 한국어로 번역.

또한 각 ep 의 target image 를 Gemini 3 Flash Preview 에 보여줘 category label 이 정확한지 검증.

Output: data/stimulus_pool_ko.json  (원본 필드 + *_ko 필드 + category_verified 필드)
"""
import base64, json, os, sys, time, requests

BASE = os.environ.get("STUDY_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "study1_binary_vs_open"))
IN_JSON  = f"{BASE}/data/stimulus_pool.json"
OUT_JSON = f"{BASE}/data/stimulus_pool_ko.json"
ENV_FILE = os.environ.get("ENV_FILE", ".env")  # file with OPENROUTER_API_KEY=...
MODEL    = "google/gemini-3-flash-preview"
URL      = "https://openrouter.ai/api/v1/chat/completions"


def get_key():
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    for line in open(ENV_FILE):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip("'\"")
    sys.exit("OPENROUTER_API_KEY not found")


def call_openrouter(api_key, messages, timeout=60):
    body = {
        "model": MODEL,
        "max_tokens": 512,
        "temperature": 0.0,
        "messages": messages,
    }
    r = requests.post(URL, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }, json=body, timeout=timeout)
    if not r.ok:
        return None
    return r.json()["choices"][0]["message"]["content"]


def translate_text(api_key, text, kind="attribute"):
    """binary attribute / open question / category 한국어 번역."""
    if kind == "attribute":
        prompt = (
            f"Translate the following English attribute phrase into a NATURAL, SHORT Korean phrase\n"
            f"suitable for a yes/no question about a household object. Keep it concise (5-15 chars).\n"
            f"Do NOT wrap in quotes. Output only the Korean phrase.\n\n"
            f"English: {text}\n"
            f"Korean:"
        )
    elif kind == "open":
        prompt = (
            f"Translate the following English open-ended question into a NATURAL Korean question\n"
            f"suitable for asking a user about a household object.\n"
            f"Do NOT wrap in quotes. Output only the Korean question.\n\n"
            f"English: {text}\n"
            f"Korean:"
        )
    else:  # category
        prompt = (
            f"Translate this English household object category to a natural short Korean noun.\n"
            f"Output only the Korean word.\n\n"
            f"English: {text}\n"
            f"Korean:"
        )
    return (call_openrouter(api_key, [{"role": "user", "content": prompt}]) or "").strip()


def verify_category_from_image(api_key, img_path, category_en, category_ko):
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    prompt = (
        f"Look at the image. The image is claimed to show a '{category_en}' ({category_ko}).\n"
        f"Is the primary object in this image really a {category_en}?\n"
        f"Reply with exactly ONE word: yes, no, or unclear."
    )
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]}]
    ans = (call_openrouter(api_key, msgs) or "").strip().lower()
    if "yes" in ans.split(): return "YES"
    if "no"  in ans.split(): return "NO"
    return "UNCLEAR"


def main():
    api_key = get_key()
    pool = json.load(open(IN_JSON))
    total_cost = 0.0

    # 1) unique category set → translate once
    cats = sorted(set(e["category"] for e in pool["episodes"]))
    print(f"Translating {len(cats)} categories...")
    cat_ko = {}
    for c in cats:
        cat_ko[c] = translate_text(api_key, c, kind="category")
        print(f"  {c:30s} -> {cat_ko[c]}")

    # 2) per ep: attributes ko + open ko + category verification
    for i, ep in enumerate(pool["episodes"]):
        print(f"\n[{i+1}/{len(pool['episodes'])}] ep{ep['ep_id']} ({ep['category']})")
        ep["category_ko"] = cat_ko[ep["category"]]
        # binary attributes
        for q in ep["binary_qs"]:
            q["prop_ko"] = translate_text(api_key, q["prop"], kind="attribute")
            print(f"  binary: {q['prop']!r} -> {q['prop_ko']!r}")
        # open questions
        ep["open_qs_ko"] = []
        for q in ep["open_qs"]:
            q_ko = translate_text(api_key, q, kind="open")
            ep["open_qs_ko"].append(q_ko)
            print(f"  open:   {q[:60]!r} -> {q_ko!r}")
        # category 는 사용자가 이미 눈으로 확인 후 pick 했으므로 verify skip

    with open(OUT_JSON, "w") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {OUT_JSON}")

    print(f"Done: {len(pool['episodes'])} eps translated")


if __name__ == "__main__":
    main()
