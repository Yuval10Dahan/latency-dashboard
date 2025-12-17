import streamlit as st
st.set_page_config(page_title="Latency Test Results", layout="wide", initial_sidebar_state="expanded")

import os
import pandas as pd
from sqlalchemy import create_engine
from PIL import Image
import io



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

    desired_order = [
        'id',
        'product_name',
        'datetime',
        'serial_number',
        'part_number',
        'hardware_version',
        'firmware_version',
        'traffic_generator_application',
        'system_mode',
        'client_service_type',
        'client_fec_mode',
        'uplink_service_type',
        'uplink_fec_mode',
        'modulation_format',
        'uplink_transceiver',   
        'frame_size',
        'result',
    ]
    # keep only columns that actually exist
    df = df[[c for c in desired_order if c in df.columns]]
    
    return df

df = load_data()

# --- Display logo above title ---
logo_path = os.path.join(os.path.dirname(__file__), 'Packetlight Logo.png')
st.image(Image.open(logo_path), width=250)
st.title("PacketLight - Latency Results")
st.subheader("(The measurement was taken using a setup with 2 devices)")

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
    'uplink_transceiver': 'Uplink Transceiver',
    'frame_size': 'Frame Size',
    'result': 'Latency (uSecs)'
}

# --- Sidebar Filters and Column Toggles ---
with st.sidebar:
    st.subheader("Contact: Yuval Dahan")

    # -------------------------------------------------------------------------------------------------- #

    st.header("🔍 Filters")

    # Start with full df
    filtered_options_df = df.copy()

    # Collect user selections (initially unfiltered)
    selected_product = st.multiselect("Product Name", sorted(df['product_name'].dropna().unique()))
    if selected_product:
        filtered_options_df = filtered_options_df[filtered_options_df['product_name'].isin(selected_product)]

    selected_hw = st.multiselect("Hardware Version", sorted(filtered_options_df['hardware_version'].dropna().unique()))
    if selected_hw:
        filtered_options_df = filtered_options_df[filtered_options_df['hardware_version'].isin(selected_hw)]

    selected_fw = st.multiselect("Firmware Version", sorted(filtered_options_df['firmware_version'].dropna().unique()))
    if selected_fw:
        filtered_options_df = filtered_options_df[filtered_options_df['firmware_version'].isin(selected_fw)]

    selected_traffic_app = st.multiselect("Traffic Generator Application", sorted(filtered_options_df['traffic_generator_application'].dropna().unique()))
    if selected_traffic_app:
        filtered_options_df = filtered_options_df[filtered_options_df['traffic_generator_application'].isin(selected_traffic_app)]

    selected_mode = st.multiselect("System Mode", sorted(filtered_options_df['system_mode'].dropna().unique()))
    if selected_mode:
        filtered_options_df = filtered_options_df[filtered_options_df['system_mode'].isin(selected_mode)]

    selected_client = st.multiselect("Client Service Type", sorted(filtered_options_df['client_service_type'].dropna().unique()))
    if selected_client:
        filtered_options_df = filtered_options_df[filtered_options_df['client_service_type'].isin(selected_client)]

    selected_client_fec = st.multiselect("Client FEC Mode", sorted(filtered_options_df['client_fec_mode'].dropna().unique()))
    if selected_client_fec:
        filtered_options_df = filtered_options_df[filtered_options_df['client_fec_mode'].isin(selected_client_fec)]

    selected_uplink = st.multiselect("Uplink Service Type", sorted(filtered_options_df['uplink_service_type'].dropna().unique()))
    if selected_uplink:
        filtered_options_df = filtered_options_df[filtered_options_df['uplink_service_type'].isin(selected_uplink)]

    selected_uplink_fec = st.multiselect("Uplink FEC Mode", sorted(filtered_options_df['uplink_fec_mode'].dropna().unique()))
    if selected_uplink_fec:
        filtered_options_df = filtered_options_df[filtered_options_df['uplink_fec_mode'].isin(selected_uplink_fec)]

    selected_modulation = st.multiselect("Modulation Format", sorted(filtered_options_df['modulation_format'].dropna().unique()))
    if selected_modulation:
        filtered_options_df = filtered_options_df[filtered_options_df['modulation_format'].isin(selected_modulation)]

    selected_uplink_transceiver = st.multiselect("Uplink Transceiver", sorted(filtered_options_df['uplink_transceiver'].dropna().unique()))
    if selected_uplink_transceiver:
        filtered_options_df = filtered_options_df[filtered_options_df['uplink_transceiver'].isin(selected_uplink_transceiver)]

    selected_frame_size = st.multiselect("Frame Size", sorted(filtered_options_df['frame_size'].dropna().unique()))
    if selected_frame_size:
        filtered_options_df = filtered_options_df[filtered_options_df['frame_size'].isin(selected_frame_size)]

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
if selected_product:
    filtered_df = filtered_df[filtered_df['product_name'].isin(selected_product)]
if selected_hw:
    filtered_df = filtered_df[filtered_df['hardware_version'].isin(selected_hw)]
if selected_fw:
    filtered_df = filtered_df[filtered_df['firmware_version'].isin(selected_fw)]
if selected_traffic_app:
    filtered_df = filtered_df[filtered_df['traffic_generator_application'].isin(selected_traffic_app)]
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
if selected_uplink_transceiver:
    filtered_df = filtered_df[filtered_df['uplink_transceiver'].isin(selected_uplink_transceiver)]
if selected_frame_size:
    filtered_df = filtered_df[filtered_df['frame_size'].isin(selected_frame_size)]
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



# =========================================== Download Options ============================================== #

# # ============ option 1 =========== #
# # --- Optional Download ---
# csv = display_df[selected_columns].to_csv(index=False)
# st.download_button("Download Filtered Results - Excel File", csv, "latency_results.csv", "text/csv")


# ============ option 3 =========== # 
# --- Optional Download as real Excel with professional formatting ---
export_df = display_df[selected_columns]

output = io.BytesIO()

with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    sheet_name = "Latency Results"

    # Offset table by 5 rows to place logo + title
    export_df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=5)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # ===== Insert PacketLight Logo =====
    logo_path = os.path.join(os.path.dirname(__file__), "Packetlight Logo.png")
    worksheet.insert_image('A1', logo_path, {'x_scale': 0.5, 'y_scale': 0.5})

    # ===== Title =====
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'left',
        'valign': 'vcenter'
    })
    worksheet.write('A4', 'PacketLight Latency Test Results', title_format)

    # ===== Header Formatting =====
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#D9E1F2',
        'border': 1
    })

    # Rewrite header row with formatting
    for col_num, value in enumerate(export_df.columns.values):
        worksheet.write(5, col_num, value, header_format)

    # ===== Cell Formatting =====
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    # Apply formatting to all data rows
    for row in range(len(export_df)):
        for col in range(len(export_df.columns)):
            worksheet.write(row + 6, col, export_df.iloc[row, col], cell_format)

    # ===== Auto-fit column widths =====
    for i, col in enumerate(export_df.columns):
        max_len = max(export_df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, max_len)

    # ===== Freeze Header =====
    worksheet.freeze_panes(6, 0)

output.seek(0)

st.download_button(
    "Download Filtered Results - Excel File",
    data=output,
    file_name="latency_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)