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
# 5. FUNGSI PENCARIAN KOLOM YANG FLEKSIBEL
# -----------------------------------------------------------------------------
def cari_nama_kolom(kata_kunci):
    """Mencari nama kolom asli di DataFrame yang mengandung kata kunci."""
    for col in df.columns:
        col_clean = str(col).strip().lower()
        kunci_clean = str(kata_kunci).strip().lower()
        if kunci_clean in col_clean:
            return col
    return None

def cari_kolom_grup(kata_kunci_list):
    """Mencari daftar kolom asli berdasarkan kumpulan kata kunci (tidak duplikat)."""
    ditemukan = []
    for kunci in kata_kunci_list:
        for col in df.columns:
            if kunci.lower() in str(col).lower() and col not in ditemukan:
                ditemukan.append(col)
    return ditemukan

# Deteksi kolom Site ID & Site Name utama
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
# TAB 4: SOW (SCOPE OF WORK) — SUB-TAB BERLAPIS (NESTED TABS) & EDITABLE
# =============================================================================
with tab4:
    st.markdown("### 🛠️ SOW (Scope of Work) — Edit Detail Lapisan Pekerjaan")
    st.caption("Pilih kategori pekerjaan di bawah ini untuk mengedit data detail (Tanggal, Tenant, ID Lama/Baru, dll).")
    
    # 1. Klasifikasikan kolom ke 3 sub-grup SOW berdasarkan kata kunci di namanya
    grup_tower = cari_kolom_grup(["Dismantle Tower", "Tanggal Dismantle Tower", "Status Tower", "Tgl Tower"])
    grup_equipment = cari_kolom_grup(["Dismantle Equipment", "Tenant", "Equipment", "Perangkat"])
    grup_relocation = cari_kolom_grup(["Relocation", "Reloc", "Site Id Old", "Site Id New", "Old", "New", "Alamat"])
    
    # Kumpulkan semua kolom yang masuk ke SOW agar bisa disimpan sekaligus
    semua_kolom_sow = list(dict.fromkeys(grup_tower + grup_equipment + grup_relocation))
    
    if semua_kolom_sow:
        with st.form("form_update_sow_berlapis"):
            st.write(f"✏️ **Form Edit SOW Lengkap: {nama_site_terpilih}**")
            
            # BUAT SUB-TAB BERLAPIS DI DALAM TAB SOW
            subtab_tower, subtab_equip, subtab_reloc = st.tabs([
                "🏗️ Dismantle Tower",
                "⚙️ Dismantle Equipment",
                "🚚 Relocation"
            ])
            
            input_progress_baru = {}
            
            # --- SUB-TAB 1: DISMANTLE TOWER ---
            with subtab_tower:
                st.markdown("#### 🏗️ Detail Dismantle Tower")
                if grup_tower:
                    cols_t = st.columns(2 if len(grup_tower) <= 2 else 3)
                    for i, col_name in enumerate(grup_tower):
                        val_lama = "" if pd.isna(data_site[col_name]) else str(data_site[col_name])
                        with cols_t[i % 3]:
                            input_progress_baru[col_name] = st.text_input(
                                label=f"🔄 {col_name}",
                                value=val_lama,
                                key=f"edit_tower_{i}"
                            )
                else:
                    st.info("ℹ️ Belum ada kolom khusus 'Dismantle Tower' yang terdeteksi.")
            
            # --- SUB-TAB 2: DISMANTLE EQUIPMENT ---
            with subtab_equip:
                st.markdown("#### ⚙️ Detail Equipment & Tenant")
                if grup_equipment:
                    cols_e = st.columns(2 if len(grup_equipment) <= 2 else 3)
                    for i, col_name in enumerate(grup_equipment):
                        val_lama = "" if pd.isna(data_site[col_name]) else str(data_site[col_name])
                        with cols_e[i % 3]:
                            input_progress_baru[col_name] = st.text_input(
                                label=f"🔄 {col_name}",
                                value=val_lama,
                                key=f"edit_equip_{i}"
                            )
                else:
                    st.info("ℹ️ Belum ada kolom khusus 'Equipment / Tenant' yang terdeteksi.")
            
            # --- SUB-TAB 3: RELOCATION ---
            with subtab_reloc:
                st.markdown("#### 🚚 Detail Relocation (Site ID Old / New)")
                if grup_relocation:
                    cols_r = st.columns(2 if len(grup_relocation) <= 2 else 3)
                    for i, col_name in enumerate(grup_relocation):
                        val_lama = "" if pd.isna(data_site[col_name]) else str(data_site[col_name])
                        with cols_r[i % 3]:
                            input_progress_baru[col_name] = st.text_input(
                                label=f"🔄 {col_name}",
                                value=val_lama,
                                key=f"edit_reloc_{i}"
                            )
                else:
                    st.info("ℹ️ Belum ada kolom khusus 'Relocation / Old / New' yang terdeteksi.")
            
            st.divider()
            submit_sow = st.form_submit_button(
                "💾 Simpan Seluruh Update SOW ke Google Sheets", 
                type="primary", 
                use_container_width=True
            )
            
            if submit_sow:
                try:
                    with st.spinner("Menyimpan seluruh data SOW ke Google Sheets..."):
                        # 1. Update nilai pada baris index site yang dipilih
                        for nama_col, val_baru in input_progress_baru.items():
                            # Paksa kolom agar bertipe string/object terlebih dahulu (Anti-Error float64)
                            df[nama_col] = df[nama_col].astype(str)
                            df.at[idx_site, nama_col] = str(val_baru)
                        
                        # 2. Simpan ke Google Sheets
                        conn.update(data=df)
                        st.success(f"✅ Berhasil mengupdate detail SOW pada site: {nama_site_terpilih}!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan perubahan progress SOW: {e}")
    else:
        st.warning("⚠️ Tidak ada kolom SOW yang terdeteksi di Baris ke-2 Google Sheets.")
