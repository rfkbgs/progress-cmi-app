import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import altair as alt
from datetime import datetime, date

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN & CUSTOM CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Progress CMI - Dashboard & Editor",
    page_icon="📊",
    layout="wide"
)

# Custom CSS untuk tampilan Checklist & Kartu Status yang modern
st.markdown("""
<style>
    .card-done {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid #10B981;
        border-left: 6px solid #10B981;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .card-progress {
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid #F59E0B;
        border-left: 6px solid #F59E0B;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .card-plan {
        background: rgba(139, 92, 246, 0.12);
        border: 1px solid #8B5CF6;
        border-left: 6px solid #8B5CF6;
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .card-title {
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 8px;
    }
    .site-detail {
        font-size: 0.88rem;
        opacity: 0.95;
        color: #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Progress CMI - Dashboard & Realtime Editor")
st.caption("Monitoring visual & update data proyek secara real-time (Google Sheets - Single Sheet).")

# -----------------------------------------------------------------------------
# 2. SYSTEM NOTIFIKASI ATAS (TOAST & BANNER) SETELAH PROSES SIMPAN
# -----------------------------------------------------------------------------
if "notif" in st.session_state:
    tipe, pesan = st.session_state.pop("notif")
    if tipe == "success":
        st.toast("Data SOW berhasil disinkronkan ke Google Sheets!", icon="🎉")
        st.success(pesan)
    elif tipe == "error":
        st.toast("Gagal menyimpan data ke Google Sheets!", icon="🚨")
        st.error(pesan)

# -----------------------------------------------------------------------------
# 3. INISIALISASI KONEKSI KE GOOGLE SHEETS
# -----------------------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# -----------------------------------------------------------------------------
# 4. SIDEBAR (TOMBOL REFRESH)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Pengaturan")
st.sidebar.caption("Google Sheets terhubung pada Sheet utama (Sheet tunggal).")

if st.sidebar.button("🔄 Refresh Data Terbaru", use_container_width=True):
    st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 5. MEMBACA DATA GOOGLE SHEETS (HEADER=0 / BARIS 1 SEBAGAI JUDUL KOLOM)
# -----------------------------------------------------------------------------
try:
    with st.spinner("Mengambil data dari Google Sheets..."):
        df = conn.read(ttl=0, header=0)
        df = df.dropna(how="all").reset_index(drop=True)
except Exception as e:
    st.error(f"❌ Gagal membaca data Google Sheets: {e}")
    st.stop()

if df.empty:
    st.warning("⚠️ Tabel di Google Sheets masih kosong. Pastikan Baris 1 berisi nama kolom dan minimal ada 1 baris data di Baris 2.")
    st.stop()

# -----------------------------------------------------------------------------
# 6. FUNGSI UTAMA: PENCARIAN KOLOM, PARSER TANGGAL, & ANALYTICS PER SITE
# -----------------------------------------------------------------------------
def cari_nama_kolom(kata_kunci):
    for col in df.columns:
        col_clean = str(col).strip().lower()
        kunci_clean = str(kata_kunci).strip().lower()
        if kunci_clean in col_clean:
            return col
    return None

def cari_kolom_grup(kata_kunci_list):
    ditemukan = []
    for kunci in kata_kunci_list:
        for col in df.columns:
            if kunci.lower() in str(col).lower() and col not in ditemukan:
                ditemukan.append(col)
    return ditemukan

col_site_id = cari_nama_kolom("Site Id") or cari_nama_kolom("Site ID") or df.columns[0]
col_site_name = cari_nama_kolom("Site Name") or (df.columns[1] if len(df.columns) > 1 else df.columns[0])

def is_terisi(val):
    """Mengecek apakah suatu sel sudah diisi dengan tanggal / data valid."""
    val_str = str(val).strip()
    return val_str not in ["", "-", "nan", "None", "NaT", "0", "null"]

def parse_tanggal_ke_date(val):
    """Menerjemahkan teks dari Google Sheets menjadi objek tanggal untuk kalender pop-up."""
    if pd.isna(val) or not is_terisi(val):
        return None
    try:
        dt = pd.to_datetime(str(val).strip(), dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.date()
    except:
        pass
    return None

def hitung_progress_site(row, grup_kolom):
    """Menghitung jumlah tahapan yang terisi dan persentase penyelesaian (0% - 100%)."""
    kolom_valid = [col for col in grup_kolom if col in df.columns]
    if not kolom_valid:
        return 0, 0, 0
    total_step = len(kolom_valid)
    step_selesai = sum(1 for col in kolom_valid if is_terisi(row.get(col)))
    pct = int((step_selesai / total_step) * 100)
    return pct, step_selesai, total_step

def tampilkan_analytics_milestone_single_site(row_site, grup_kolom, nama_sow):
    """Menampilkan Analytics Dashboard khusus untuk 1 Site ID terpilih secara bersih & elegan."""
    kolom_valid = [col for col in grup_kolom if col in df.columns]
    if not kolom_valid:
        st.info(f"ℹ️ Kolom tahapan untuk {nama_sow} belum terdeteksi di tabel.")
        return

    pct, sel, tot = hitung_progress_site(row_site, kolom_valid)
    
    # Penentuan status & warna badge
    if pct == 100:
        status_label = "🟢 DONE (100%)"
        card_class = "card-done"
        color_hex = "#34D399"
    elif pct > 0:
        status_label = "🟡 PROGRESS"
        card_class = "card-progress"
        color_hex = "#FBBF24"
    else:
        status_label = "🟣 PLAN (0%)"
        card_class = "card-plan"
        color_hex = "#C084FC"

    # --- 1. KPI CARDS ATAS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Status Progres", status_label)
    with c2:
        st.metric("Tingkat Penyelesaian", f"{pct}%")
    with c3:
        st.metric("Tahapan Selesai", f"{sel} dari {tot} Tahapan")

    # --- 2. PROGRESS BAR ---
    st.markdown(f"##### 🎯 Progress Penyelesaian {nama_sow}: **{pct}%**")
    st.progress(pct / 100.0)
    
    # --- 3. CHECKLIST TAHAPAN PEKERJAAN ---
    st.markdown("##### 📋 Checklist Tahapan Pekerjaan:")
    cols_step = st.columns(2 if len(kolom_valid) <= 2 else 3)
    for idx_col, col_name in enumerate(kolom_valid):
        val_tgl = str(row_site.get(col_name, "")).strip()
        with cols_step[idx_col % len(cols_step)]:
            if is_terisi(val_tgl):
                with st.container(border=True):
                    st.markdown(f"✅ **{col_name}**")
                    st.caption(f"Selesai: `{val_tgl}`")
            else:
                with st.container(border=True):
                    st.markdown(f"⏳ **{col_name}**")
                    st.caption("*Belum ada tanggal*")
                    
    # --- 4. KARTU RINGKASAN STATUS DI BAWAH ---
    s_id = str(row_site.get(col_site_id, "")).strip()
    s_name = str(row_site.get(col_site_name, "")).strip()
    st.markdown(f"""
    <div class="{card_class}" style="margin-top: 15px;">
        <div class="card-title" style="color: {color_hex};">📌 Status Aktual: {status_label}</div>
        <div class="site-detail">
            <b>Site ID:</b> {s_id} &nbsp;|&nbsp; <b>Nama Site:</b> {s_name}<br>
            <b>Progress {nama_sow}:</b> {sel} dari {tot} tahapan telah selesai dikerjakan ({pct}%).
        </div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. MENU UTAMA: DASHBOARD vs REALTIME EDITOR
# -----------------------------------------------------------------------------
menu_dash, menu_editor = st.tabs(["📈 Dashboard & Analytics", "📝 Realtime Editor"])

# =============================================================================
# MENU 1: DASHBOARD & ANALYTICS PER SOW (MANDATORY SINGLE-SITE VIEW)
# =============================================================================
with menu_dash:
    st.subheader("📊 Dashboard Analytics per Scope of Work (SOW)")
    
    # --- SEARCH & FILTER WAJIB PILIH 1 SITE ID (TANPA 'SEMUA SITE') ---
    daftar_site_dash = []
    for _, row in df.iterrows():
        val_id = str(row.get(col_site_id, "")).strip()
        val_name = str(row.get(col_site_name, "")).strip()
        if val_id or val_name:
            daftar_site_dash.append(f"{val_id} — {val_name}")
            
    pilih_site_dash = st.selectbox(
        "🔍 Cari & Pilih Site ID untuk melihat Dashboard (Ketik untuk mencari):",
        options=daftar_site_dash,
        index=None,  # Default kosong agar user wajib memilih
        placeholder="-- Pilih atau ketik Site ID di sini --",
        key="filter_site_dash"
    )
    
    # JIKA USER BELUM MEMILIH SITE, TAMPILKAN INFO DAN HENTIKAN RENDER
    if not pilih_site_dash:
        st.info("👈 Silakan pilih atau ketik **Site ID** pada kotak di atas terlebih dahulu untuk menampilkan data Dashboard & Checklist.")
        st.stop()

    # Ambil data 1 baris untuk site yang dipilih
    id_terpilih = pilih_site_dash.split(" — ")[0].strip()
    df_filter = df[df[col_site_id].astype(str).str.strip() == id_terpilih]
    row_terpilih = df_filter.iloc[0]

    st.divider()
    
    dash_tower, dash_equip, dash_reloc = st.tabs([
        "🏗️ Dismantle Tower (4 Tahapan)", 
        "⚙️ Dismantle Equipment (4 Tahapan)", 
        "🚚 Relocation (5 Tahapan)"
    ])
    
    grup_tower_cols = cari_kolom_grup(["Survey Tower", "Report Survey Tower", "Dismantle Tower", "BAST"])
    grup_equip_cols = cari_kolom_grup(["Survey Equipment", "Report Survey Equipment", "Dismantle Equipment", "Inbound Material"])
    grup_reloc_cols = cari_kolom_grup(["Survey Relocation", "Report Survey Relocation", "Relocation", "OA", "ATP MS"])
    
    with dash_tower:
        st.markdown("#### 📈 Analytics: Dismantle Tower")
        tampilkan_analytics_milestone_single_site(row_terpilih, grup_tower_cols, "Dismantle Tower")
            
    with dash_equip:
        st.markdown("#### 📈 Analytics: Dismantle Equipment")
        tampilkan_analytics_milestone_single_site(row_terpilih, grup_equip_cols, "Dismantle Equipment")
            
    with dash_reloc:
        st.markdown("#### 📈 Analytics: Site Relocation")
        tampilkan_analytics_milestone_single_site(row_terpilih, grup_reloc_cols, "Relocation")

# =============================================================================
# MENU 2: REALTIME EDITOR (GATE 1 & GATE 2 - WAJIB PILIH SITE)
# =============================================================================
with menu_editor:
    st.subheader("🔍 Gate 1: Pilih Site ID / Site Name")

    daftar_pilihan_site = []
    for idx, row in df.iterrows():
        val_id = str(row.get(col_site_id, "")).strip()
        val_name = str(row.get(col_site_name, "")).strip()
        if val_id or val_name:
            label_tampil = f"{val_id}  —  {val_name}"
            daftar_pilihan_site.append((idx, label_tampil))

    if not daftar_pilihan_site:
        st.warning("⚠️ Data Site tidak terdeteksi. Pastikan kolom Site ID atau Site Name di Google Sheets sudah terisi.")
        st.stop()

    # Default kosong agar user wajib memilih terlebih dahulu
    pilihan_terpilih = st.selectbox(
        "Pilih Site yang ingin dilihat atau diedit (Ketik untuk mencari):",
        options=daftar_pilihan_site,
        format_func=lambda x: x[1],
        index=None,
        placeholder="-- Pilih atau ketik Site ID di sini --",
        key="select_gate_site"
    )

    # JIKA USER BELUM MEMILIH SITE, TAMPILKAN INFO DAN HENTIKAN RENDER
    if not pilihan_terpilih:
        st.info("👈 Silakan pilih atau ketik **Site ID** pada kotak di atas terlebih dahulu untuk melihat dan mengedit detail Site.")
        st.stop()

    idx_site, nama_site_terpilih = pilihan_terpilih

    st.divider()
    data_site = df.loc[idx_site]

    st.subheader(f"📌 Detail Site: **{nama_site_terpilih}**")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏢 Detail Information",
        "📑 Permit",
        "🛡️ HSE",
        "🛠️ SOW (Scope of Work) — [EDITABLE]"
    ])

    with tab1:
        st.markdown("### 🏢 Detail Information *(Locked / Read-Only)*")
        st.caption("Informasi teknis dan administratif site ini dilock untuk menjaga keaslian data.")
        target_detail = ["Provinsi", "Kabupaten", "Address", "Lat", "Tower Height", "Tower Weight", "End Lease"]
        cols = st.columns(3)
        for i, kunci in enumerate(target_detail):
            nama_col_asli = cari_nama_kolom(kunci)
            label_col = nama_col_asli if nama_col_asli else kunci
            nilai_tampil = str(data_site[nama_col_asli]) if (nama_col_asli and pd.notna(data_site[nama_col_asli])) else "-"
            with cols[i % 3]:
                st.text_input(label=label_col, value=nilai_tampil, disabled=True, key=f"lock_detail_{idx_site}_{i}")

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
                    st.text_input(label=nama_col_asli, value=nilai_tampil, disabled=True, key=f"lock_permit_{idx_site}_{i}")
        if not ditemukan:
            st.info("ℹ️ Kolom terkait 'Permit' atau 'Start-End' tidak terdeteksi pada tabel.")

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
                st.text_input(label=label_col, value=nilai_tampil, disabled=True, key=f"lock_hse_{idx_site}_{i}")

    with tab4:
        st.markdown("### 🛠️ SOW (Scope of Work) — Edit Tanggal Tahapan Pekerjaan")
        st.caption("Klik kotak input di bawah untuk membuka kalender dan memilih tanggal selesai per tahapan.")
        
        grup_tower = cari_kolom_grup(["Survey Tower", "Report Survey Tower", "Dismantle Tower", "BAST"])
        grup_equipment = cari_kolom_grup(["Survey Equipment", "Report Survey Equipment", "Dismantle Equipment", "Inbound Material"])
        grup_relocation = cari_kolom_grup(["Survey Relocation", "Report Survey Relocation", "Relocation", "OA", "ATP MS"])
        
        semua_kolom_sow = list(dict.fromkeys(grup_tower + grup_equipment + grup_relocation))
        
        if semua_kolom_sow:
            with st.form("form_update_sow_berlapis"):
                st.write(f"📅 **Form Input Tanggal SOW: {nama_site_terpilih}**")
                subtab_tower, subtab_equip, subtab_reloc = st.tabs(["🏗️ Dismantle Tower", "⚙️ Dismantle Equipment", "🚚 Relocation"])
                input_progress_baru = {}
                
                with subtab_tower:
                    st.markdown("#### 🏗️ Tanggal Tahapan Dismantle Tower")
                    if grup_tower:
                        cols_t = st.columns(2 if len(grup_tower) <= 2 else 3)
                        for i, col_name in enumerate(grup_tower):
                            val_lama_dt = parse_tanggal_ke_date(data_site[col_name])
                            with cols_t[i % 3]:
                                input_progress_baru[col_name] = st.date_input(
                                    label=f"📅 {col_name}",
                                    value=val_lama_dt,
                                    format="DD/MM/YYYY",
                                    key=f"edit_tower_{idx_site}_{i}"
                                )
                    else:
                        st.info("ℹ️ Kolom tahapan Dismantle Tower belum terdeteksi.")
                
                with subtab_equip:
                    st.markdown("#### ⚙️ Tanggal Tahapan Dismantle Equipment")
                    if grup_equipment:
                        cols_e = st.columns(2 if len(grup_equipment) <= 2 else 3)
                        for i, col_name in enumerate(grup_equipment):
                            val_lama_dt = parse_tanggal_ke_date(data_site[col_name])
                            with cols_e[i % 3]:
                                input_progress_baru[col_name] = st.date_input(
                                    label=f"📅 {col_name}",
                                    value=val_lama_dt,
                                    format="DD/MM/YYYY",
                                    key=f"edit_equip_{idx_site}_{i}"
                                )
                    else:
                        st.info("ℹ️ Kolom tahapan Dismantle Equipment belum terdeteksi.")
                
                with subtab_reloc:
                    st.markdown("#### 🚚 Tanggal Tahapan Relocation")
                    if grup_relocation:
                        cols_r = st.columns(2 if len(grup_relocation) <= 2 else 3)
                        for i, col_name in enumerate(grup_relocation):
                            val_lama_dt = parse_tanggal_ke_date(data_site[col_name])
                            with cols_r[i % 3]:
                                input_progress_baru[col_name] = st.date_input(
                                    label=f"📅 {col_name}",
                                    value=val_lama_dt,
                                    format="DD/MM/YYYY",
                                    key=f"edit_reloc_{idx_site}_{i}"
                                )
                    else:
                        st.info("ℹ️ Kolom tahapan Relocation belum terdeteksi.")
                
                st.divider()
                submit_sow = st.form_submit_button("💾 Simpan Tanggal SOW ke Google Sheets", type="primary", use_container_width=True)
                
                if submit_sow:
                    try:
                        with st.spinner("⏳ Menyimpan tanggal SOW ke Google Sheets..."):
                            for nama_col, val_date in input_progress_baru.items():
                                if val_date is not None:
                                    val_str = val_date.strftime("%d-%m-%Y")
                                else:
                                    val_str = ""
                                df[nama_col] = df[nama_col].astype(str)
                                df.at[idx_site, nama_col] = val_str
                            conn.update(data=df)
                            
                            st.session_state["notif"] = (
                                "success", 
                                f"✅ Berhasil mengupdate tanggal SOW untuk site: **{nama_site_terpilih}**!"
                            )
                            st.rerun()
                    except Exception as e:
                        st.session_state["notif"] = (
                            "error", 
                            f"❌ Gagal menyimpan perubahan progress SOW: {e}"
                        )
                        st.rerun()
        else:
            st.warning("⚠️ Tidak ada kolom SOW yang terdeteksi di Baris 1 Google Sheets.")
