import streamlit as st
st.set_page_config(page_title="Latency Test Results", page_icon= "🔝",layout="wide", initial_sidebar_state="expanded")

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

# ======================================================================================
# Query-params persistence helpers (survive F5 refresh)
# ======================================================================================

QP = st.query_params  # dict-like

def qp_get_list(key: str) -> list[str]:
    if key not in QP:
        return []
    val = QP.get(key)
    if isinstance(val, list):
        out = []
        for x in val:
            out.extend([p for p in str(x).split(",") if p != ""])
        return out
    return [p for p in str(val).split(",") if p != ""]

def qp_get_str(key: str, default: str = "") -> str:
    if key not in QP:
        return default
    val = QP.get(key)
    if isinstance(val, list):
        return str(val[0]) if val else default
    return str(val)

def qp_get_float(key: str, default: float = 0.0) -> float:
    s = qp_get_str(key, "")
    try:
        return float(s)
    except Exception:
        return default

def qp_set_list(key: str, values: list) -> None:
    if values:
        QP[key] = ",".join([str(x) for x in values])
    else:
        QP.pop(key, None)

def qp_set_str(key: str, value: str, default: str = "") -> None:
    if value is None or value == default:
        QP.pop(key, None)
    else:
        QP[key] = str(value)

def qp_set_float(key: str, value: float, default: float = 0.0) -> None:
    if value is None or float(value) == float(default):
        QP.pop(key, None)
    else:
        QP[key] = str(float(value))

# Defaults
DEFAULT_LAT_FILTER = "Show All"
DEFAULT_LAT_THRESHOLD = 0.0

# ======================================================================================
# Widget remount token (THIS fixes the "chip still shown after reset" issue)
# ======================================================================================
if "reset_token" not in st.session_state:
    st.session_state["reset_token"] = 0

reset_token = st.session_state["reset_token"]

def K(name: str) -> str:
    """Create a widget key that changes after reset -> forces widget remount."""
    return f"{name}__rt{reset_token}"

# ======================================================================================
# Reset mechanism for Streamlit 1.40.1
# - callback ONLY marks reset
# - top-of-script executes the reset before building widgets
# ======================================================================================

def _mark_reset():
    st.session_state["_do_reset"] = True

if st.session_state.get("_do_reset", False):
    st.session_state["_do_reset"] = False

    # clear URL query params (so refresh starts clean)
    st.query_params.clear()

    # increment token so ALL widgets remount with fresh state
    st.session_state["reset_token"] += 1

    st.rerun()

