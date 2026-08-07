import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Progress CMI - Dashboard & Editor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Progress CMI - Dashboard & Realtime Editor")
st.caption("Monitoring visual & update data proyek secara real-time (Google Sheets - Single Sheet).")

# -----------------------------------------------------------------------------
# 2. INISIALISASI KONEKSI KE GOOGLE SHEETS
# -----------------------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# -----------------------------------------------------------------------------
# 3. SIDEBAR (TOMBOL REFRESH)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Pengaturan")
st.sidebar.caption("Google Sheets terhubung pada Sheet utama (Sheet tunggal).")

if st.sidebar.button("🔄 Refresh Data Terbaru", use_container_width=True):
    st.rerun()

st.divider()

# -----------------------------------------------------------------------------
# 4. MEMBACA DATA GOOGLE SHEETS (HEADER=0 / BARIS 1 SEBAGAI JUDUL KOLOM)
# -----------------------------------------------------------------------------
try:
    with st.spinner("Mengambil data dari Google Sheets..."):
        df = conn.read(ttl=0, header=0)
        # Hapus baris yang kosong sepenuhnya agar rapi & tidak error
        df = df.dropna(how="all").reset_index(drop=True)
except Exception as e:
    st.error(f"❌ Gagal membaca data Google Sheets: {e}")
    st.stop()

if df.empty:
    st.warning("⚠️ Tabel di Google Sheets masih kosong. Pastikan Baris 1 berisi nama kolom dan minimal ada 1 baris data di Baris 2.")
    st.stop()

# -----------------------------------------------------------------------------
# 5. FUNGSI PENCARIAN KOLOM & TABEL DETAIL
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
    """Mencari daftar kolom asli berdasarkan kumpulan kata kunci (tanpa duplikat)."""
    ditemukan = []
    for kunci in kata_kunci_list:
        for col in df.columns:
            if kunci.lower() in str(col).lower() and col not in ditemukan:
                ditemukan.append(col)
    return ditemukan

# Deteksi kolom Site ID & Site Name utama
col_site_id = cari_nama_kolom("Site Id") or cari_nama_kolom("Site ID") or df.columns[0]
col_site_name = cari_nama_kolom("Site Name") or (df.columns[1] if len(df.columns) > 1 else df.columns[0])

