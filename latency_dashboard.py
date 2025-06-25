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

    # Drop unused columns
    df = df.drop(columns=[col for col in ['step', 'id'] if col in df.columns])
    return df

df = load_data()

# --- Display logo above title ---
logo_path = os.path.join(os.path.dirname(__file__), 'Packetlight Logo.png')
st.image(Image.open(logo_path), width=250)
st.title("PacketLight - Latency Results")

# --- Define renamed display columns ---
display_columns_map = {
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

    st.header("🧩 Columns to Display")
    st.caption("Toggle columns on/off to display in the table:")

    checkbox_columns = {}
    for col in df.rename(columns=display_columns_map).columns:
        checkbox_columns[col] = st.checkbox(col, value=True)
    selected_columns = [col for col, show in checkbox_columns.items() if show]

    st.header("🔍 Filters")
    selected_product = st.multiselect("Product Name", df['product_name'].dropna().unique())
    selected_hw = st.multiselect("Hardware Version", df['hardware_version'].dropna().unique())
    selected_fw = st.multiselect("Firmware Version", df['firmware_version'].dropna().unique())
    selected_mode = st.multiselect("System Mode", df['system_mode'].dropna().unique())
    selected_client = st.multiselect("Client Service Type", df['client_service_type'].dropna().unique())
    selected_client_fec = st.multiselect("Client FEC Mode", df['client_fec_mode'].dropna().unique())
    selected_uplink = st.multiselect("Uplink Service Type", df['uplink_service_type'].dropna().unique())
    selected_uplink_fec = st.multiselect("Uplink FEC Mode", df['uplink_fec_mode'].dropna().unique())
    selected_modulation = st.multiselect("Modulation Format", df['modulation_format'].dropna().unique())
    selected_frame_size = st.multiselect("Frame Size", sorted(df['frame_size'].dropna().unique()))

# --- Apply filters ---
filtered_df = df.copy()
if selected_product:
    filtered_df = filtered_df[filtered_df['product_name'].isin(selected_product)]
if selected_hw:
    filtered_df = filtered_df[filtered_df['hardware_version'].isin(selected_hw)]
if selected_fw:
    filtered_df = filtered_df[filtered_df['firmware_version'].isin(selected_fw)]
if selected_mode:
    filtered_df = filtered_df[filtered_df['system_mode'].isin(selected_mode)]
if selected_client:
    filtered_df = filtered_df[filtered_df['client_service_type'].isin(selected_client)]
if selected_client_fec:
    filtered_df = filtered_df[filtered_df['client_fec_mode'].isin(selected_client_fec)]
if selected_uplink:
    filtered_df = filtered_df[filtered_df['uplink_service_type'].isin(selected_uplink)]
if selected_uplink_fec:
    filtered_df = filtered_df[filtered_df['uplink_fec_mode'].isin(selected_uplink_fec)]
if selected_modulation:
    filtered_df = filtered_df[filtered_df['modulation_format'].isin(selected_modulation)]
if selected_frame_size:
    filtered_df = filtered_df[filtered_df['frame_size'].isin(selected_frame_size)]

# --- Rename columns for display ---
display_df = filtered_df.rename(columns=display_columns_map)

# --- Display Results ---
st.subheader(f"Showing {len(display_df)} Records")
st.dataframe(display_df[selected_columns], use_container_width=True)

# --- Optional Download ---
csv = display_df[selected_columns].to_csv(index=False)
st.download_button("Download Filtered Results - Excel File", csv, "latency_results.csv", "text/csv")