# ======================================================================================
# Sidebar
# ======================================================================================
with st.sidebar:
    st.subheader("Contact: Yuval Dahan")

    st.button("🔄 Reset Button", on_click=_mark_reset, use_container_width=True)

    st.header("🔍 Filters")

    filtered_options_df = df.copy()

    # ---- 1) Product ----
    product_options = sorted(df['product_name'].dropna().unique())
    selected_product_default = [x for x in qp_get_list("product") if x in product_options]
    selected_product = st.multiselect(
        "Product Name",
        product_options,
        default=selected_product_default,
        key=K("f_product")
    )
    if selected_product:
        filtered_options_df = filtered_options_df[filtered_options_df['product_name'].isin(selected_product)]

    # ---- 2) HW ----
    hw_options = sorted(filtered_options_df['hardware_version'].dropna().unique())
    selected_hw_default = [x for x in qp_get_list("hw") if x in hw_options]
    selected_hw = st.multiselect("Hardware Version", hw_options, default=selected_hw_default, key=K("f_hw"))
    if selected_hw:
        filtered_options_df = filtered_options_df[filtered_options_df['hardware_version'].isin(selected_hw)]

    # ---- 3) FW ----
    fw_options = sorted(filtered_options_df['firmware_version'].dropna().unique())
    selected_fw_default = [x for x in qp_get_list("fw") if x in fw_options]
    selected_fw = st.multiselect("Firmware Version", fw_options, default=selected_fw_default, key=K("f_fw"))
    if selected_fw:
        filtered_options_df = filtered_options_df[filtered_options_df['firmware_version'].isin(selected_fw)]

    # ---- 4) Traffic app ----
    tg_options = sorted(filtered_options_df['traffic_generator_application'].dropna().unique())
    selected_traffic_app_default = [x for x in qp_get_list("tg") if x in tg_options]
    selected_traffic_app = st.multiselect(
        "Traffic Generator Application",
        tg_options,
        default=selected_traffic_app_default,
        key=K("f_tg")
    )
    if selected_traffic_app:
        filtered_options_df = filtered_options_df[filtered_options_df['traffic_generator_application'].isin(selected_traffic_app)]

    # ---- 5) System Mode ----
    mode_options = sorted(filtered_options_df['system_mode'].dropna().unique())
    selected_mode_default = [x for x in qp_get_list("mode") if x in mode_options]
    selected_mode = st.multiselect("System Mode", mode_options, default=selected_mode_default, key=K("f_mode"))
    if selected_mode:
        filtered_options_df = filtered_options_df[filtered_options_df['system_mode'].isin(selected_mode)]

    # ---- 6) Client Service Type ----
    client_options = sorted(filtered_options_df['client_service_type'].dropna().unique())
    selected_client_default = [x for x in qp_get_list("client") if x in client_options]
    selected_client = st.multiselect("Client Service Type", client_options, default=selected_client_default, key=K("f_client"))
    if selected_client:
        filtered_options_df = filtered_options_df[filtered_options_df['client_service_type'].isin(selected_client)]

    # ---- 7) Client FEC ----
    client_fec_options = sorted(filtered_options_df['client_fec_mode'].dropna().unique())
    selected_client_fec_default = [x for x in qp_get_list("client_fec") if x in client_fec_options]
    selected_client_fec = st.multiselect(
        "Client FEC Mode",
        client_fec_options,
        default=selected_client_fec_default,
        key=K("f_client_fec")
    )
    if selected_client_fec:
        filtered_options_df = filtered_options_df[filtered_options_df['client_fec_mode'].isin(selected_client_fec)]

    # ---- 8) Uplink Service Type ----
    uplink_options = sorted(filtered_options_df['uplink_service_type'].dropna().unique())
    selected_uplink_default = [x for x in qp_get_list("uplink") if x in uplink_options]
    selected_uplink = st.multiselect("Uplink Service Type", uplink_options, default=selected_uplink_default, key=K("f_uplink"))
    if selected_uplink:
        filtered_options_df = filtered_options_df[filtered_options_df['uplink_service_type'].isin(selected_uplink)]

    # ---- 9) Uplink FEC ----
    uplink_fec_options = sorted(filtered_options_df['uplink_fec_mode'].dropna().unique())
    selected_uplink_fec_default = [x for x in qp_get_list("uplink_fec") if x in uplink_fec_options]
    selected_uplink_fec = st.multiselect(
        "Uplink FEC Mode",
        uplink_fec_options,
        default=selected_uplink_fec_default,
        key=K("f_uplink_fec")
    )
    if selected_uplink_fec:
        filtered_options_df = filtered_options_df[filtered_options_df['uplink_fec_mode'].isin(selected_uplink_fec)]

    # ---- 10) Modulation ----
    modulation_options = sorted(filtered_options_df['modulation_format'].dropna().unique())
    selected_modulation_default = [x for x in qp_get_list("mod") if x in modulation_options]
    selected_modulation = st.multiselect(
        "Modulation Format",
        modulation_options,
        default=selected_modulation_default,
        key=K("f_mod")
    )
    if selected_modulation:
        filtered_options_df = filtered_options_df[filtered_options_df['modulation_format'].isin(selected_modulation)]

    # ---- 11) Uplink Transceiver ----
    uplink_tr_options = sorted(filtered_options_df['uplink_transceiver'].dropna().unique())
    selected_uplink_transceiver_default = [x for x in qp_get_list("uplink_tr") if x in uplink_tr_options]
    selected_uplink_transceiver = st.multiselect(
        "Uplink Transceiver",
        uplink_tr_options,
        default=selected_uplink_transceiver_default,
        key=K("f_uplink_tr")
    )
    if selected_uplink_transceiver:
        filtered_options_df = filtered_options_df[filtered_options_df['uplink_transceiver'].isin(selected_uplink_transceiver)]

    # ---- 12) Frame size ----
    frame_options = sorted(filtered_options_df['frame_size'].dropna().unique())
    selected_frame_size_default = [x for x in qp_get_list("frame") if x in frame_options]
    selected_frame_size = st.multiselect("Frame Size", frame_options, default=selected_frame_size_default, key=K("f_frame"))
    if selected_frame_size:
        filtered_options_df = filtered_options_df[filtered_options_df['frame_size'].isin(selected_frame_size)]

    # -------------------------------------------------------------------------------------------------- #
    st.header("🆔 Filter by ID")
    id_input_default = qp_get_str("ids", "")
    id_input = st.text_input("Enter IDs (comma-separated)", value=id_input_default, key=K("f_id_input"))
    id_list = []
    if id_input.strip():
        try:
            id_list = [int(x.strip()) for x in id_input.split(",") if x.strip().isdigit()]
        except ValueError:
            st.warning("Please enter only integers separated by commas.")

    # -------------------------------------------------------------------------------------------------- #
    st.header("⏱️ Latency Filter (μSec)")
    lat_type_default = qp_get_str("lat_type", "Show All")
    if lat_type_default not in ["Show All", "Above", "Below"]:
        lat_type_default = "Show All"

    latency_filter_type = st.radio(
        "Filter by Latency:",
        ["Show All", "Above", "Below"],
        horizontal=True,
        index=["Show All", "Above", "Below"].index(lat_type_default),
        key=K("f_lat_type")
    )
    latency_threshold_default = qp_get_float("lat_th", 0.0)
    latency_threshold = st.number_input(
        "Latency Threshold (μSec)",
        min_value=0.0,
        step=0.1,
        value=float(latency_threshold_default),
        key=K("f_lat_thresh")
    )

    # -------------------------------------------------------------------------------------------------- #
    st.header("🧩 Columns to Display")
    st.caption("Toggle columns on/off to display in the table:")

    default_cols = list(df.rename(columns=display_columns_map).columns)
    cols_from_qp = qp_get_list("cols")
    if cols_from_qp:
        cols_default = [c for c in cols_from_qp if c in default_cols] or default_cols
    else:
        cols_default = default_cols

    checkbox_columns = {}
    for col in default_cols:
        checkbox_columns[col] = st.checkbox(col, value=(col in cols_default), key=K(f"col_{col}"))

    selected_columns = [col for col, show in checkbox_columns.items() if show]

