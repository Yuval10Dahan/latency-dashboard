import streamlit as st
import os
import pandas as pd
from sqlalchemy import create_engine
from PIL import Image

st.set_page_config(page_title="Latency Test Results", layout="wide", initial_sidebar_state="expanded")

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
    df = df.drop(columns=[col for col in ['step'] if col in df.columns])
    return df

df = load_data()

# --- Display logo above title ---
logo_path = os.path.join(os.path.dirname(__file__), 'Packetlight Logo.png')
if os.path.exists(logo_path):
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
    st.header("🔍 Filters")

    # Initialize all filter fields
    all_filters = {
        "product_name": None,
        "hardware_version": None,
        "firmware_version": None,
        "traffic_generator_application": None,
        "system_mode": None,
        "client_service_type": None,
        "client_fec_mode": None,
        "uplink_service_type": None,
        "uplink_fec_mode": None,
        "modulation_format": None,
        "frame_size": None
    }

    # Two-pass update to allow all interdependencies to resolve
    for _ in range(2):
        filtered_options_df = df.copy()
        for key, value in all_filters.items():
            if value:
                filtered_options_df = filtered_options_df[filtered_options_df[key].isin(value)]

        # Multiselects with dynamically updated options
        all_filters["product_name"] = st.multiselect("Product Name", sorted(filtered_options_df['product_name'].dropna().unique()), default=all_filters["product_name"])
        all_filters["hardware_version"] = st.multiselect("Hardware Version", sorted(filtered_options_df['hardware_version'].dropna().unique()), default=all_filters["hardware_version"])
        all_filters["firmware_version"] = st.multiselect("Firmware Version", sorted(filtered_options_df['firmware_version'].dropna().unique()), default=all_filters["firmware_version"])
        all_filters["traffic_generator_application"] = st.multiselect("Traffic Generator Application", sorted(filtered_options_df['traffic_generator_application'].dropna().unique()), default=all_filters["traffic_generator_application"])
        all_filters["system_mode"] = st.multiselect("System Mode", sorted(filtered_options_df['system_mode'].dropna().unique()), default=all_filters["system_mode"])
        all_filters["client_service_type"] = st.multiselect("Client Service Type", sorted(filtered_options_df['client_service_type'].dropna().unique()), default=all_filters["client_service_type"])
        all_filters["client_fec_mode"] = st.multiselect("Client FEC Mode", sorted(filtered_options_df['client_fec_mode'].dropna().unique()), default=all_filters["client_fec_mode"])
        all_filters["uplink_service_type"] = st.multiselect("Uplink Service Type", sorted(filtered_options_df['uplink_service_type'].dropna().unique()), default=all_filters["uplink_service_type"])
        all_filters["uplink_fec_mode"] = st.multiselect("Uplink FEC Mode", sorted(filtered_options_df['uplink_fec_mode'].dropna().unique()), default=all_filters["uplink_fec_mode"])
        all_filters["modulation_format"] = st.multiselect("Modulation Format", sorted(filtered_options_df['modulation_format'].dropna().unique()), default=all_filters["modulation_format"])
        all_filters["frame_size"] = st.multiselect("Frame Size", sorted(filtered_options_df['frame_size'].dropna().unique()), default=all_filters["frame_size"])

    st.header("🆔 Filter by ID")
    id_input = st.text_input("Enter IDs (comma-separated)", value="")
    id_list = []
    if id_input.strip():
        try:
            id_list = [int(x.strip()) for x in id_input.split(",") if x.strip().isdigit()]
        except ValueError:
            st.warning("Please enter only integers separated by commas.")

    st.header("⏱️ Latency Filter (μSec)")
    latency_filter_type = st.radio("Filter by Latency:", ["Show All", "Above", "Below"], horizontal=True)
    latency_threshold = st.number_input("Latency Threshold (μSec)", min_value=0.0, step=0.1)

    st.header("🧩 Columns to Display")
    st.caption("Toggle columns on/off to display in the table:")
    checkbox_columns = {}
    for col in df.rename(columns=display_columns_map).columns:
        checkbox_columns[col] = st.checkbox(col, value=True)
    selected_columns = [col for col, show in checkbox_columns.items() if show]

# --- Apply Filters ---
filtered_df = df.copy()
for key, values in all_filters.items():
    if values:
        filtered_df = filtered_df[filtered_df[key].isin(values)]

if id_list:
    filtered_df = filtered_df[filtered_df['id'].isin(id_list)]

if latency_filter_type == "Above":
    filtered_df = filtered_df[filtered_df['result'] > latency_threshold]
elif latency_filter_type == "Below":
    filtered_df = filtered_df[filtered_df['result'] < latency_threshold]

# --- Display Results ---
display_df = filtered_df.rename(columns=display_columns_map)
st.subheader(f"Showing {len(display_df)} Records")
st.dataframe(display_df[selected_columns], use_container_width=True)

# --- Optional Download ---
csv = display_df[selected_columns].to_csv(index=False)
st.download_button("Download Filtered Results - Excel File", csv, "latency_results.csv", "text/csv")
