from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


def _get_matplotlib():
    try:
        import matplotlib.pyplot as plt  # type: ignore

        return plt
    except Exception:
        return None


@dataclass(frozen=True)
class SnapshotMetrics:
    model: str
    snapshot: str
    is_best: bool
    epoch: float
    step: int
    precision: float
    recall: float
    f1: float
    accuracy: Optional[float]
    tp: int
    fp: int
    fn: int
    tn: Optional[int]
    source_file: str
    source_lines: str
    notes: str = ""

MODEL_NER_DETAIL = "indolem/indobert-base-uncased"
MODEL_REVISION_DETAIL = "indobenchmark/indobert-base-p2"
COL_MODEL = "indoBERT model"


METRICS = [
    SnapshotMetrics(
        model=MODEL_NER_DETAIL,
        snapshot="best_model",
        is_best=True,
        epoch=3.0,
        step=300,
        precision=0.9950549450549451,
        recall=0.9983461962513782,
        f1=0.9966978536048432,
        accuracy=0.9982178500142572,
        tp=1811,
        fp=9,
        fn=3,
        tn=None,
        source_file="models/indobert_NER/checkpoint-500/trainer_state.json",
        source_lines="2,247,248,250,251",
        notes="Entity-level seqeval (TN tidak terdefinisi langsung).",
    ),
    SnapshotMetrics(
        model=MODEL_NER_DETAIL,
        snapshot="last_epoch",
        is_best=False,
        epoch=5.0,
        step=500,
        precision=0.9945085118066996,
        recall=0.9983461962513782,
        f1=0.9964236588720771,
        accuracy=0.9980752780153977,
        tp=1811,
        fp=10,
        fn=3,
        tn=None,
        source_file="models/indobert_NER/checkpoint-500/trainer_state.json",
        source_lines="411,412,414,415",
        notes="Entity-level seqeval (TN tidak terdefinisi langsung).",
    ),
    SnapshotMetrics(
        model=MODEL_REVISION_DETAIL,
        snapshot="best_model",
        is_best=True,
        epoch=3.0,
        step=1155,
        precision=1.0,
        recall=0.9975,
        f1=0.9987484355444305,
        accuracy=0.9986996098829649,
        tp=399,
        fp=0,
        fn=1,
        tn=369,
        source_file="models/indobert_revision_matcher/checkpoint-1540/trainer_state.json",
        source_lines="2,3,442,444,447,449",
    ),
    SnapshotMetrics(
        model=MODEL_REVISION_DETAIL,
        snapshot="last_epoch",
        is_best=False,
        epoch=4.0,
        step=1540,
        precision=0.9975,
        recall=0.9975,
        f1=0.9975,
        accuracy=0.9973992197659298,
        tp=399,
        fp=1,
        fn=1,
        tn=368,
        source_file="models/indobert_revision_matcher/checkpoint-1540/trainer_state.json",
        source_lines="597,599,602,604",
    ),
]

LATEST_METRICS = [m for m in METRICS if m.snapshot == "last_epoch"]


def _build_summary_df() -> pd.DataFrame:
    rows = []
    for m in LATEST_METRICS:
        rows.append(
            {
                COL_MODEL: m.model,
                "Epoch": m.epoch,
                "Step": m.step,
                "Precision": m.precision,
                "Recall": m.recall,
                "F1_Score": m.f1,
                "Accuracy": m.accuracy,
                "TP": m.tp,
                "FP": m.fp,
                "FN": m.fn,
                "TN": m.tn,
                "Source_File": m.source_file,
                "Source_Lines": m.source_lines,
                "Notes": m.notes,
            }
        )
    return pd.DataFrame(rows)


def _build_confusion_df() -> pd.DataFrame:
    rows = []
    for m in LATEST_METRICS:
        rows.append(
            {
                COL_MODEL: m.model,
                "TP": m.tp,
                "FP": m.fp,
                "FN": m.fn,
                "TN": m.tn,
                "Confusion_Matrix_Available": "YES" if m.tn is not None else "PARTIAL",
            }
        )
    return pd.DataFrame(rows)


