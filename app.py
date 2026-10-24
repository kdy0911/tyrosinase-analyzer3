
from pathlib import Path

import math
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams


# ==================================================
# 1. 페이지 설정 및 한글 글꼴
# ==================================================

st.set_page_config(
    page_title="티로시나아제 실험 분석기",
    page_icon="🧪",
    layout="wide"
)

FONT_PATH = (
    Path(__file__).parent
    / "fonts"
    / "NotoSansKR-VF.ttf"
)

if FONT_PATH.exists():
    font_manager.fontManager.addfont(str(FONT_PATH))
    korean_font = font_manager.FontProperties(
        fname=str(FONT_PATH)
    )
    rcParams["font.family"] = korean_font.get_name()
else:
    korean_font = None

rcParams["axes.unicode_minus"] = False


def apply_korean_font(ax):
    """그래프의 모든 글자에 한글 글꼴 적용"""
    if korean_font is not None:
        ax.title.set_fontproperties(korean_font)
        ax.xaxis.label.set_fontproperties(korean_font)
        ax.yaxis.label.set_fontproperties(korean_font)

        for label in ax.get_xticklabels():
            label.set_fontproperties(korean_font)

        for label in ax.get_yticklabels():
            label.set_fontproperties(korean_font)


# ==================================================
# 2. 앱 제목
# ==================================================

st.title("🧪 티로시나아제 억제 실험 분석기")

st.write(
    "천연물 추출물의 흡광도 데이터를 입력하면 "
    "공시험 보정, 효소 억제율 계산, 결과 시각화와 "
    "실험 결과에 대한 점검 의견을 확인할 수 있습니다."
)

st.info(
    "이 프로그램은 입력된 수치와 실험 조건을 바탕으로 "
    "계산 및 규칙 기반 점검을 수행합니다. "
    "실험 결과만으로 억제 기전을 확정하지는 않습니다."
)


# ==================================================
# 3. 실험 조건 입력
# ==================================================

st.header("1. 실험 조건")

col1, col2 = st.columns(2)

with col1:
    temperature = st.number_input(
        "반응 온도 (℃)",
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
        ["PBS", "에탄올", "증류수", "기타"]
    )

with col2:
    appearance = st.selectbox(
        "시료의 외관",
        ["맑음", "약간 혼탁함", "침전 또는 응집 관찰", "확인하지 않음"]
    )

    mixing = st.selectbox(
        "혼합 방법",
        ["충분히 혼합", "가볍게 혼합", "혼합 정도 불확실"]
    )

    repeats = st.number_input(
        "반복 측정 횟수",
        min_value=1,
        max_value=20,
        value=3,
        step=1
    )

notes = st.text_area(
    "추가 실험 메모",
    placeholder="예: 계피 추출물이 PBS에서 응집함"
)


# ==================================================
# 4. 대조군 흡광도 입력
# ==================================================

st.header("2. 대조군 데이터")

st.write(
    "대조군은 천연물 시료를 넣지 않은 효소 반응을 의미합니다. "
    "대조군 흡광도와 대조군 공시험 흡광도를 입력하세요."
)

col3, col4 = st.columns(2)

with col3:
    control_abs = st.number_input(
        "대조군 흡광도",
        min_value=0.0,
        value=0.800,
        step=0.01,
        format="%.4f"
    )

with col4:
    control_blank = st.number_input(
        "대조군 공시험 흡광도",
        min_value=0.0,
        value=0.100,
        step=0.01,
        format="%.4f"
    )

control_corrected = control_abs - control_blank

st.metric(
    "공시험 보정 대조군 흡광도",
    f"{control_corrected:.4f}"
)


# ==================================================
# 5. 천연물별 데이터 입력
# ==================================================

st.header("3. 천연물별 흡광도 데이터")

st.write(
    "아래 표의 예시 수치를 실제 측정값으로 바꿔 주세요. "
    "각 시료의 흡광도와 해당 시료의 공시험 흡광도를 입력합니다."
)

