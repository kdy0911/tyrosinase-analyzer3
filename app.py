
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math

st.set_page_config(
    page_title="티로시나아제 실험 분석",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 티로시나아제 억제율 분석 프로그램")
st.write(
    "천연물 추출물의 흡광도와 실험 조건을 분석하여 "
    "억제율, 결과의 특이점, 가능한 원인 및 후속 실험을 제안합니다."
)

st.info(
    "이 프로그램은 사전에 정의한 규칙을 사용하는 분석 도구입니다. "
    "제시되는 원인은 가설이며, 실제 원인은 추가 실험으로 확인해야 합니다."
)

# --------------------------------------------------
# 1. 실험 조건 입력
# --------------------------------------------------

st.header("1. 실험 조건")

col1, col2 = st.columns(2)

with col1:
    temperature = st.number_input(
        "반응 온도 (°C)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=1.0
    )

    reaction_time = st.number_input(
        "반응 시간 (분)",
        min_value=0.0,
        max_value=300.0,
        value=10.0,
        step=1.0
    )

    solvent = st.selectbox(
        "천연물 추출 용매",
        ["PBS", "증류수", "에탄올", "기타"]
    )

with col2:
    appearance = st.selectbox(
        "시료의 색과 탁도",
        [
            "특이사항 없음",
            "색이 진함",
            "탁하거나 침전이 있음",
            "색이 진하고 탁함",
            "확인하지 않음"
        ]
    )

    mixing = st.selectbox(
        "시료와 반응액의 혼합 상태",
        ["잘 혼합됨", "혼합이 불균일할 수 있음", "확인하지 않음"]
    )

    repeat_count = st.selectbox(
        "각 조건의 반복 측정 횟수",
        [1, 2, 3, 4, 5],
        index=0
    )

experiment_notes = st.text_area(
    "추가 관찰 사항 (선택)",
    placeholder=(
        "예: 계피 추출액에 침전이 생김, "
        "반응 후 색 변화가 작았음, 측정 시간이 조금 달랐음"
    )
)

# --------------------------------------------------
# 2. 대조군 입력
# --------------------------------------------------

st.header("2. 대조군 흡광도")

col3, col4 = st.columns(2)

with col3:
    control_abs = st.number_input(
        "대조군 반응액 흡광도",
        min_value=0.0,
        value=0.500,
        step=0.010,
        format="%.4f"
    )

with col4:
    control_blank = st.number_input(
        "대조군 블랭크 흡광도",
        min_value=0.0,
        value=0.050,
        step=0.010,
        format="%.4f"
    )

control_corrected = control_abs - control_blank

if control_corrected <= 0:
    st.warning(
        "대조군의 보정 흡광도가 0 이하입니다. "
        "대조군과 블랭크의 조성 및 입력값을 확인하세요. "
        "이 상태에서는 억제율을 계산하지 않습니다."
    )

# --------------------------------------------------
# 3. 시료 흡광도 입력
# --------------------------------------------------

st.header("3. 천연물별 흡광도 입력")

st.caption(
    "아래 예시값을 실제 측정값으로 바꿔 주세요. "
    "시료 블랭크는 시료 자체의 색이나 탁도 등 "
    "배경 흡광도를 보정할 수 있도록 구성해야 합니다."
)

initial_data = pd.DataFrame({
    "천연물": ["계피", "녹차", "블루베리", "마늘"],
    "시료 흡광도": [0.400, 0.350, 0.450, 0.420],
    "시료 블랭크": [0.080, 0.060, 0.120, 0.070]
})

samples = st.data_editor(
    initial_data,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    column_config={
        "천연물": st.column_config.TextColumn(
            "천연물 이름",
            required=True
        ),
        "시료 흡광도": st.column_config.NumberColumn(
            "시료 흡광도",
            min_value=0.0,
            format="%.4f",
            required=True
        ),
        "시료 블랭크": st.column_config.NumberColumn(
            "시료 블랭크",
            min_value=0.0,
            format="%.4f",
            required=True
        )
    }
)

# --------------------------------------------------
# 4. 데이터 분석 함수
# --------------------------------------------------

def diagnose(row, control_value):
    name = str(row["천연물"]).strip()
    sample_abs = float(row["시료 흡광도"])
    blank_abs = float(row["시료 블랭크"])

    corrected = sample_abs - blank_abs
    rate = (1 - corrected / control_value) * 100

    findings = []
    possible_causes = []
    followups = []

    # 보정 흡광도 점검
    if corrected < 0:
        findings.append("시료의 보정 흡광도가 음수입니다.")
        possible_causes.append(
            "블랭크 흡광도가 시료 흡광도보다 높습니다. "
            "측정값, 블랭크 조성, 기기 영점 및 큐벳 상태를 확인해야 합니다."
        )
        followups.append(
            "시료와 블랭크의 조성을 다시 확인하고 동일 조건에서 재측정하세요."
        )

    elif math.isclose(corrected, 0, abs_tol=1e-10):
        findings.append("시료의 보정 흡광도가 0에 가깝습니다.")
        possible_causes.append(
            "반응 생성물이 적었거나, 블랭크 보정 또는 측정 범위의 영향일 수 있습니다."
        )
        followups.append(
            "반응 유무, 반응 시간, 블랭크 구성 및 기기의 측정 범위를 확인하세요."
        )

    # 억제율 범위 점검
    if rate < 0:
        findings.append("억제율이 음수입니다.")
        possible_causes.append(
            "보정된 시료 흡광도가 대조군보다 높습니다. "
            "효소 반응 증가 외에도 시료의 색, 탁도, "
            "블랭크 불일치 또는 반응 조건 차이가 원인일 수 있습니다."
        )
        followups.append(
            "시료 색과 탁도에 맞는 블랭크인지 확인하고 "
            "대조군과 시료의 반응 시간 및 온도를 일치시키세요."
        )

    elif rate > 100:
        findings.append("억제율이 100%를 초과합니다.")
        possible_causes.append(
            "시료의 보정 흡광도가 음수일 때 나타날 수 있습니다. "
            "블랭크 보정과 입력값을 먼저 확인해야 합니다."
        )
        followups.append(
            "보정 흡광도 계산과 시료 블랭크를 점검하고 재측정하세요."
        )

    elif 0 <= rate < 10:
        findings.append("계산된 억제율이 0~10%입니다.")
        possible_causes.append(
            "측정 조건에서 억제 효과가 작았을 가능성이 있지만, "
            "측정 오차와 시료의 광학적 간섭도 고려해야 합니다."
        )
        followups.append(
            "반복 측정 결과와 대조군 변동을 확인하고, "
            "필요하면 시료 농도별 비교 실험을 계획하세요."
        )

    elif 10 <= rate <= 100:
        findings.append("계산된 억제율은 10~100% 범위입니다.")
        possible_causes.append(
            "대조군보다 보정 흡광도가 낮다는 뜻입니다. "
            "이 차이가 실제 효소 억제 때문인지는 "
            "블랭크와 대조 조건을 통해 확인해야 합니다."
        )
        followups.append(
            "동일 조건에서 반복 측정하고 시료 블랭크 보정이 적절한지 확인하세요."
        )

    # 시료 블랭크 영향 점검
    if sample_abs > 0 and blank_abs / sample_abs >= 0.5:
        findings.append(
            "시료 흡광도에서 블랭크가 차지하는 비율이 큽니다."
        )
        possible_causes.append(
            "시료 자체의 색이나 탁도가 측정값에 크게 영향을 줄 수 있습니다."
        )
        followups.append(
            "시료만 포함한 블랭크의 조성을 확인하고, "
            "필요하면 시료의 색과 탁도를 별도로 기록하세요."
        )

    # 실험 조건에 따른 진단
    if appearance in ["색이 진함", "색이 진하고 탁함"]:
        findings.append("시료 색이 흡광도에 영향을 줄 가능성이 있습니다.")
        possible_causes.append(
            "천연물 색소가 측정 파장에서 흡광할 수 있습니다."
        )
        followups.append(
            "시료 자체의 배경 흡광도를 적절히 보정하고 "
            "모든 시료에 같은 측정 조건을 적용하세요."
        )

    if appearance in ["탁하거나 침전이 있음", "색이 진하고 탁함"]:
        findings.append("탁도나 침전이 측정값에 영향을 줄 수 있습니다.")
        possible_causes.append(
            "입자에 의한 빛 산란이나 불균일한 시료 분포가 "
            "흡광도에 영향을 줄 수 있습니다."
        )
        followups.append(
            "시료의 침전 여부와 측정 전 혼합 조건을 일정하게 유지하세요."
        )

    if mixing == "혼합이 불균일할 수 있음":
        findings.append("반응액이 균일하게 혼합되지 않았을 가능성이 있습니다.")
        possible_causes.append(
            "시료와 기질의 혼합 정도 차이가 반응 및 측정값의 변동을 유발할 수 있습니다."
        )
        followups.append(
            "혼합 방법과 측정 시점을 통일하세요."
        )

    if reaction_time <= 0:
        findings.append("반응 시간이 0분 이하로 입력되었습니다.")
        followups.append("실제 반응 시간을 확인해 입력하세요.")

    if repeat_count == 1:
        findings.append("반복 측정이 1회뿐입니다.")
        possible_causes.append(
            "현재 값만으로 측정의 재현성이나 변동 정도를 판단하기 어렵습니다."
        )
        followups.append(
            "가능하면 동일 조건에서 여러 번 반복 측정해 평균과 변동을 확인하세요."
        )

    if solvent == "에탄올":
        findings.append(
            "에탄올 추출물을 사용했습니다. 효소 반응액에 들어간 용매 조건을 확인하세요."
        )
        possible_causes.append(
            "추출 용매가 반응액에 남아 있다면 효소 활성에 영향을 줄 수 있습니다."
        )
        followups.append(
            "최종 반응액의 용매 비율을 확인하고, 이에 맞는 용매 대조군을 고려하세요."
        )

    # 중복 문구 제거
    findings = list(dict.fromkeys(findings))
    possible_causes = list(dict.fromkeys(possible_causes))
    followups = list(dict.fromkeys(followups))

    if not findings:
        findings.append("입력된 정보에서 기본적인 이상 징후가 발견되지 않았습니다.")
        possible_causes.append(
            "이 결과만으로 효소 억제의 원인이나 측정 정확성을 확정할 수는 없습니다."
        )
        followups.append(
            "반복 측정과 대조군 비교를 통해 결과의 재현성을 확인하세요."
        )

    return {
        "천연물": name,
        "시료 흡광도": sample_abs,
        "시료 블랭크": blank_abs,
        "보정 흡광도": corrected,
        "억제율 (%)": rate,
        "관찰된 특징": findings,
        "가능한 원인": possible_causes,
        "추천 후속 실험": followups
    }

# --------------------------------------------------
# 5. 분석 실행
# --------------------------------------------------

st.header("4. 분석 및 진단")

if st.button("억제율 계산 및 원인 분석", type="primary"):

    if control_corrected <= 0:
        st.error(
            "대조군의 보정 흡광도가 0 이하이므로 "
            "억제율을 계산할 수 없습니다. 대조군 입력값을 확인하세요."
        )

    elif samples.empty:
        st.error("분석할 천연물 데이터를 입력하세요.")

    elif samples["천연물"].isna().any():
        st.error("천연물 이름이 비어 있는 행을 수정하거나 삭제하세요.")

    elif samples["천연물"].astype(str).str.strip().eq("").any():
        st.error("천연물 이름이 비어 있는 행을 수정하거나 삭제하세요.")

    elif samples[["시료 흡광도", "시료 블랭크"]].isna().any().any():
        st.error("흡광도 또는 블랭크 값이 비어 있습니다.")

    elif (samples[["시료 흡광도", "시료 블랭크"]] < 0).any().any():
        st.error("흡광도 값은 음수가 될 수 없습니다. 입력값을 확인하세요.")

    else:
        results = []

        for _, row in samples.iterrows():
            results.append(diagnose(row, control_corrected))

        result_df = pd.DataFrame(results)

        st.session_state["tyrosinase_results"] = result_df
        st.session_state["tyrosinase_conditions"] = {
            "반응 온도": temperature,
            "반응 시간": reaction_time,
            "추출 용매": solvent,
            "시료 색과 탁도": appearance,
            "혼합 상태": mixing,
            "반복 측정 횟수": repeat_count,
            "추가 관찰": experiment_notes
        }

# --------------------------------------------------
# 6. 결과 표시
# --------------------------------------------------

if "tyrosinase_results" in st.session_state:

    result_df = st.session_state["tyrosinase_results"]

    st.subheader("계산 결과")

    display_df = result_df[
        [
            "천연물",
            "시료 흡광도",
            "시료 블랭크",
            "보정 흡광도",
            "억제율 (%)"
        ]
    ].copy()

    st.dataframe(
        display_df.style.format({
            "시료 흡광도": "{:.4f}",
            "시료 블랭크": "{:.4f}",
            "보정 흡광도": "{:.4f}",
            "억제율 (%)": "{:.2f}%"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("천연물별 억제율 그래프")

    fig, ax = plt.subplots(figsize=(9, 4))

    ax.bar(
        result_df["천연물"],
        result_df["억제율 (%)"]
    )

    ax.axhline(0, linewidth=1)
    ax.axhline(100, linestyle="--", linewidth=1)

    ax.set_xlabel("천연물")
    ax.set_ylabel("계산된 억제율 (%)")
    ax.set_title("Tyrosinase Inhibition Rate")
    ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("천연물별 원인 분석")

    for _, row in result_df.iterrows():

        with st.expander(
            f'{row["천연물"]} — 억제율 {row["억제율 (%)"]:.2f}%'
        ):
            st.markdown("**관찰된 특징**")
            for item in row["관찰된 특징"]:
                st.write(f"- {item}")

            st.markdown("**가능한 원인**")
            for item in row["가능한 원인"]:
                st.write(f"- {item}")

            st.markdown("**추천 후속 실험**")
            for item in row["추천 후속 실험"]:
                st.write(f"- {item}")

    # 조건별 전체 주의사항
    st.subheader("전체 실험 조건 점검")

    conditions = st.session_state.get(
        "tyrosinase_conditions", {}
    )

    st.write(
        f'- 반응 온도: {conditions.get("반응 온도")} °C'
    )
    st.write(
        f'- 반응 시간: {conditions.get("반응 시간")} 분'
    )
    st.write(
        f'- 추출 용매: {conditions.get("추출 용매")}'
    )
    st.write(
        f'- 반복 측정 횟수: {conditions.get("반복 측정 횟수")} 회'
    )

    if conditions.get("추가 관찰", "").strip():
        st.write(
            f'- 추가 관찰: {conditions["추가 관찰"]}'
        )

    st.warning(
        "주의: 이 앱은 입력된 조건과 계산 결과를 바탕으로 "
        "가능한 원인을 제안합니다. 억제율만으로 실제 효소 억제 여부를 "
        "확정할 수 없으며, 후속 실험으로 확인해야 합니다."
    )

    csv_data = result_df[
        [
            "천연물",
            "시료 흡광도",
            "시료 블랭크",
            "보정 흡광도",
            "억제율 (%)"
        ]
    ].to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "분석 결과 CSV 다운로드",
        data=csv_data,
        file_name="tyrosinase_analysis.csv",
        mime="text/csv"
    )
