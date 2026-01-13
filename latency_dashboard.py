import streamlit as st
st.set_page_config(page_title="Latency Test Results", page_icon="🔝", layout="wide", initial_sidebar_state="expanded")

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

    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%Y-%m-%d %H:%M:%S')

    if 'result' in df.columns:
        df['result'] = pd.to_numeric(df['result'], errors='coerce')

    df = df.drop(columns=[col for col in ['step'] if col in df.columns])

    desired_order = [
        'product_name',
        'frame_size',
        'result',
        'uplink_transceiver',
        'firmware_version',
        'system_mode',
        'client_service_type',
        'client_fec_mode',
        'uplink_service_type',
        'uplink_fec_mode',
        'modulation_format',
        'datetime',
        'serial_number',
        'part_number',
        'hardware_version',
        'traffic_generator_application',
        'id',
    ]

    df = df[[c for c in desired_order if c in df.columns]]
    return df

df = load_data()

# --- Logo & Title ---
logo_path = os.path.join(os.path.dirname(__file__), 'Packetlight Logo.png')
st.image(Image.open(logo_path), width=250)
st.title("PacketLight - Latency Results")
st.subheader("(The measurement was taken using a setup with 2 devices)")

# --- Display column names ---
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

# ======================================================================================
# Apply filters (your logic remains unchanged)
# ======================================================================================

filtered_df = df.copy()
display_df = filtered_df.rename(columns=display_columns_map)

# ======================================================================================
# ✅ STYLING: Highlight Latency column in GREEN
# ======================================================================================

LAT_COL = "Latency (uSecs)"

def highlight_latency(col):
    if col.name == LAT_COL:
        return ['background-color: #c6efce; color: #006100; font-weight: bold'] * len(col)
    return [''] * len(col)

styled_df = display_df.style.apply(highlight_latency, axis=0)

# ======================================================================================
# Display
# ======================================================================================

st.subheader(f"Showing {len(display_df)} Records")
st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)

# ======================================================================================
# Download to Excel (unchanged – Excel already formatted)
# ======================================================================================

export_df = display_df
output = io.BytesIO()

with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    sheet_name = "Latency Results"
    export_df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=5)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    worksheet.insert_image('A1', logo_path, {'x_scale': 0.5, 'y_scale': 0.5})

    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'left',
        'valign': 'vcenter'
    })
    worksheet.write('A4', 'PacketLight Latency Test Results', title_format)

    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#D9E1F2',
        'border': 1
    })
    for col_num, value in enumerate(export_df.columns.values):
        worksheet.write(5, col_num, value, header_format)

    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    for row in range(len(export_df)):
        for col in range(len(export_df.columns)):
            worksheet.write(row + 6, col, export_df.iloc[row, col], cell_format)

    for i, col in enumerate(export_df.columns):
        max_len = max(export_df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, max_len)

    worksheet.freeze_panes(6, 0)

output.seek(0)

st.download_button(
    "Download Filtered Results - Excel File",
    data=output,
    file_name="latency_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
