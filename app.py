import streamlit as st
import time

# --- 1. [메타 데이터 테이블 시뮬레이션] ---
META_TABLE = {
    "구매": {
        "pur_amt_7d": "최근 7일 구매 금액 합계",
        "pur_cnt_30d": "최근 30일 구매 건수",
        "pref_cat_l": "최대 구매 카테고리(대)",
        "avg_order_val": "평균 주문 단가",
        "last_pur_date": "최종 구매 경과일"
    },
    "통화/문자": {
        "call_dur_avg": "평균 통화 시간",
        "sms_sent_30d": "최근 30일 문자 발송 건수",
        "intl_call_use_flag": "국제 전화 이용 여부",
        "weekend_call_ratio": "주말 통화 비중",
        "roaming_use_days": "해외 로밍 이용 일수"
    },
    "시청": {
        "ott_netflix_min": "넷플릭스 월간 시청 시간",
        "vod_action_score": "액션 장르 선호도",
        "realtime_tv_min": "실시간 TV 일평균 시청 시간",
        "kids_contents_ratio": "키즈 콘텐츠 시청 비중",
        "vod_purchase_amt": "VOD 유료 결제 금액"
    },
    "데모": {
        "cust_age": "고객 연령",
        "cust_gender": "고객 성별",
        "household_cnt": "가구원 수",
        "home_addr_city": "거주지 주소(시/도)",
        "is_married": "기혼 여부"
    },
    "위치": {
        "main_activity_area": "주 활동 지역명",
        "stay_time_work": "직장 지역 체류 시간",
        "moving_dist_avg": "일평균 이동 거리",
        "overnight_stay_cnt": "최근 1개월 타지역 숙박 횟수"
    },
    "서비스 이용": {
        "svc_stus_period": "서비스 가입 기간(개월)",
        "membership_grade": "멤버십 등급",
        "vas_join_cnt": "부가서비스 가입 개수",
        "m3_membership_use_cnt": "최근 3개월 멤버십 이용 건수",
        "lnwls_cnvg_yn" : "유무선 결합 여부"
    },
    "웹앱 접속": {
        "app_launch_cnt": "자사 앱 실행 횟수",
        "top_access_app": "최다 접속 앱 카테고리",
        "data_usage_mb": "웹/앱 데이터 사용량(MB)",
        "night_access_ratio": "심야 시간대 접속 비중",
        "m3_ytbe_wbap_cnt": "최근 3개월 유튜브 웹앱 접속 건수", 
        "m3_sns_wbap_cnt": "최근 3개월 SNS 웹앱 접속 건수",
        "m3_simp_stlm_wbap_cnt": "최근 3개월 간편결제 웹앱 접속 건수"
    }
}

KOR_TO_ENG = {v: k for cat in META_TABLE.values() for k, v in cat.items()}
ALL_KOR_NAMES = list(KOR_TO_ENG.keys())

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="Gen-AI EDA Agent Prototype", layout="wide")

# 세션 관리 (모드 변경 시 초기화 로직 포함)
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'mapped_kor' not in st.session_state:
    st.session_state.mapped_kor = []
if 'current_mode' not in st.session_state:
    st.session_state.current_mode = ""

# --- 메인 화면 ---
st.title("🔍 Gen-AI EDA Agent")
st.caption("BigQuery 기반 데이터 탐색 및 한글 물리명 기반 변수 셋업")

# --- STEP 1: 분석 모드 선택 ---
st.header("Step 1. 분석 모드 선택")
mode = st.radio(
    "분석 목적에 맞는 모드를 선택해주세요.",
    ["🏢 Target Profiling Mode", "🧪 Feature Engineering Mode"],
    horizontal=True
)

# 모드가 바뀌면 Step 3를 닫고 매핑 리스트를 비웁니다 (에러 방지 핵심)
if st.session_state.current_mode != mode:
    st.session_state.current_mode = mode
    st.session_state.step = 1
    st.session_state.mapped_kor = []

st.divider()

# --- STEP 2: 모드별 동적 입력 화면 ---
st.header("Step 2. 분석 목적 및 조건 입력")

