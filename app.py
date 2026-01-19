import json
import uuid
from datetime import date
import pandas as pd
import streamlit as st

# -----------------------------
# 0) 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="S26 예약판매 타겟팅 Agent (MVP)",
    layout="wide",
)

st.title("🤖 갤럭시 S26 예약판매 타겟팅 Agent (Streamlit MVP)")
st.caption("계획 입력 → 추천 Feature 후보 제시 → 스코어 설계(placeholder) 출력 → 설정(JSON) 내보내기")

# -----------------------------
# 1) Feature 후보 라이브러리 (예시)
#    - 실제로는 너희가 쓰는 C360 스코어/행동지표/단말/요금제/결합/구매이력 등으로 확장하면 됨
# -----------------------------
FEATURE_LIBRARY = {
    "기변 의향/단말": [
        {"key": "device_change_intent_30d", "desc": "최근 30일 기변 의향(모델/요금제 탐색 기반)"},
        {"key": "premium_device_affinity", "desc": "프리미엄 단말 선호도(갤럭시 플래그십/폴더블 관심)"},
        {"key": "current_device_age_months", "desc": "현 단말 사용 개월 수"},
        {"key": "device_price_sensitivity", "desc": "가격 민감도(프로모션 반응/저가 선호)"},
    ],
    "구매/반응": [
        {"key": "campaign_response_rate_90d", "desc": "최근 90일 캠페인 반응률"},
        {"key": "high_value_purchase_history", "desc": "고가 구매/업그레이드 이력"},
        {"key": "reservation_purchase_propensity", "desc": "사전예약 구매 성향(과거 예약판매 참여)"},
        {"key": "channel_conversion_affinity", "desc": "채널 전환 선호(문자/카카오/앱푸시 등)"},
    ],
    "콘텐츠/행동": [
        {"key": "s26_content_views_14d", "desc": "최근 14일 S26 관련 콘텐츠 조회/체류"},
        {"key": "spec_comparison_behavior", "desc": "스펙 비교 행동(카메라/배터리/칩셋 페이지 탐색)"},
        {"key": "cart_or_apply_signal", "desc": "장바구니/신청/상담 시그널(구매 직전)"},
    ],
    "고객 가치/리텐션": [
        {"key": "arpu_bucket", "desc": "ARPU 구간(고/중/저)"},
        {"key": "tenure_months", "desc": "가입 기간"},
        {"key": "churn_risk_score", "desc": "이탈 위험 스코어"},
        {"key": "vip_or_priority_segment", "desc": "VIP/우수고객 세그먼트"},
    ],
    "혜택/프로모션 적합": [
        {"key": "trade_in_affinity", "desc": "보상판매(Trade-in) 선호"},
        {"key": "installment_affinity", "desc": "할부/카드혜택 선호"},
        {"key": "bundle_affinity", "desc": "결합/부가서비스 묶음 선호"},
    ],
}

# “상품/캠페인 성격”에 따라 추천 feature 세트를 다르게 뽑는 아주 단순한 규칙
RECOMMENDATION_RULES = {
    "S26 Ultra": {
        "must_have": ["premium_device_affinity", "spec_comparison_behavior", "high_value_purchase_history"],
        "nice_to_have": ["s26_content_views_14d", "reservation_purchase_propensity", "arpu_bucket"],
    },
    "S26 (Base)": {
        "must_have": ["device_change_intent_30d", "s26_content_views_14d", "campaign_response_rate_90d"],
        "nice_to_have": ["installment_affinity", "device_price_sensitivity", "channel_conversion_affinity"],
    },
    "S26 Plus": {
        "must_have": ["device_change_intent_30d", "spec_comparison_behavior", "campaign_response_rate_90d"],
        "nice_to_have": ["arpu_bucket", "trade_in_affinity", "installment_affinity"],
    },
    "S26 Ultra + 워치 번들": {
        "must_have": ["premium_device_affinity", "bundle_affinity", "high_value_purchase_history"],
        "nice_to_have": ["vip_or_priority_segment", "arpu_bucket", "reservation_purchase_propensity"],
    },
}

