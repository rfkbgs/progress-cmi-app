import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Progress CMI - Realtime Editor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Progress CMI - Realtime Editor")
st.caption("Aplikasi monitoring & update data proyek secara real-time (Google Sheets - Single Sheet).")

# -----------------------------------------------------------------------------
# 2. INISIALISASI KONEKSI KE GOOGLE SHEETS
# -----------------------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# -----------------------------------------------------------------------------
# 3. SIDEBAR (RINGKAS: HANYA TOMBOL REFRESH)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Pengaturan")
st.sidebar.caption("Google Sheets terhubung pada Sheet utama (Sheet tunggal).")

if st.sidebar.button("🔄 Refresh Data Terbaru", use_container_width=True):
    st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 4. MEMBACA DATA GOOGLE SHEETS (HEADER=1 KARENA JUDUL DI BARIS KE-2)
# -----------------------------------------------------------------------------
try:
    with st.spinner("Mengambil data dari Google Sheets..."):
        # header=1 artinya membaca Baris ke-2 (Row 2) sebagai nama kolom
        df = conn.read(ttl=0, header=1)
except Exception as e:
    st.error(f"❌ Gagal membaca data Google Sheets: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 5. FUNGSI PENCARIAN KOLOM YANG FLEKSIBEL (CASE-INSENSITIVE & SYMBOL-SAFE)
# -----------------------------------------------------------------------------
def cari_nama_kolom(kata_kunci):
    """Mencari nama kolom asli di DataFrame yang mengandung kata kunci."""
    for col in df.columns:
        # Menghapus spasi berlebih untuk pencarian lebih akurat
        col_clean = str(col).strip().lower()
        kunci_clean = kata_kunci.strip().lower()
        if kunci_clean in col_clean:
            return col
    return None

# Deteksi kolom Site ID & Site Name
col_site_id = cari_nama_kolom("Site Id") or cari_nama_kolom("Site ID") or df.columns[0]
col_site_name = cari_nama_kolom("Site Name") or (df.columns[1] if len(df.columns) > 1 else df.columns[0])

# -----------------------------------------------------------------------------
# 6. GATE 1: PEMILIHAN SITE ID / SITE NAME
# -----------------------------------------------------------------------------
st.subheader("🔍 Gate 1: Pilih Site ID / Site Name")

daftar_pilihan_site = []
for idx, row in df.iterrows():
    val_id = str(row.get(col_site_id, "")).strip()
    val_name = str(row.get(col_site_name, "")).strip()
    label_tampil = f"{val_id}  —  {val_name}" if (val_id or val_name) else f"Baris {idx+1}"
    daftar_pilihan_site.append((idx, label_tampil))

idx_site, nama_site_terpilih = st.selectbox(
    "Pilih Site yang ingin dilihat atau diedit:",
    options=daftar_pilihan_site,
    format_func=lambda x: x[1],
    key="select_gate_site"
)

st.divider()

# Ambil data baris untuk site yang dipilih
data_site = df.loc[idx_site]

# -----------------------------------------------------------------------------
# 7. GATE 2: 4 BAGIAN UTAMA (DETAIL INFORMATION, PERMIT, HSE, SOW)
# -----------------------------------------------------------------------------
st.subheader(f"📌 Detail Site: **{nama_site_terpilih}**")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏢 Detail Information",
    "📑 Permit",
    "🛡️ HSE",
    "🛠️ SOW (Scope of Work) — [EDITABLE]"
])

# =============================================================================
# TAB 1: DETAIL INFORMATION (READ-ONLY / LOCKED)
# =============================================================================
with tab1:
    st.markdown("### 🏢 Detail Information *(Locked / Read-Only)*")
    st.caption("Informasi teknis dan administratif site ini dilock untuk menjaga keaslian data.")
    
    # Termasuk End Lease sesuai letak kolom di spreadsheet
    target_detail = [
        "Provinsi", "Kabupaten", "Address", "Lat", "Tower Height", 
        "Tower Weight", "End Lease"
    ]
    
    cols = st.columns(3)
    for i, kunci in enumerate(target_detail):
        nama_col_asli = cari_nama_kolom(kunci)
        label_col = nama_col_asli if nama_col_asli else kunci
        nilai_tampil = str(data_site[nama_col_asli]) if (nama_col_asli and pd.notna(data_site[nama_col_asli])) else "-"
        
        with cols[i % 3]:
            st.text_input(
                label=label_col,
                value=nilai_tampil,
                disabled=True,
                key=f"lock_detail_{i}"
            )

