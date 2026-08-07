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

# Custom CSS untuk Kartu Catatan (Smart Notes) agar tampil modern & berwarna
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
        margin-bottom: 12px;
    }
    .site-item {
        font-size: 0.92rem;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px dashed rgba(255, 255, 255, 0.15);
        line-height: 1.4;
    }
    .site-item:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    .site-detail {
        font-size: 0.82rem;
        opacity: 0.9;
        display: block;
        margin-top: 4px;
        margin-left: 14px;
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
# 6. FUNGSI UTAMA: PENCARIAN KOLOM, PARSER TANGGAL, & SMART NOTES
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

def parse_tanggal_ke_date(val):
    """Menerjemahkan teks dari Google Sheets menjadi objek tanggal untuk kalender pop-up."""
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if val_str in ["", "-", "nan", "None", "NaT"]:
        return None
    try:
        dt = pd.to_datetime(val_str, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.date()
    except:
        pass
    return None

def ambil_info_tambahan(row, col_status, grup_kolom):
    """Mendeteksi seluruh tahapan milestone di grup SOW terkait untuk ditampilkan di Smart Notes."""
    info_list = []
    for col in grup_kolom:
        if col == col_status or col in [col_site_id, col_site_name]:
            continue
        val = str(row.get(col, "")).strip()
        if val and val.lower() not in ["nan", "none", "-", "", "nat"]:
            info_list.append(f"<b>{col}:</b> {val}")
    
    if info_list:
        return "<span class='site-detail'>↳ &nbsp;" + " &nbsp;|&nbsp; ".join(info_list) + "</span>"
    return ""

def buat_grafik_status_berwarna(series_data):
    """Membuat grafik batang (Altair) berwarna khusus untuk status Done, Progress, dan Plan."""
    df_chart = series_data.replace("", pd.NA).dropna().astype(str).value_counts().reset_index()
    df_chart.columns = ["Status", "Jumlah"]
    
    domain_warna = ["Done", "DONE", "Progress", "In Progress", "IN PROGRESS", "Plan", "PLAN", "Planning"]
    range_warna = [
        "#10B981", "#10B981",  # Hijau Emerald
        "#F59E0B", "#F59E0B", "#F59E0B",  # Kuning Amber
        "#8B5CF6", "#8B5CF6", "#8B5CF6"   # Ungu Modern
    ]
    
    chart = alt.Chart(df_chart).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=45).encode(
        x=alt.X("Status:N", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=12)),
        y=alt.Y("Jumlah:Q", title="Jumlah Site"),
        color=alt.Color("Status:N", scale=alt.Scale(domain=domain_warna, range=range_warna), legend=None),
        tooltip=["Status", "Jumlah"]
    ).properties(height=260)
    
    st.altair_chart(chart, use_container_width=True)