# -----------------------------
# 2) 유틸: 라이브러리에서 key로 feature 메타 찾기
# -----------------------------
def get_feature_meta(key: str):
    for group, feats in FEATURE_LIBRARY.items():
        for f in feats:
            if f["key"] == key:
                return {"group": group, **f}
    return {"group": "기타", "key": key, "desc": "(정의 필요)"}

def flatten_features():
    rows = []
    for group, feats in FEATURE_LIBRARY.items():
        for f in feats:
            rows.append({"group": group, "key": f["key"], "desc": f["desc"]})
    return pd.DataFrame(rows)

# -----------------------------
# 3) 사이드바: 캠페인 계획 입력
# -----------------------------
with st.sidebar:
    st.header("🧩 캠페인 계획 입력")
    campaign_name = st.text_input("캠페인명", value="갤럭시 S26 예약판매 타겟팅")
    product = st.selectbox(
        "상품/오퍼",
        options=list(RECOMMENDATION_RULES.keys()),
        index=0,
    )
    target_size = st.number_input("타겟 규모(명)", min_value=1000, step=1000, value=50000)
    start_dt = st.date_input("캠페인 시작일", value=date.today())
    channel = st.multiselect(
        "발송 채널(예시)",
        options=["문자(SMS)", "카카오", "앱푸시", "이메일", "콜/상담"],
        default=["문자(SMS)", "카카오"],
    )

    st.divider()
    st.subheader("⚙️ 스코어링 옵션(placeholder)")
    score_name = st.text_input("스코어 이름", value="S26_RESERVATION_SCORE")
    topn = st.number_input("최종 추출 Top-N", min_value=1000, step=1000, value=int(target_size))
    normalize = st.selectbox("정규화 방식", ["None", "Min-Max", "Z-Score", "Quantile(0~1)"], index=3)
    calibration = st.selectbox("캘리브레이션", ["None", "Platt", "Isotonic"], index=0)

# -----------------------------
# 4) 메인: Agent 실행 버튼
# -----------------------------
colA, colB = st.columns([2, 1], gap="large")

with colA:
    st.subheader("1) 입력된 계획 요약")
    st.write(
        {
            "캠페인명": campaign_name,
            "상품/오퍼": product,
            "타겟 규모(명)": int(target_size),
            "시작일": str(start_dt),
            "채널": channel,
            "스코어": score_name,
            "Top-N": int(topn),
            "정규화": normalize,
            "캘리브레이션": calibration,
        }
    )

    st.subheader("2) Feature 라이브러리(예시)")
    st.dataframe(flatten_features(), use_container_width=True, height=260)

with colB:
    st.subheader("🚀 Agent 실행")
    st.info("이 버튼이 ‘Agent가 계획을 받아 feature를 추천하고 스코어 설계를 제안’하는 단계라고 보면 돼.")
    run = st.button("계획 기반 추천 생성", type="primary")
    st.caption("※ 지금은 규칙 기반 추천 + 스코어 설계 템플릿 출력(MVP)")