# =============================================================================
# TAB 2: PERMIT (READ-ONLY / LOCKED)
# =============================================================================
with tab2:
    st.markdown("### 📑 Permit *(Locked / Read-Only)*")
    st.caption("Data perizinan site dilock agar tidak terjadi modifikasi secara tidak sengaja.")
    
    target_permit = ["Start-End", "Permit"]
    cols = st.columns(2)
    
    ditemukan = False
    for i, kunci in enumerate(target_permit):
        nama_col_asli = cari_nama_kolom(kunci)
        if nama_col_asli:
            ditemukan = True
            nilai_tampil = str(data_site[nama_col_asli]) if pd.notna(data_site[nama_col_asli]) else "-"
            with cols[i % 2]:
                st.text_input(
                    label=nama_col_asli,
                    value=nilai_tampil,
                    disabled=True,
                    key=f"lock_permit_{i}"
                )
    if not ditemukan:
        st.info("ℹ️ Kolom terkait 'Permit' atau 'Start-End' tidak terdeteksi pada tabel.")

# =============================================================================
# TAB 3: HSE (READ-ONLY / LOCKED)
# =============================================================================
with tab3:
    st.markdown("### 🛡️ HSE *(Locked / Read-Only)*")
    st.caption("Dokumen K3 dan Keselamatan Kerja dilock dari pengeditan umum.")
    
    target_hse = ["JSA", "HSE Plan", "SWP"]
    cols = st.columns(3)
    
    for i, kunci in enumerate(target_hse):
        nama_col_asli = cari_nama_kolom(kunci)
        label_col = nama_col_asli if nama_col_asli else kunci
        nilai_tampil = str(data_site[nama_col_asli]) if (nama_col_asli and pd.notna(data_site[nama_col_asli])) else "-"
        
        with cols[i % 3]:
            st.text_input(
                label=label_col,
                value=nilai_tampil,
                disabled=True,
                key=f"lock_hse_{i}"
            )

# =============================================================================
# TAB 4: SOW (SCOPE OF WORK) — HANYA INI YANG BISA DIEDIT & DISIMPAN!
# =============================================================================
with tab4:
    st.markdown("### 🛠️ SOW (Scope of Work)")
    st.caption("Hanya bagian Progress pada kolom di bawah ini yang dapat kamu edit dan simpan ke Google Sheets.")
    
    target_sow = ["Dismantle Tower", "Dismantle Equipment", "Relocation"]
    kolom_sow_terdeteksi = []
    
    # Kumpulkan semua kolom yang sesuai dengan SOW
    for kunci in target_sow:
        nama_col = cari_nama_kolom(kunci)
        if nama_col and nama_col not in kolom_sow_terdeteksi:
            kolom_sow_terdeteksi.append(nama_col)
    
    if kolom_sow_terdeteksi:
        with st.form("form_update_sow"):
            st.write(f"✏️ **Update Progress untuk: {nama_site_terpilih}**")
            
            input_progress_baru = {}
            cols = st.columns(len(kolom_sow_terdeteksi) if len(kolom_sow_terdeteksi) <= 3 else 3)
            
            for i, nama_col in enumerate(kolom_sow_terdeteksi):
                val_lama = data_site[nama_col]
                val_lama_str = "" if pd.isna(val_lama) else str(val_lama)
                
                with cols[i % 3]:
                    # Kolom ini TIDAK DI-DISABLED agar bisa diedit progressnya
                    input_progress_baru[nama_col] = st.text_input(
                        label=f"🔄 {nama_col}",
                        value=val_lama_str,
                        key=f"edit_sow_{i}"
                    )
            
            st.divider()
            submit_sow = st.form_submit_button("💾 Simpan Progress SOW ke Google Sheets", type="primary", use_container_width=True)
            
            if submit_sow:
                try:
                    with st.spinner("Menyimpan update progress SOW ke Google Sheets..."):
                        # Update nilai pada baris index site yang dipilih
                        for nama_col, val_baru in input_progress_baru.items():
                            df.at[idx_site, nama_col] = val_baru
                        
                        # Simpan ke Google Sheets (otomatis ke sheet pertama/tunggal)
                        conn.update(data=df)
                        st.success(f"✅ Berhasil mengupdate progress SOW pada site: {nama_site_terpilih}!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan perubahan progress SOW: {e}")
    else:
        st.warning("⚠️ Kolom 'Dismantle Tower', 'Dismantle Equipment', atau 'Relocation' tidak terdeteksi. Pastikan nama kolom di Baris ke-2 Google Sheets sudah sesuai.")