initial_data = pd.DataFrame({
    "천연물": ["계피", "녹차", "블루베리", "마늘"],
    "시료 흡광도": [0.600, 0.650, 0.700, 0.750],
    "시료 공시험": [0.100, 0.150, 0.200, 0.100]
})

if "sample_data" not in st.session_state:
    st.session_state.sample_data = initial_data.copy()

edited_data = st.data_editor(
    st.session_state.sample_data,
    num_rows="dynamic",
    use_container_width=True,
    key="sample_editor",
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
        "시료 공시험": st.column_config.NumberColumn(
            "시료 공시험 흡광도",
            min_value=0.0,
            format="%.4f",
            required=True
        )
    }
)

st.session_state.sample_data = edited_data.copy()


# ==================================================
# 6. 흡광도 보정 및 억제율 계산
# ==================================================

st.header("4. 계산 결과")

result_df = edited_data.copy()

numeric_columns = ["시료 흡광도", "시료 공시험"]

for column in numeric_columns:
    result_df[column] = pd.to_numeric(
        result_df[column],
        errors="coerce"
    )

result_df = result_df.dropna(
    subset=["천연물"] + numeric_columns
)

result_df["보정 흡광도"] = (
    result_df["시료 흡광도"]
    - result_df["시료 공시험"]
)

if control_corrected <= 0:
    st.error(
        "대조군의 보정 흡광도가 0 이하입니다. "
        "대조군과 공시험 측정값을 확인하세요."
    )
    result_df["억제율 (%)"] = float("nan")

else:
    result_df["억제율 (%)"] = (
        1
        - result_df["보정 흡광도"] / control_corrected
    ) * 100

    st.latex(
        r"\text{억제율}(\%)="
        r"\left(1-\frac{A_{\text{시료}}-A_{\text{시료 공시험}}}"
        r"{A_{\text{대조군}}-A_{\text{대조군 공시험}}}\right)"
        r"\times100"
    )

    st.dataframe(
        result_df.style.format({
            "시료 흡광도": "{:.4f}",
            "시료 공시험": "{:.4f}",
            "보정 흡광도": "{:.4f}",
            "억제율 (%)": "{:.2f}"
        }, na_rep="-"),
        use_container_width=True
    )

    valid_results = result_df[
        result_df["억제율 (%)"].notna()
    ]

    if not valid_results.empty:
        best_idx = valid_results["억제율 (%)"].idxmax()
        best_sample = valid_results.loc[best_idx]

        metric1, metric2 = st.columns(2)

        with metric1:
            st.metric(
                "가장 높은 계산 억제율",
                f"{best_sample['억제율 (%)']:.2f}%"
            )

        with metric2:
            st.metric(
                "해당 천연물",
                str(best_sample["천연물"])
            )

        st.caption(
            "계산된 억제율이 0% 미만이거나 100%를 초과할 수 있습니다. "
            "이 경우에도 값을 임의로 0~100%로 제한하지 말고 "
            "측정값과 공시험 보정 과정을 점검하세요."
        )


# ==================================================
# 7. 결과 그래프
# ==================================================

st.header("5. 천연물별 억제율 그래프")

if control_corrected > 0 and not result_df.empty:
    plot_df = result_df.dropna(
        subset=["억제율 (%)"]
    )

    if not plot_df.empty:
        fig, ax = plt.subplots(figsize=(9, 4))

        ax.bar(
            plot_df["천연물"].astype(str),
            plot_df["억제율 (%)"]
        )

        ax.axhline(0, linewidth=1)
        ax.axhline(100, linestyle="--", linewidth=1)

        ax.set_xlabel("천연물")
        ax.set_ylabel("계산된 억제율 (%)")
        ax.set_title("티로시나아제 억제율 비교")
        ax.tick_params(axis="x", rotation=20)

        apply_korean_font(ax)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# ==================================================
# 8. 규칙 기반 결과 점검
# ==================================================

st.header("6. 실험 결과 점검")