def tampilkan_catatan_status_site_berwarna(df_data, col_status, grup_kolom):
    """Menampilkan daftar site berdasar status + detail tahapan pada kartu Smart Notes."""
    if not col_status or col_status not in df_data.columns:
        return
    
    st.markdown("##### 📌 Catatan Daftar Site & Tahapan Pekerjaan")
    
    kategori_done = df_data[df_data[col_status].astype(str).str.strip().str.upper() == "DONE"]
    kategori_prog = df_data[df_data[col_status].astype(str).str.strip().str.upper().isin(["IN PROGRESS", "PROGRESS", "ON PROGRESS"])]
    kategori_plan = df_data[df_data[col_status].astype(str).str.strip().str.upper().isin(["PLAN", "PLANNING", ""])]
    
    col1, col2, col3 = st.columns(3)
    
    # --- KARTU 1: DONE ---
    with col1:
        items_html = ""
        if not kategori_done.empty:
            for _, row in kategori_done.iterrows():
                s_id = str(row.get(col_site_id, "")).strip()
                s_name = str(row.get(col_site_name, "")).strip()
                detail_info = ambil_info_tambahan(row, col_status, grup_kolom)
                items_html += f"<div class='site-item'>• <b>{s_id}</b> — {s_name}{detail_info}</div>"
        else:
            items_html = "<div class='site-item'><i>Belum ada site selesai.</i></div>"
            
        st.markdown(f"""
        <div class="card-done">
            <div class="card-title" style="color: #34D399;">🟢 DONE ({len(kategori_done)} Site)</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)
                
    # --- KARTU 2: PROGRESS ---
    with col2:
        items_html = ""
        if not kategori_prog.empty:
            for _, row in kategori_prog.iterrows():
                s_id = str(row.get(col_site_id, "")).strip()
                s_name = str(row.get(col_site_name, "")).strip()
                detail_info = ambil_info_tambahan(row, col_status, grup_kolom)
                items_html += f"<div class='site-item'>• <b>{s_id}</b> — {s_name}{detail_info}</div>"
        else:
            items_html = "<div class='site-item'><i>Belum ada site in progress.</i></div>"
            
        st.markdown(f"""
        <div class="card-progress">
            <div class="card-title" style="color: #FBBF24;">🟡 PROGRESS ({len(kategori_prog)} Site)</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)
                
    # --- KARTU 3: PLAN / LAINNYA ---
    with col3:
        items_html = ""
        if not kategori_plan.empty:
            for _, row in kategori_plan.iterrows():
                s_id = str(row.get(col_site_id, "")).strip()
                s_name = str(row.get(col_site_name, "")).strip()
                detail_info = ambil_info_tambahan(row, col_status, grup_kolom)
                items_html += f"<div class='site-item'>• <b>{s_id}</b> — {s_name}{detail_info}</div>"
        else:
            items_html = "<div class='site-item'><i>Belum ada site berstatus plan.</i></div>"
            
        st.markdown(f"""
        <div class="card-plan">
            <div class="card-title" style="color: #C084FC;">🟣 PLAN / LAINNYA ({len(kategori_plan)} Site)</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. MENU UTAMA: DASHBOARD vs REALTIME EDITOR
# -----------------------------------------------------------------------------
menu_dash, menu_editor = st.tabs(["📈 Dashboard & Analytics", "📝 Realtime Editor"])

# =============================================================================
# MENU 1: DASHBOARD & ANALYTICS PER SOW (PREMIUM & SMART NOTES)
# =============================================================================
with menu_dash:
    st.subheader("📊 Dashboard Analytics per Scope of Work (SOW)")
    
    # --- SEARCH & FILTER BERDASARKAN SITE ID ---
    daftar_site_dash = ["Semua Site ID"]
    for _, row in df.iterrows():
        val_id = str(row.get(col_site_id, "")).strip()
        val_name = str(row.get(col_site_name, "")).strip()
        if val_id or val_name:
            daftar_site_dash.append(f"{val_id} — {val_name}")
            
    pilih_site_dash = st.selectbox(
        "🔍 Cari & Filter berdasarkan Site ID (Ketik untuk mencari):",
        options=daftar_site_dash,
        key="filter_site_dash"
    )
    
    if pilih_site_dash == "Semua Site ID":
        df_filter = df
    else:
        # Ambil kode ID di sebelah kiri tanda ' — '
        id_terpilih = pilih_site_dash.split(" — ")[0].strip()
        df_filter = df[df[col_site_id].astype(str).str.strip() == id_terpilih]

    st.divider()
    
    dash_tower, dash_equip, dash_reloc = st.tabs([
        "🏗️ Dismantle Tower", 
        "⚙️ Dismantle Equipment", 
        "🚚 Relocation"
    ])
    
    grup_tower_cols = cari_kolom_grup(["Survey Tower", "Report Survey Tower", "Dismantle Tower", "BAST"])
    grup_equip_cols = cari_kolom_grup(["Survey Equipment", "Report Survey Equipment", "Dismantle Equipment", "Inbound Material"])
    grup_reloc_cols = cari_kolom_grup(["Survey Relocation", "Report Survey Relocation", "Relocation", "OA", "ATP MS"])
    
    # --- DASHBOARD A: DISMANTLE TOWER ---
    with dash_tower:
        st.markdown("#### 📈 Analytics: Dismantle Tower")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Site Target", len(df_filter))
        
        col_dt = cari_nama_kolom("Dismantle Tower")
        with c2:
            if col_dt and col_dt in df_filter.columns:
                done_t = len(df_filter[df_filter[col_dt].astype(str).str.upper() == "DONE"])
                st.metric("Tower Done", done_t)
            else:
                st.metric("Tower Done", 0)
        with c3:
            if col_dt and col_dt in df_filter.columns:
                sisa_t = len(df_filter) - done_t
                st.metric("Progress", sisa_t)
            else:
                st.metric("Progress", len(df_filter))
                
        st.markdown("##### Sebaran Status Dismantle Tower:")
        if col_dt and col_dt in df_filter.columns:
            buat_grafik_status_berwarna(df_filter[col_dt])
            tampilkan_catatan_status_site_berwarna(df_filter, col_dt, grup_tower_cols)
        else:
            st.info("ℹ️ Kolom 'Dismantle Tower' belum terdeteksi.")
            
    # --- DASHBOARD B: DISMANTLE EQUIPMENT ---
    with dash_equip:
        st.markdown("#### 📈 Analytics: Dismantle Equipment")
        e1, e2, e3 = st.columns(3)
        with e1:
            st.metric("Total Site Target", len(df_filter))
            
        col_de = cari_nama_kolom("Dismantle Equipment")
        with e2:
            if col_de and col_de in df_filter.columns:
                done_e = len(df_filter[df_filter[col_de].astype(str).str.upper() == "DONE"])
                st.metric("Equipment Done", done_e)
            else:
                st.metric("Equipment Done", 0)
        with e3:
            if col_de and col_de in df_filter.columns:
                sisa_e = len(df_filter) - done_e
                st.metric("Progress", sisa_e)
            else:
                st.metric("Progress", len(df_filter))
                
        st.markdown("##### Sebaran Status Dismantle Equipment:")
        if col_de and col_de in df_filter.columns:
            buat_grafik_status_berwarna(df_filter[col_de])
            tampilkan_catatan_status_site_berwarna(df_filter, col_de, grup_equip_cols)
        else:
            st.info("ℹ️ Kolom 'Dismantle Equipment' belum terdeteksi.")
            
    # --- DASHBOARD C: RELOCATION ---
    with dash_reloc:
        st.markdown("#### 📈 Analytics: Site Relocation")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Total Target Relokasi", len(df_filter))
            
        col_reloc = cari_nama_kolom("Relocation")
        with r2:
            if col_reloc and col_reloc in df_filter.columns:
                done_r = len(df_filter[df_filter[col_reloc].astype(str).str.upper() == "DONE"])
                st.metric("Relocation Done", done_r)
            else:
                st.metric("Relocation Done", 0)
        with r3:
            if col_reloc and col_reloc in df_filter.columns:
                sisa_r = len(df_filter) - done_r
                st.metric("Progress", sisa_r)
            else:
                st.metric("Progress", len(df_filter))
                
        st.markdown("##### Progress Status Relokasi:")
        if col_reloc and col_reloc in df_filter.columns:
            buat_grafik_status_berwarna(df_filter[col_reloc])
            tampilkan_catatan_status_site_berwarna(df_filter, col_reloc, grup_reloc_cols)
        else:
            st.info("ℹ️ Kolom 'Relocation' belum terdeteksi.")

# =============================================================================
# MENU 2: REALTIME EDITOR (GATE 1 & GATE 2)
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

    pilihan_terpilih = st.selectbox(
        "Pilih Site yang ingin dilihat atau diedit:",
        options=daftar_pilihan_site,
        format_func=lambda x: x[1],
        key="select_gate_site"
    )

    if not pilihan_terpilih:
        st.info("👈 Silakan pilih Site di atas terlebih dahulu.")
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

    # =========================================================================
    # TAB 4: SOW DENGAN INPUT KALENDER POP-UP (DATE INPUT)
    # =========================================================================
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
                
                # --- SUB-TAB 1: DISMANTLE TOWER ---
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
                
                # --- SUB-TAB 2: DISMANTLE EQUIPMENT ---
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
                
                # --- SUB-TAB 3: RELOCATION ---
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