def tampilkan_detail_site_per_status(df_data, col_status, kolom_grup, key_prefix):
    """Menampilkan tabel daftar site secara detail berdasarkan filter status tertentu."""
    if not col_status or col_status not in df_data.columns:
        return
    
    st.markdown("---")
    st.markdown("##### 📋 Detail Daftar Site & Status Pekerjaan")
    
    # Ambil daftar status unik yang ada di kolom tersebut
    status_unik = sorted(list(set(
        str(val).strip() 
        for val in df_data[col_status].dropna() 
        if str(val).strip() != ""
    )))
    
    # Filter dropdown untuk memilih status (Done / Progress / Plan / Semua)
    pilih_status = st.selectbox(
        "🔍 Filter Daftar Site berdasar Status:",
        options=["Semua Status"] + status_unik,
        key=f"filter_tbl_{key_prefix}"
    )
    
    if pilih_status == "Semua Status":
        df_tampil = df_data.copy()
    else:
        df_tampil = df_data[df_data[col_status].astype(str).str.strip() == pilih_status]
        
    # Tentukan kolom apa saja yang muncul di tabel detail agar rapi & tidak kepanjangan
    col_wajib = [c for c in [col_site_id, col_site_name, "Provinsi", "Kabupaten"] if c in df_tampil.columns]
    col_tambahan = [c for c in kolom_grup if c in df_tampil.columns and c not in col_wajib]
    col_final = col_wajib + col_tambahan
    
    if col_status not in col_final and col_status in df_tampil.columns:
        col_final.append(col_status)
        
    st.dataframe(
        df_tampil[col_final],
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Menampilkan **{len(df_tampil)}** site untuk filter: **{pilih_status}**")

# -----------------------------------------------------------------------------
# 6. MENU UTAMA: DASHBOARD vs REALTIME EDITOR
# -----------------------------------------------------------------------------
menu_dash, menu_editor = st.tabs(["📈 Dashboard & Analytics", "📝 Realtime Editor"])

# =============================================================================
# MENU 1: DASHBOARD & ANALYTICS PER SOW (DENGAN TABEL DETAIL)
# =============================================================================
with menu_dash:
    st.subheader("📊 Dashboard Analytics per Scope of Work (SOW)")
    
    # 1. FILTER WILAYAH (Berlaku untuk semua SOW)
    prov_col = cari_nama_kolom("Provinsi")
    if prov_col and prov_col in df.columns:
        prov_list = ["Semua Provinsi"] + list(df[prov_col].dropna().unique())
        pilih_prov = st.selectbox("🔍 Filter Wilayah (Provinsi):", prov_list, key="filter_prov_dash")
        df_filter = df if pilih_prov == "Semua Provinsi" else df[df[prov_col] == pilih_prov]
    else:
        df_filter = df

    st.divider()
    
    # 2. SUB-TAB DASHBOARD KHUSUS PER SOW
    dash_tower, dash_equip, dash_reloc = st.tabs([
        "🏗️ Dismantle Tower", 
        "⚙️ Dismantle Equipment", 
        "🚚 Relocation"
    ])
    
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
            data_chart = df_filter[col_dt].replace("", pd.NA).dropna()
            if not data_chart.empty:
                st.bar_chart(data_chart.astype(str).value_counts())
            else:
                st.info("ℹ️ Belum ada status Dismantle Tower yang diisi pada tabel.")
                
            # --- TABEL DETAIL DISMANTLE TOWER ---
            grup_tower_dash = cari_kolom_grup(["Dismantle Tower", "Tanggal Dismantle Tower", "Status Tower", "Tgl Tower"])
            tampilkan_detail_site_per_status(df_filter, col_dt, grup_tower_dash, "dt")
        else:
            st.info("ℹ️ Kolom 'Dismantle Tower' belum terdeteksi.")
            
    # --- DASHBOARD B: DISMANTLE EQUIPMENT ---
    with dash_equip:
        st.markdown("#### 📈 Analytics: Dismantle Equipment & Tenant")
        e1, e2 = st.columns(2)
        with e1:
            st.metric("Total Equipment Target", len(df_filter))
            
        col_tenant = cari_nama_kolom("Tenant")
        with e2:
            if col_tenant and col_tenant in df_filter.columns:
                st.metric("Jumlah Tenant / Operator", df_filter[col_tenant].replace("", pd.NA).dropna().nunique())
            else:
                st.metric("Jumlah Tenant / Operator", 0)
                
        st.markdown("##### Beban Kerja per Tenant / Operator:")
        if col_tenant and col_tenant in df_filter.columns:
            data_chart = df_filter[col_tenant].replace("", pd.NA).dropna()
            if not data_chart.empty:
                st.bar_chart(data_chart.astype(str).value_counts())
            else:
                st.info("ℹ️ Belum ada data Tenant yang diisi pada tabel.")
        else:
            st.info("ℹ️ Kolom 'Tenant' belum terdeteksi.")
            
        # --- TABEL DETAIL DISMANTLE EQUIPMENT ---
        col_de = cari_nama_kolom("Dismantle Equipment") or col_tenant
        grup_equip_dash = cari_kolom_grup(["Dismantle Equipment", "Tenant", "Equipment", "Perangkat"])
        if col_de and col_de in df_filter.columns:
            tampilkan_detail_site_per_status(df_filter, col_de, grup_equip_dash, "de")
            
    # --- DASHBOARD C: RELOCATION ---
    with dash_reloc:
        st.markdown("#### 📈 Analytics: Site Relocation")
        r1, r2 = st.columns(2)
        with r1:
            st.metric("Total Target Relokasi", len(df_filter))
            
        col_new = cari_nama_kolom("Site Id New") or cari_nama_kolom("Site ID New")
        with r2:
            if col_new and col_new in df_filter.columns:
                reloc_ready = df_filter[col_new].replace("", pd.NA).dropna().count()
                st.metric("Sudah Ada Site ID New", reloc_ready)
            else:
                st.metric("Sudah Ada Site ID New", 0)
                
        st.markdown("##### Progress Status Relokasi:")
        col_reloc = cari_nama_kolom("Relocation")
        if col_reloc and col_reloc in df_filter.columns:
            data_chart = df_filter[col_reloc].replace("", pd.NA).dropna()
            if not data_chart.empty:
                st.bar_chart(data_chart.astype(str).value_counts())
            else:
                st.info("ℹ️ Belum ada status Relocation yang diisi pada tabel.")
                
            # --- TABEL DETAIL RELOCATION ---
            grup_reloc_dash = cari_kolom_grup(["Relocation", "Reloc", "Site Id Old", "Site Id New", "Old", "New", "Alamat"])
            tampilkan_detail_site_per_status(df_filter, col_reloc, grup_reloc_dash, "rel")
        else:
            st.info("ℹ️ Kolom 'Relocation' belum terdeteksi.")

# =============================================================================
# MENU 2: REALTIME EDITOR (GATE 1 & GATE 2)
# =============================================================================
with menu_editor:
    # -------------------------------------------------------------------------
    # GATE 1: PEMILIHAN SITE ID / SITE NAME (ANTI-CRASH)
    # -------------------------------------------------------------------------
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

    # Ambil data baris untuk site yang dipilih
    data_site = df.loc[idx_site]

    # -------------------------------------------------------------------------
    # GATE 2: 4 BAGIAN UTAMA (DETAIL INFORMATION, PERMIT, HSE, SOW)
    # -------------------------------------------------------------------------
    st.subheader(f"📌 Detail Site: **{nama_site_terpilih}**")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏢 Detail Information",
        "📑 Permit",
        "🛡️ HSE",
        "🛠️ SOW (Scope of Work) — [EDITABLE]"
    ])

    # --- TAB 1: DETAIL INFORMATION (READ-ONLY) ---
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

    # --- TAB 2: PERMIT (READ-ONLY) ---
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

    # --- TAB 3: HSE (READ-ONLY) ---
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

    # --- TAB 4: SOW (EDITABLE & BERLAPIS) ---
    with tab4:
        st.markdown("### 🛠️ SOW (Scope of Work) — Edit Detail Lapisan Pekerjaan")
        st.caption("Pilih kategori pekerjaan di bawah ini untuk mengedit data detail (Tanggal, Tenant, ID Lama/Baru, dll).")
        
        grup_tower = cari_kolom_grup(["Dismantle Tower", "Tanggal Dismantle Tower", "Status Tower", "Tgl Tower"])
        grup_equipment = cari_kolom_grup(["Dismantle Equipment", "Tenant", "Equipment", "Perangkat"])
        grup_relocation = cari_kolom_grup(["Relocation", "Reloc", "Site Id Old", "Site Id New", "Old", "New", "Alamat"])
        
        semua_kolom_sow = list(dict.fromkeys(grup_tower + grup_equipment + grup_relocation))
        
        if semua_kolom_sow:
            with st.form("form_update_sow_berlapis"):
                st.write(f"✏️ **Form Edit SOW Lengkap: {nama_site_terpilih}**")
                
                subtab_tower, subtab_equip, subtab_reloc = st.tabs([
                    "🏗️ Dismantle Tower",
                    "⚙️ Dismantle Equipment",
                    "🚚 Relocation"
                ])
                
                input_progress_baru = {}
                
                # Sub-Tab 1: Dismantle Tower
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
                
                # Sub-Tab 2: Dismantle Equipment
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
                
                # Sub-Tab 3: Relocation
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
                            for nama_col, val_baru in input_progress_baru.items():
                                df[nama_col] = df[nama_col].astype(str)
                                df.at[idx_site, nama_col] = str(val_baru)
                            
                            conn.update(data=df)
                            st.success(f"✅ Berhasil mengupdate detail SOW pada site: {nama_site_terpilih}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal menyimpan perubahan progress SOW: {e}")
        else:
            st.warning("⚠️ Tidak ada kolom SOW yang terdeteksi di Baris 1 Google Sheets.")
