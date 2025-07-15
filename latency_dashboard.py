import streamlit as st
st.set_page_config(page_title="Latency Test Results", layout="wide", initial_sidebar_state="expanded")

import os
import pandas as pd
from sqlalchemy import create_engine
from PIL import Image

# --- DB Connection ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'latency_results.db')
engine = create_engine(f'sqlite:///{DB_PATH}')

@st.cache_data
def load_data():
    df = pd.read_sql('SELECT * FROM test_results', engine)

    # Format datetime
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Convert result to numeric
    if 'result' in df.columns:
        df['result'] = pd.to_numeric(df['result'], errors='coerce')

    # Drop unused columns
    # df = df.drop(columns=[col for col in ['step', 'id'] if col in df.columns])
    df = df.drop(columns=[col for col in ['step'] if col in df.columns])
    return df

df = load_data()

# --- Display logo above title ---
logo_path = os.path.join(os.path.dirname(__file__), 'Packetlight Logo.png')
st.image(Image.open(logo_path), width=250)
st.title("PacketLight - Latency Results")

# --- Define renamed display columns ---
display_columns_map = {
    'id': 'ID',
    'product_name': 'Product Name',
    'datetime': 'Date & Time',
    'serial_number': 'Serial Number',
    'part_number': 'Part Number',
    'hardware_version': 'Hardware Version',
    'firmware_version': 'Firmware Version',
    'traffic_generator_application': 'Traffic Generator Application',
    'system_mode': 'System Mode',
    'client_service_type': 'Client Service Type',
    'client_fec_mode': 'Client FEC Mode',
    'uplink_service_type': 'Uplink Service Type',
    'uplink_fec_mode': 'Uplink FEC Mode',
    'modulation_format': 'Modulation Format',
    'frame_size': 'Frame Size',
    'result': 'Latency (uSecs)'
}

# --- Sidebar Filters and Column Toggles ---
with st.sidebar:
    st.subheader("Contact: Yuval Dahan")

    # -------------------------------------------------------------------------------------------------- #

    st.header("🔍 Filters")

    # --- Define all columns you want to allow filtering on ---
    filter_columns = [
        'product_name', 'hardware_version', 'firmware_version',
        'traffic_generator_application', 'system_mode',
        'client_service_type', 'client_fec_mode',
        'uplink_service_type', 'uplink_fec_mode',
        'modulation_format', 'frame_size'
    ]

    # --- Build selections from user input ---
    selections = {}
    for col in filter_columns:
        label = display_columns_map.get(col, col.replace('_', ' ').title())
        selections[col] = st.multiselect(label, sorted(df[col].dropna().unique()))

    # --- Apply all filters at once ---
    filtered_df = df.copy()
    for col, selected_vals in selections.items():
        if selected_vals:
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

    # --- Rebuild available options based on filtered_df ---
    for col in filter_columns:
        label = display_columns_map.get(col, col.replace('_', ' ').title())
        if not selections[col]:
            st.multiselect(
                label,
                sorted(filtered_df[col].dropna().unique()),
                key=col
            )

    # -------------------------------------------------------------------------------------------------- #

    st.header("🆔 Filter by ID")
    id_input = st.text_input("Enter IDs (comma-separated)", value="")
    id_list = []
    if id_input.strip():
        try:
            id_list = [int(x.strip()) for x in id_input.split(",") if x.strip().isdigit()]
        except ValueError:
            st.warning("Please enter only integers separated by commas.")

    # -------------------------------------------------------------------------------------------------- #

    st.header("⏱️ Latency Filter (μSec)")
    latency_filter_type = st.radio("Filter by Latency:", ["Show All", "Above", "Below"], horizontal=True)
    latency_threshold = st.number_input("Latency Threshold (μSec)", min_value=0.0, step=0.1)

    # -------------------------------------------------------------------------------------------------- #

    st.header("🧩 Columns to Display")
    st.caption("Toggle columns on/off to display in the table:")

    checkbox_columns = {}
    for col in df.rename(columns=display_columns_map).columns:
        checkbox_columns[col] = st.checkbox(col, value=True)
    selected_columns = [col for col, show in checkbox_columns.items() if show]

    # -------------------------------------------------------------------------------------------------- #

# --- Apply filters ---
filtered_df = df.copy()
for key, selected_vals in selections.items():
    if selected_vals:
        filtered_df = filtered_df[filtered_df[key].isin(selected_vals)]

if id_list:
    filtered_df = filtered_df[filtered_df['id'].isin(id_list)]

if latency_filter_type == "Above":
    filtered_df = filtered_df[filtered_df['result'] > latency_threshold]
elif latency_filter_type == "Below":
    filtered_df = filtered_df[filtered_df['result'] < latency_threshold]


# --- Rename columns for display ---
display_df = filtered_df.rename(columns=display_columns_map)

# --- Display Results ---
st.subheader(f"Showing {len(display_df)} Records")
st.dataframe(display_df[selected_columns], use_container_width=True)

# --- Optional Download ---
csv = display_df[selected_columns].to_csv(index=False)
st.download_button("Download Filtered Results - Excel File", csv, "latency_results.csv", "text/csv")