if mode == "🏢 Target Profiling Mode":
    st.subheader("🏢 Business Insight Setup")
    col1, col2 = st.columns(2)
    with col1:
        target_def = st.text_input("🎯 타겟 정의 (필수)", placeholder="예: 최근 3개월 내 가입한 Sim Only 고객")
        control_def = st.text_input("👥 비교군 정의 (선택)", placeholder="미입력 시 전체 데이터와 비교")
    with col2:
        hypothesis = st.text_area("💡 나의 가설 입력 (선택)", placeholder="예: 연령대가 낮고 유튜브 사용량이 많을 것 같아", height=100)
    
    if st.button("🪄 가설 기반 지표 매핑 시작"):
        with st.spinner("AI가 가설을 해석하여 메타 테이블에서 지표를 찾는 중..."):
            time.sleep(1)
            # AI 선별 결과 (메타 테이블에 있는 이름만 정확히 넣어야 함)
            st.session_state.mapped_kor = ["고객 연령", "고객 성별", "최근 3개월 유튜브 웹앱 접속 건수", "최근 3개월 SNS 웹앱 접속 건수", "웹/앱 데이터 사용량(MB)", "최근 3개월 간편결제 웹앱 접속 건수"]
            st.session_state.step = 2
            st.rerun()

else:
    st.subheader("🧪 Data Analyst Setup")
    col1, col2 = st.columns(2)
    with col1:
        y_label = st.text_input("🎯 Target (Y Label) 지정", placeholder="예: 모바일 프리미엄 단말 사용")
        st.checkbox("Unsupervised 모드 (Y Label 없음)")
    with col2:
        st.write("⚙️ 진단 기준 설정")
        c_outlier, c_missing = st.columns(2)
        c_outlier.select_slider("이상치 기준(IQR)", options=[1.5, 2.0, 3.0], value=1.5)
        c_missing.number_input("결측치 허용(%)", 0, 100, 30)
    
    analyst_goal = st.text_area("📝 상세 분석 목적", placeholder="피처 품질 진단 요청 사항 입력", height=100)

    if st.button("🔍 데이터 품질 진단 셋업 시작"):
        with st.spinner("AI가 변수를 선별 중..."):
            time.sleep(1)
            st.session_state.mapped_kor = ["고객 연령", "서비스 가입 기간(개월)", "최근 3개월 멤버십 이용 건수", "유무선 결합 여부", "웹/앱 데이터 사용량(MB)"]
            st.session_state.step = 2
            st.rerun()

# --- STEP 3: 최종 분석 셋업 확인 ---
if st.session_state.step >= 2:
    st.divider()
    st.header("Step 3. 최종 분석 셋업 확인 및 수정")
    
    # 에러 방지용 안전 장치: default 값이 ALL_KOR_NAMES 안에 있는지 한 번 더 확인
    safe_defaults = [val for val in st.session_state.mapped_kor if val in ALL_KOR_NAMES]
    
    selected_kor_final = st.multiselect(
        "✅ 최종 선택된 분석 지표",
        options=ALL_KOR_NAMES,
        default=safe_defaults
    )

    st.subheader("📂 카테고리별 전체 탐색")
    tab_titles = [f"{cat} ({len(items)})" for cat, items in META_TABLE.items()]
    tabs = st.tabs(tab_titles)
    
    for i, (cat_name, items) in enumerate(META_TABLE.items()):
        with tabs[i]:
            cols = st.columns(3)
            for j, (eng, kor) in enumerate(items.items()):
                # 체크박스로도 선택 가능하게 연동
                cols[j % 3].checkbox(f"{kor}", key=f"chk_{eng}_{i}", value=(kor in selected_kor_final))

    with st.expander("🛠️ 시스템 추출 정보 (백엔드 매핑 확인)"):
        selected_eng_cols = [KOR_TO_ENG[k] for k in selected_kor_final if k in KOR_TO_ENG]
        st.code(f"Selected Columns: {', '.join(selected_eng_cols)}")

    if st.button("🚀 최종 분석 리포트 생성", type="primary"):
        st.balloons()
        st.success("BigQuery 데이터 기반 분석이 시작되었습니다.")