diagnostics = []

if temperature != 25:
    diagnostics.append(
        "반응 온도가 25℃와 다릅니다. "
        "시료 간 비교에서는 반응 온도를 동일하게 유지했는지 확인하세요."
    )

if reaction_time <= 0:
    diagnostics.append(
        "반응 시간이 0분 이하입니다. 실제 반응 시간을 확인하세요."
    )

if appearance in ["약간 혼탁함", "침전 또는 응집 관찰"]:
    diagnostics.append(
        "시료의 혼탁이나 침전은 빛의 산란으로 흡광도에 영향을 줄 수 있습니다. "
        "시료 공시험 보정이 적절한지 확인하세요."
    )

if mixing == "혼합 정도 불확실":
    diagnostics.append(
        "혼합 정도가 불확실하면 반응물의 접촉과 측정값이 달라질 수 있습니다. "
        "모든 시료에 동일한 혼합 절차를 적용했는지 확인하세요."
    )

if solvent != "PBS":
    diagnostics.append(
        "시료별 용매가 다르면 효소 활성이나 흡광도에 영향을 줄 수 있습니다. "
        "용매 자체의 영향을 확인할 대조 조건이 있는지 점검하세요."
    )

if control_corrected <= 0:
    diagnostics.append(
        "대조군 보정 흡광도가 0 이하이므로 억제율을 신뢰성 있게 계산할 수 없습니다."
    )

elif control_corrected < 0.05:
    diagnostics.append(
        "대조군 보정 흡광도가 매우 낮습니다. "
        "분모가 작아 억제율 계산 오차가 커질 수 있습니다."
    )

if repeats < 3:
    diagnostics.append(
        "반복 횟수가 적습니다. 가능하다면 독립적인 반복 측정으로 "
        "결과의 변동성을 확인하세요."
    )

if not result_df.empty and "억제율 (%)" in result_df.columns:
    for _, row in result_df.iterrows():
        name = str(row["천연물"])
        inhibition = row["억제율 (%)"]
        corrected = row["보정 흡광도"]

        if pd.isna(inhibition):
            continue

        if corrected < 0:
            diagnostics.append(
                f"{name}: 보정 흡광도가 음수입니다. "
                "시료 공시험과 시료 흡광도 입력값을 확인하세요."
            )

        if inhibition < 0:
            diagnostics.append(
                f"{name}: 계산 억제율이 음수입니다. "
                "시료의 보정 흡광도가 대조군보다 큰 경우 나타날 수 있습니다. "
                "시료 색, 혼탁, 반응 조건 및 측정값을 점검하세요."
            )

        elif inhibition > 100:
            diagnostics.append(
                f"{name}: 계산 억제율이 100%를 초과합니다. "
                "보정 흡광도가 음수인지 확인하고 공시험 보정 과정을 점검하세요."
            )

if notes.strip():
    st.write("**추가 메모:**", notes)

if diagnostics:
    for item in diagnostics:
        st.warning(item)
else:
    st.success(
        "입력된 조건에서 기본적인 점검 항목이 발견되지 않았습니다. "
        "이것이 실험 결과의 정확성을 보장하는 것은 아닙니다."
    )

st.caption(
    f"입력한 조건: {temperature:g}℃, "
    f"반응 시간 {reaction_time:g}분, "
    f"용매 {solvent}, 반복 횟수 {repeats}회"
)


# ==================================================
# 9. CSV 파일 다운로드
# ==================================================

st.header("7. 결과 파일 저장")

if not result_df.empty:
    csv_data = result_df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="분석 결과 CSV 다운로드",
        data=csv_data,
        file_name="tyrosinase_analysis.csv",
        mime="text/csv"
    )

st.caption(
    "주의: 이 프로그램은 입력된 데이터에 대한 계산과 기본적인 점검을 제공합니다. "
    "효소 억제 여부와 기전을 확정하려면 실험 설계, 반복 측정 및 추가 검증이 필요합니다."
)
