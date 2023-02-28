#!/usr/bin/env python3
import streamlit as st

import evaluator.state as sta
import pandas as pd
import os
import nervaluate

st.title("View results (v0)")

PREFIX = "NERONE_VIEW_V0"
NERONE_HOME = os.path.join(os.getenv("HOME"), "repos", "nerone_mvn")
NERONE_EVAL_OUT = os.path.join(NERONE_HOME, "output", "evaluation")


@st.cache_data
def load_csv(path):
    df = pd.read_csv(path)
    return df


def dataset_runs_dir(dataset):
    return os.path.join(NERONE_EVAL_OUT, dataset)


# @sta.with_prop("dataset", "", PREFIX)
# @sta.with_prop("eval_run", "", PREFIX)
@sta.keygetter(PREFIX)
class State:
    dataset: str
    ...


state = State()


@st.cache_data
def run_evaluator(_ev: nervaluate.Evaluator):
    return _ev.evaluate()


def df_to_prodigy_spans(df: pd.DataFrame):
    spans = []
    for _, row in df.iterrows():
        spans.append({"label": row.ETYPE, "start": row.START, "end": row.END})

    return [spans]


def ner_metrics(m_dict):
    columns_0 = st.columns(5)
    with columns_0[0]:
        st.metric("predicted", f"{m_dict['actual']}/{m_dict['possible']}")
    with columns_0[1]:
        st.metric("correct", f"{m_dict['correct']}/{m_dict['possible']}")
    with columns_0[2]:
        st.metric("incorrect", f"{m_dict['incorrect']}/{m_dict['possible']}")
    with columns_0[3]:
        st.metric("missed", f"{m_dict['missed']}/{m_dict['possible']}")
    with columns_0[4]:
        st.metric("spurious", f"{m_dict['spurious']}")

    columns_1 = st.columns(3)

    with columns_1[0]:
        st.metric("precision", m_dict["precision"])

    with columns_1[1]:
        st.metric("recall", m_dict["recall"])

    with columns_1[2]:
        st.metric("f1", f"{m_dict['f1']:.4f}")


def main():
    ev_configs = os.listdir(NERONE_EVAL_OUT)
    # st.write(datasets)

    ev_config = st.selectbox("eval_config", options=ev_configs, key="chosen_ev_config")

    ev_dir = dataset_runs_dir(ev_config)
    runs = os.listdir(ev_dir)

    the_run = st.selectbox("run", options=runs, key="chosen_run")

    run_path = os.path.join(ev_dir, the_run)

    datasets = os.listdir(run_path)

    the_dataset = st.selectbox("dataset", options=datasets, key="chosen_dataset")

    dataset_path = os.path.join(run_path, the_dataset)

    # st.write(os.listdir(dataset_path))

    expected_df = load_csv(os.path.join(dataset_path, "expected.csv"))
    predicted_df = load_csv(os.path.join(dataset_path, "predicted.csv"))

    expected_spans = df_to_prodigy_spans(expected_df)
    predicted_spans = df_to_prodigy_spans(predicted_df)

    with st.expander("tables"):
        c0, c1 = st.columns(2)
        with c0:
            st.header("Expected")
            st.dataframe(expected_df)
            st.json(expected_spans, expanded=False)

        with c1:
            st.header("Predicted")
            st.dataframe(predicted_df)
            st.json(predicted_spans, expanded=False)

    ev = nervaluate.Evaluator(
        expected_spans, predicted_spans, tags=["LOCATION", "PERSON", "ORGANIZATION"]
    )

    results, results_per_tag = run_evaluator(ev)

    st.json(results, expanded=False)

    for result_kind, m_dict in results.items():
        st.header(f"Kind: {result_kind}")
        ner_metrics(m_dict)

    st.json(results_per_tag, expanded=False)

    for etype, desc in results_per_tag.items():
        with st.expander(f"Results for {etype}"):
            st.header(f"Entity Type: {etype}")
            for result_kind, m_dict in desc.items():
                st.header(f"Kind: {result_kind}")
                ner_metrics(m_dict)


main()