def _to_markdown_safe(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        cols = list(df.columns)
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join(["---"] * len(cols)) + " |"
        rows = []
        for _, row in df.iterrows():
            rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        return "\n".join([header, sep] + rows)


def _save_table_files(summary_df: pd.DataFrame, confusion_df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "performance_summary.csv", index=False, encoding="utf-8")
    confusion_df.to_csv(out_dir / "confusion_matrix_summary.csv", index=False, encoding="utf-8")

    with open(out_dir / "performance_summary.md", "w", encoding="utf-8") as f:
        f.write("# Table 1. Model Performance Summary (Deep Learning Evaluation)\n\n")
        f.write(_to_markdown_safe(summary_df))
        f.write("\n\n# Table 2. Confusion Matrix Components\n\n")
        f.write(_to_markdown_safe(confusion_df))
        f.write("\n")

    with open(out_dir / "performance_summary.tex", "w", encoding="utf-8") as f:
        f.write("% Table 1. Model Performance Summary\n")
        f.write(summary_df.to_latex(index=False, float_format="%.6f"))
        f.write("\n\n% Table 2. Confusion Matrix Components\n")
        f.write(confusion_df.to_latex(index=False))


def _plot_metric_comparison(summary_df: pd.DataFrame, out_dir: Path, plt) -> None:
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        pass

    df_plot = summary_df.copy()
    df_plot["Label"] = df_plot[COL_MODEL]
    metrics = ["Precision", "Recall", "F1_Score"]
    x = range(len(df_plot))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    for idx, metric in enumerate(metrics):
        offsets = [p + (idx - 1) * width for p in x]
        ax.bar(offsets, df_plot[metric], width=width, label=metric)

    ax.set_xticks(list(x))
    ax.set_xticklabels(df_plot["Label"], rotation=20, ha="right")
    ax.set_ylim(0.95, 1.005)
    ax.set_ylabel("Score")
    ax.set_title("Precision / Recall / F1 Comparison")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "metric_comparison.png", dpi=240)
    plt.close(fig)


def _plot_confusion_component_comparison(summary_df: pd.DataFrame, out_dir: Path, plt) -> None:
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        pass

    df_plot = summary_df.copy()
    df_plot["Label"] = df_plot[COL_MODEL]
    df_plot["TN"] = df_plot["TN"].fillna(0)

    metrics = ["TP", "FP", "FN", "TN"]
    x = range(len(df_plot))
    width = 0.2

    fig, ax = plt.subplots(figsize=(13, 6))
    for idx, metric in enumerate(metrics):
        offsets = [p + (idx - 1.5) * width for p in x]
        ax.bar(offsets, df_plot[metric], width=width, label=metric)

    ax.set_xticks(list(x))
    ax.set_xticklabels(df_plot["Label"], rotation=20, ha="right")
    ax.set_ylabel("Count")
    ax.set_title("Confusion Components Comparison (TN for NER = 0 placeholder)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "confusion_component_comparison.png", dpi=240)
    plt.close(fig)


def _plot_revision_confusion_heatmaps(summary_df: pd.DataFrame, out_dir: Path, plt) -> None:
    rev_df = summary_df[
        (summary_df[COL_MODEL] == MODEL_REVISION_DETAIL) & (summary_df["TN"].notna())
    ].copy()

    for _, row in rev_df.iterrows():
        tn = int(row["TN"])
        fp = int(row["FP"])
        fn = int(row["FN"])
        tp = int(row["TP"])
        cm = [[tn, fp], [fn, tp]]

        fig, ax = plt.subplots(figsize=(5.8, 5.0))
        im = ax.imshow(cm, cmap="Blues")
        ax.set_xticks([0, 1], labels=["Pred NO_MATCH", "Pred MATCH"])
        ax.set_yticks([0, 1], labels=["True NO_MATCH", "True MATCH"])
        ax.set_title("Revision Matcher Confusion Matrix - Last Checkpoint")

        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i][j]), ha="center", va="center", color="black", fontsize=11)

        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(out_dir / "confusion_matrix_revision_matcher_last_checkpoint.png", dpi=240)
        plt.close(fig)


def _generate_static_plots(summary_df: pd.DataFrame, out_dir: Path) -> bool:
    plt = _get_matplotlib()
    if plt is None:
        return False

    _plot_metric_comparison(summary_df, out_dir, plt)
    _plot_confusion_component_comparison(summary_df, out_dir, plt)
    _plot_revision_confusion_heatmaps(summary_df, out_dir, plt)
    return True


def _in_streamlit_context() -> bool:
    import sys

    if "streamlit" not in sys.modules:
        return False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore

        return get_script_run_ctx() is not None
    except Exception:
        return False