# -----------------------------
# 5) Agent 로직 (run 시)
# -----------------------------
if run:
    # (1) 상품별 추천 세트
    rule = RECOMMENDATION_RULES.get(product, {"must_have": [], "nice_to_have": []})
    must = rule["must_have"]
    nice = rule["nice_to_have"]

    # (2) 규모에 따른 약간의 추천 변화 (예시)
    #  - 타겟 규모가 크면 범용 피처(반응률/의향) 위주
    #  - 타겟 규모가 작으면 구매직전 시그널(정밀 피처) 비중 증가
    if target_size <= 20000:
        nice = list(dict.fromkeys(nice + ["cart_or_apply_signal", "reservation_purchase_propensity"]))
    elif target_size >= 100000:
        nice = list(dict.fromkeys(nice + ["campaign_response_rate_90d", "device_change_intent_30d"]))

    # (3) 사용자 선택 가능하도록 기본 선택 세트 구성
    default_selected = list(dict.fromkeys(must + nice))  # 순서 유지 + 중복 제거

    st.divider()
    st.subheader("✅ Agent 결과: 추천 Feature 후보")

    # 메타 테이블
    rec_rows = [get_feature_meta(k) for k in default_selected]
    rec_df = pd.DataFrame(rec_rows)[["group", "key", "desc"]]
    st.dataframe(rec_df, use_container_width=True, height=240)

    st.markdown("### 3) Feature 선택/가중치(placeholder) 설정")
    st.write("아래에서 **스코어에 넣을 feature**를 고르고, **가중치(예시)**를 지정할 수 있어. (나중에 엔진 붙일 때 그대로 config로 넘기기 좋게 설계)")

    # 편집 테이블(사용자 선택 + weight)
    editable = rec_df.copy()
    editable.insert(0, "use", True)
    editable["weight"] = 1.0

    edited = st.data_editor(
        editable,
        use_container_width=True,
        hide_index=True,
        column_config={
            "use": st.column_config.CheckboxColumn("사용", help="스코어에 포함할지 여부"),
            "weight": st.column_config.NumberColumn("가중치(예시)", min_value=0.0, step=0.1),
        },
    )

    selected = edited[edited["use"] == True].copy()
    selected_keys = selected["key"].tolist()

    st.markdown("### 4) 스코어 설계 출력(placeholder)")
    if len(selected_keys) == 0:
        st.warning("선택된 feature가 없어 스코어를 구성할 수 없어요. 최소 1개 이상 선택해줘.")
    else:
        # 스코어 포맷(나중에 meta-logistic/MLP/LP 연동 등으로 확장 가능)
        # 여기서는 단순 가중합 + 정규화/캘리브레이션 옵션 표기만
        terms = []
        for _, r in selected.iterrows():
            terms.append(f"{r['weight']:.2f} * {r['key']}")

        score_formula = " + ".join(terms)
        st.code(
            f"""
[Score Spec]
score_name: {score_name}

raw_score = {score_formula}

post_process:
  normalize: {normalize}
  calibration: {calibration}

selection:
  top_n: {int(topn)}
""".strip(),
            language="yaml",
        )

        st.success("👉 출력 예시: 위 스펙대로 feature를 조합해서 하나의 스코어를 만들겠습니다! (뒷단 엔진은 추후 연결)")

    # -----------------------------
    # 6) Config(JSON) 생성 & 다운로드
    # -----------------------------
    st.markdown("### 5) 엔진 연동용 설정(JSON) 내보내기")
    config = {
        "run_id": str(uuid.uuid4()),
        "campaign": {
            "name": campaign_name,
            "product": product,
            "target_size": int(target_size),
            "start_date": str(start_dt),
            "channels": channel,
        },
        "score": {
            "name": score_name,
            "top_n": int(topn),
            "normalize": normalize,
            "calibration": calibration,
            "features": [
                {"key": r["key"], "weight": float(r["weight"]), "group": r["group"], "desc": r["desc"]}
                for _, r in selected.iterrows()
            ],
        },
        "notes": {
            "mvp": True,
            "todo": [
                "여기에 실제 스코어링 엔진 연결 (BQ/모델/룰베이스 등)",
                "feature 정의/스케일 방향(+) (-) 정리",
                "결측 처리, 이상치 처리, 중복 고객 처리",
            ],
        },
    }

    st.json(config)

    st.download_button(
        label="⬇️ 설정 JSON 다운로드",
        data=json.dumps(config, ensure_ascii=False, indent=2),
        file_name=f"{score_name}_config.json",
        mime="application/json",
    )

    st.markdown("---")
    st.subheader("🧠 (옵션) Agent가 말로 정리해주는 최종 메시지")
    summary_text = f"""
- 계획 입력 완료: **{product}** 예약판매 캠페인, 타겟 규모 **{int(target_size):,}명**, 채널 {", ".join(channel) if channel else "미지정"}
- 추천 feature 후보를 기반으로 **{len(selected_keys)}개 feature**를 선택했고, 이를 가중합 형태의 **{score_name}**로 구성합니다.
- 후처리 옵션: normalize={normalize}, calibration={calibration}
- 최종 추출은 Top-{int(topn):,} 기준으로 수행(엔진 연동 시 적용)
"""
    st.write(summary_text.strip())

else:
    st.info("왼쪽에서 계획을 입력하고, 오른쪽 **‘계획 기반 추천 생성’** 버튼을 눌러 실행해봐.")
