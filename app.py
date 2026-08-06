import streamlit as st
import pandas as pd
import gspread

# ==========================================
# 1. KONFIGURASI HALAMAN WEB (MOBILE-FRIENDLY)
# ==========================================
st.set_page_config(
    page_title="Site Monitoring & Progress SOW",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. KONEKSI KE GOOGLE SHEETS
# ==========================================
@st.cache_resource
def get_worksheet():
    try:
        # Menghubungkan menggunakan service account file (credentials.json)
        gc = gspread.service_account(filename="credentials.json")
        
        # GANTI "Nama Google Sheet Kamu" dengan JUDUL file Google Sheets kamu
        sh = gc.open("Nama Google Sheet Kamu")
        
        # Mengambil sheet pertama (Sheet1 / Data_Site)
        worksheet = sh.sheet1
        return worksheet
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        st.stop()

worksheet = get_worksheet()

# Ambil data dari sheet sebagai DataFrame (cache 10 detik agar cepat di HP)
@st.cache_data(ttl=10)
def load_data():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    # Pastikan Site ID dibaca sebagai string agar tidak error pada angka
    if "Site ID" in df.columns:
        df["Site ID"] = df["Site ID"].astype(str)
    return df

df = load_data()

# Cek jika data kosong
if df.empty:
    st.warning("Data di Google Sheets masih kosong. Silakan isi data terlebih dahulu.")
    st.stop()

# ==========================================
# 3. HEADER APLIKASI
# ==========================================
st.title("📡 Site Monitoring & SOW")
st.caption("Monitoring dan update progress lapangan. Bagian di luar SOW dikunci (Read-Only).")
st.divider()

# ==========================================
# 4. GATE 1: METODE PENCARIAN
# ==========================================
st.subheader("🔍 Gate 1: Pilih Kategori Pencarian")
search_by = st.radio(
    "Cari site berdasarkan:",
    ["Site ID", "Site Name"],
    horizontal=True
)

# ==========================================
# 5. GATE 2: PILIH SITE (ID / NAME)
# ==========================================
st.subheader("🏢 Gate 2: Pilih Site")
if search_by == "Site ID":
    options = df["Site ID"].unique()
    selected_value = st.selectbox("Pilih Site ID:", options)
    selected_row = df[df["Site ID"] == str(selected_value)].iloc[0]
else:
    options = df["Site Name"].unique()
    selected_value = st.selectbox("Pilih Site Name:", options)
    selected_row = df[df["Site Name"] == selected_value].iloc[0]

st.divider()

# Banner informasi site terpilih
st.info(f"**Site Terpilih:** `{selected_row['Site ID']}` — **{selected_row['Site Name']}**")

# ==========================================
# 6. MENU TAB: 4 BAGIAN
# ==========================================
tab_detail, tab_permit, tab_hse, tab_sow = st.tabs([
    "📍 Detail Info 🔒", 
    "📜 Permit 🔒", 
    "🛡️ HSE 🔒", 
    "🔧 SOW (Edit) ✏️"
])

# --- TAB 1: DETAIL INFORMATION (READ-ONLY) ---
with tab_detail:
    st.write("### Detail Information")
    st.caption("🔒 *Bagian ini dikunci (Read-Only)*")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Provinsi", value=str(selected_row.get("Provinsi", "")), disabled=True)
        st.text_input("Kabupaten", value=str(selected_row.get("Kabupaten", "")), disabled=True)
        st.text_input("Tower Height", value=str(selected_row.get("Tower Height", "")), disabled=True)
        # End Lease masuk ke Detail Information
        st.text_input("End Lease", value=str(selected_row.get("End Lease", "")), disabled=True)
    with col2:
        st.text_input("Lat / Long", value=str(selected_row.get("Lat/Long", "")), disabled=True)
        st.text_input("Tower Weight", value=str(selected_row.get("Tower Weight", "")), disabled=True)
        
    st.text_area("Address", value=str(selected_row.get("Address", "")), disabled=True)

# --- TAB 2: PERMIT (READ-ONLY) ---
with tab_permit:
    st.write("### Permit Information")
    st.caption("🔒 *Bagian ini dikunci (Read-Only)*")
    
    # Hanya Start - End
    st.text_input("Start - End", value=str(selected_row.get("Start - End", "")), disabled=True)

# --- TAB 3: HSE (READ-ONLY) ---
with tab_hse:
    st.write("### HSE Documents")
    st.caption("🔒 *Bagian ini dikunci (Read-Only)*")
    
    st.text_input("JSA", value=str(selected_row.get("JSA", "")), disabled=True)
    st.text_input("HSE Plan", value=str(selected_row.get("HSE Plan", "")), disabled=True)
    st.text_input("SWP", value=str(selected_row.get("SWP", "")), disabled=True)

# --- TAB 4: SOW (EDITABLE & SAVE KE SHEETS) ---
with tab_sow:
    st.write("### 🔧 Update Progress SOW")
    st.caption("✏️ *Hanya 3 data di bawah ini yang dapat diupdate ke Google Sheets.*")
    
    with st.form("form_sow_update"):
        input_dt = st.text_input(
            "Dismantle Tower Progress", 
            value=str(selected_row.get("Dismantle Tower", "")),
            placeholder="Contoh: 50% / Selesai / Belum Mulai"
        )
        input_de = st.text_input(
            "Dismantle Equipment Progress", 
            value=str(selected_row.get("Dismantle Equipment", "")),
            placeholder="Contoh: In Progress"
        )
        input_re = st.text_input(
            "Relocation Progress", 
            value=str(selected_row.get("Relocation", "")),
            placeholder="Contoh: Done"
        )
        
        submit_btn = st.form_submit_button("💾 Simpan Progress SOW", use_container_width=True)
        
        if submit_btn:
            with st.spinner("Menyimpan perubahan ke Google Sheets..."):
                try:
                    # Cari nomor baris berdasarkan Site ID di Google Sheets
                    cell = worksheet.find(str(selected_row["Site ID"]))
                    row_idx = cell.row
                    
                    # Update cell kolom SOW:
                    # N = Kolom 14 (Dismantle Tower)
                    # O = Kolom 15 (Dismantle Equipment)
                    # P = Kolom 16 (Relocation)
                    worksheet.update_cell(row_idx, 14, input_dt)
                    worksheet.update_cell(row_idx, 15, input_de)
                    worksheet.update_cell(row_idx, 16, input_re)
                    
                    # Hapus cache agar Streamlit langsung memuat data terbaru
                    st.cache_data.clear()
                    st.success("✅ Progress SOW berhasil diperbarui di Google Sheets!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal memperbarui data: {e}")