# ======================================================================================
# Save current selections back into query params (so F5 keeps state)
# ======================================================================================
qp_set_list("product", selected_product)
qp_set_list("hw", selected_hw)
qp_set_list("fw", selected_fw)
qp_set_list("tg", selected_traffic_app)
qp_set_list("mode", selected_mode)
qp_set_list("client", selected_client)
qp_set_list("client_fec", selected_client_fec)
qp_set_list("uplink", selected_uplink)
qp_set_list("uplink_fec", selected_uplink_fec)
qp_set_list("mod", selected_modulation)
qp_set_list("uplink_tr", selected_uplink_transceiver)
qp_set_list("frame", selected_frame_size)

qp_set_str("ids", id_input, default="")
qp_set_str("lat_type", latency_filter_type, default=DEFAULT_LAT_FILTER)
qp_set_float("lat_th", latency_threshold, default=DEFAULT_LAT_THRESHOLD)

qp_set_list("cols", selected_columns)

# ======================================================================================
# Apply filters
# ======================================================================================
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

display_df = filtered_df.rename(columns=display_columns_map)

st.subheader(f"Showing {len(display_df)} Records")
st.dataframe(display_df[selected_columns], use_container_width=True)

# =========================================== Download Options ============================================== #
export_df = display_df[selected_columns]
output = io.BytesIO()

with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    sheet_name = "Latency Results"
    export_df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=5)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    logo_path = os.path.join(os.path.dirname(__file__), "Packetlight Logo.png")
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