def _render_streamlit_dashboard(summary_df: pd.DataFrame, confusion_df: pd.DataFrame, out_dir: Path) -> None:
    import streamlit as st  # type: ignore

    st.set_page_config(page_title="Deep Learning Performance Dashboard", layout="wide")
    st.title("Deep Learning Performance Dashboard")
    st.caption(f"Model: {MODEL_NER_DETAIL} dan {MODEL_REVISION_DETAIL}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Models", f"{len(summary_df)}")
    c2.metric("Models", f"{summary_df[COL_MODEL].nunique()}")
    c3.metric("Output Folder", str(out_dir))

    summary_view = summary_df.copy()
    summary_view["Precision"] = summary_view["Precision"].round(6)
    summary_view["Recall"] = summary_view["Recall"].round(6)
    summary_view["F1_Score"] = summary_view["F1_Score"].round(6)
    summary_view["Accuracy"] = summary_view["Accuracy"].round(6)

    tab_overview, tab_ner, tab_revision = st.tabs(
        [
            "Overview (Paper Tables)",
            f"Confusion - {MODEL_NER_DETAIL}",
            f"Confusion - {MODEL_REVISION_DETAIL}",
        ]
    )

    with tab_overview:
        st.subheader("Table 1. Model Performance Summary")
        st.dataframe(summary_view, use_container_width=True, hide_index=True)

        st.subheader("Table 2. Confusion Matrix Components")
        st.dataframe(confusion_df, use_container_width=True, hide_index=True)

        metric_png = out_dir / "metric_comparison.png"
        component_png = out_dir / "confusion_component_comparison.png"
        if metric_png.exists():
            st.image(str(metric_png), caption="Figure 1. Precision / Recall / F1 Comparison")
        if component_png.exists():
            st.image(str(component_png), caption="Figure 2. Confusion Components (TP/FP/FN/TN)")

    with tab_ner:
        st.subheader(f"{MODEL_NER_DETAIL} - Confusion Metrics")
        ner = confusion_df[confusion_df[COL_MODEL] == MODEL_NER_DETAIL].copy()
        st.dataframe(ner, use_container_width=True, hide_index=True)
        st.info("Untuk NER (entity-level seqeval), TN tidak didefinisikan secara langsung.")

        ner_long = ner.melt(
            id_vars=[COL_MODEL],
            value_vars=["TP", "FP", "FN"],
            var_name="Metric",
            value_name="Count",
        )
        pivot_ner = ner_long.pivot(index=COL_MODEL, columns="Metric", values="Count")
        st.bar_chart(pivot_ner, use_container_width=True)

    with tab_revision:
        st.subheader(f"{MODEL_REVISION_DETAIL} - Full Confusion Matrix")
        rev = confusion_df[confusion_df[COL_MODEL] == MODEL_REVISION_DETAIL].copy()
        st.dataframe(rev, use_container_width=True, hide_index=True)

        plt = _get_matplotlib()
        for _, row in rev.iterrows():
            st.markdown("**Last Checkpoint**")
            tn = int(row["TN"])
            fp = int(row["FP"])
            fn = int(row["FN"])
            tp = int(row["TP"])
            cm_df = pd.DataFrame(
                [[tn, fp], [fn, tp]],
                index=["True NO_MATCH", "True MATCH"],
                columns=["Pred NO_MATCH", "Pred MATCH"],
            )
            st.table(cm_df)
            st.bar_chart(
                pd.DataFrame(
                    [{"TN": tn, "FP": fp, "FN": fn, "TP": tp}],
                    index=["last_checkpoint"],
                ),
                use_container_width=True,
            )

            if plt is not None:
                fig, ax = plt.subplots(figsize=(5.5, 4.6))
                im = ax.imshow(cm_df.values, cmap="Blues")
                ax.set_xticks([0, 1], labels=list(cm_df.columns))
                ax.set_yticks([0, 1], labels=list(cm_df.index))
                ax.set_title("Confusion Matrix - Last Checkpoint")
                for i in range(2):
                    for j in range(2):
                        ax.text(j, i, str(cm_df.values[i, j]), ha="center", va="center", color="black")
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                fig.tight_layout()
                st.pyplot(fig, use_container_width=False)
                plt.close(fig)


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    out_dir = root_dir / "performance_outputs"

    summary_df = _build_summary_df()
    confusion_df = _build_confusion_df()

    _save_table_files(summary_df, confusion_df, out_dir)
    has_static_plot = _generate_static_plots(summary_df, out_dir)

    if _in_streamlit_context():
        _render_streamlit_dashboard(summary_df, confusion_df, out_dir)
        return

    print("\n=== TABLE 1. MODEL PERFORMANCE SUMMARY ===")
    print(_to_markdown_safe(summary_df))
    print("\n=== TABLE 2. CONFUSION MATRIX COMPONENTS ===")
    print(_to_markdown_safe(confusion_df))
    print(f"\nOutput tersimpan di: {out_dir}")
    if not has_static_plot:
        print("Catatan: matplotlib tidak tersedia, sehingga file grafik tidak dibuat.")
    else:
        print("Grafik dibuat: metric comparison, confusion component, confusion matrices.")


if __name__ == "__main__":
    main()
