import pandas as pd

import streamlit as st
import firebase_admin
from firebase_admin import db, credentials


DEFAULT_SOURCE = "PGM"
SOURCE_MAP = {
    "PGM": "pgm",
    "Kitco": "kitco",
    "Yahoo Gold": "yh_gld",
    "Yahoo GSPC": "yh_sp500",
    "Yahoo FTSE": "yh_ftse",
}

DB_URL = st.secrets["DATABASE"]["DB_URL"]


def connect_firebase():
    if not firebase_admin._apps:
        firebase_cred = dict(st.secrets["FIREBASE"])
        cred = credentials.Certificate(firebase_cred)
        firebase_admin.initialize_app(
            cred,
            {"databaseURL": DB_URL},
        )
    return db.reference("/")


@st.cache_data
def get_data(name):
    ref = connect_firebase()
    source_ref = ref.child(name)
    data = source_ref.get()
    df = pd.DataFrame.from_dict(data, orient="index")
    df.index = pd.to_datetime(df.index, errors="coerce").date
    return df


st.set_page_config(
    page_title="Data Visualization Dashboard", 
    page_icon="🪙", 
    layout="wide"
)
st.header("Metal Prices Dashboard")
cols = st.columns([1, 3])

top_left_cell = cols[0].container(
    border=True, 
    height="stretch", 
    vertical_alignment="center"
)

bottom_left_cell = cols[0].container(
    border=True, 
    height="stretch", 
    vertical_alignment="center"
)

right_cell = cols[1].container(
    border=True, 
    height="stretch", 
    vertical_alignment="center"
)


def metals_to_str(metals):
    return ",".join(metals)


if "metals_input" not in st.session_state:
    st.session_state.metals_input = st.query_params.get(
        "metals", metals_to_str(get_data(SOURCE_MAP[DEFAULT_SOURCE]))
    ).split(",")


def update_query_param():
    if st.session_state.metals_input:
        st.query_params["metals"] = metals_to_str(st.session_state.metals_input)
    else:
        st.query_params.pop("metals", None)


with top_left_cell:
    source_choice = st.selectbox(
        "Source",
        options=list(SOURCE_MAP.keys()),
        index=list(SOURCE_MAP.keys()).index(DEFAULT_SOURCE),
    )

    df = get_data(SOURCE_MAP[source_choice])

    if (
        "last_source" not in st.session_state
        or st.session_state.last_source != source_choice
    ):
        st.session_state.metals_input = df.columns.tolist()[:4]
        st.session_state.last_source = source_choice

    metals = st.multiselect(
        "Parameters",
        options=list(df.columns),
        default=st.session_state.metals_input,
        placeholder="Choose parameters",
        key="metals_input",
        accept_new_options=False,
    )

    max_date = df.index.max()
    min_date = df.index.min()

    start_date = st.date_input("Start date", min_date, min_date, max_date)
    end_date = st.date_input("End date", max_date, min_date, max_date)

    mask = (df.index >= start_date) & (df.index <= end_date)

    show_df = st.checkbox("Show Dataframe")

if metals:
    st.query_params["metals"] = metals_to_str(metals)
else:
    st.query_params.pop("metals", None)

if not metals:
    top_left_cell.info("Pick some parametrs", icon=":material/info:")
    st.stop()

with right_cell:
    st.line_chart(
        df.loc[mask, metals],
        width='stretch',
        height=500,
        x_label="Date",
        y_label="Price",
    )

with bottom_left_cell:
    st.write("**Today's prices (USD)**")
    for met in metals:
        st.write(f"{met}: {df[met][max_date]}")

if show_df:
    st.write("Historical Data")
    st.dataframe(df.loc[mask, metals])
