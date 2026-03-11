import streamlit as st
import time

# --- 페이지 설정 ---
st.set_page_config(page_title="Gen-AI EDA Agent Prototype", layout="wide")

st.title("🚀 Gen-AI EDA Agent Prototype")
st.caption("사업팀과 분석가를 위한 맞춤형 데이터 탐색 및 진단 에이전트")

# --- 세션 상태 초기화 (AI 매핑 시뮬레이션용) ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'mapped_features' not in st.session_state:
    st.session_state.mapped_features = []

# --- STEP 1: 분석 모드 선택 ---
st.header("Step 1. 분석 모드 선택")
mode = st.radio(
    "본인의 역할을 선택해주세요.",
    ["🏢 사업팀 인사이트 모드", "🧪 분석가 데이터 진단 모드"],
    horizontal=True
)

st.divider()

# --- STEP 2: 목적 및 조건 입력 ---
st.header("Step 2. 분석 목적 및 조건 입력")

if mode == "🏢 사업팀 인사이트 모드":
    col1, col2 = st.columns(2)
    with col1:
        target_def = st.text_input("🎯 타겟 정의 (필수)", placeholder="예: 최근 3개월 내 가입한 Sim Only 고객")
        control_def = st.text_input("👥 비교군 정의 (선택)", placeholder="미입력 시 전체 데이터와 비교")
    with col2:
        hypothesis = st.text_area("💡 나의 가설 입력 (선택)", placeholder="예: 연령대가 낮고 유튜브 사용량이 많을 것 같아", height=100)
    
    if st.button("🪄 가설 기반 변수 매핑 시작"):
        with st.spinner("AI가 가설을 해석하여 Feature Store에서 데이터를 찾는 중..."):
            time.sleep(1.5)
            st.session_state.mapped_features = ["나이", "성별", "유튜브_사용량", "넷플릭스_사용량", "평균_데이터_사용량", "가입_경로"]
            st.session_state.step = 2

else:  # 분석가 모드
    col1, col2 = st.columns(2)
    with col1:
        y_label = st.text_input("🎯 Target (Y Label) 지정 (필수)", placeholder="예: is_churn_3m (해지여부)")
        is_unsupervised = st.checkbox("Unsupervised 모드 (Y Label 없음)")
    with col2:
        st.write("⚙️ 진단 기준 설정 (기본값 제공)")
        outlier = st.select_slider("이상치 기준 (IQR)", options=[1.5, 2.0, 3.0], value=1.5)
        missing_th = st.slider("결측치 허용 임계치 (%)", 0, 100, 30)
        corr_th = st.slider("상관관계 경고 임계치", 0.0, 1.0, 0.8)

    analyst_goal = st.text_area("📝 상세 분석 목적 입력", placeholder="예: 해지 예측 모델용 피처들의 품질 진단 및 변수 선택 가이드 요청")

    if st.button("🔍 데이터 품질 진단 셋업 시작"):
        with st.spinner("AI가 분석 목적을 이해하고 Feature Store에서 매핑 중..."):
            time.sleep(1.5)
            st.session_state.mapped_features = ["age", "gender", "avg_arpu_3m", "call_quality_score", "contract_period", "complain_cnt"]
            st.session_state.step = 2

# --- STEP 3: 분석 셋업 확인 및 수정 ---
if st.session_state.step >= 2:
    st.divider()
    st.header("Step 3. 최종 분석 셋업 확인 및 수정")
    
    st.info("💡 AI가 Feature Store에서 다음 변수들을 선별했습니다. 분석에 포함할 항목을 최종 확인하세요.")
    
    # 변수 태그 UI 시뮬레이션 (Multiselect 활용)
    final_features = st.multiselect(
        "선별된 변수 리스트 (X Features)",
        options=st.session_state.mapped_features + ["추가_변수_A", "추가_변수_B"],
        default=st.session_state.mapped_features
    )
    
    st.subheader("📝 최종 로직 요약")
    if mode == "🏢 사업팀 인사이트 모드":
        st.write(f"✅ **타겟:** {target_def if target_def else '미지정'}")
        st.write(f"✅ **비교군:** {control_def if control_def else '전체 데이터'}")
        st.write(f"✅ **핵심 가설:** {hypothesis if hypothesis else '없음'}")
        st.success("📊 분석 방향: 두 집단 간의 라이프스타일 지표(Lift Index) 차이 분석 및 가설 검증 리포트 생성")
    else:
        st.write(f"✅ **Target:** {y_label if not is_unsupervised else 'Unsupervised'}")
        st.write(f"✅ **품질 기준:** 결측치 {missing_th}%, 상관관계 {corr_th} 이상")
        st.success("📊 분석 방향: 모델링 적합성 판단을 위한 품질 진단 및 변수 선택 가이드 생성")

    if st.button("🚀 분석 시작 (Run EDA)"):
        st.balloons()
        st.success("데이터 추출 및 분석이 시작되었습니다! (실제 구현 시 BQ 쿼리 실행)")
