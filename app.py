import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Konfigurasi Halaman Web
st.set_page_config(
    page_title="Progress CMI - Realtime Editor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Progress CMI - Realtime Editor")
st.caption("Aplikasi monitoring & update data proyek secara real-time (Google Sheets).")

# 2. Inisialisasi Koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Sidebar: Pilih Tab / Worksheet
daftar_tab = [
    "Reloc",
    "Account",
    "List Material Inbound",
    "LOS Survey",
    "List team",
    "Email Permit",
    "SPH",
    "oret2",
    "Update Boram",
    "CMI-RLC-Nasional"
]

st.sidebar.header("⚙️ Pengaturan")
tab_terpilih = st.sidebar.selectbox("📂 Pilih Tab (Worksheet):", daftar_tab, index=0)

if st.sidebar.button("🔄 Refresh Data Terbaru", use_container_width=True):
    st.rerun()

st.divider()

# 4. Baca Data dari Google Sheets (header=2 agar melewati baris merged di atasnya)
try:
    with st.spinner(f"Mengambil data dari tab '{tab_terpilih}'..."):
        df = conn.read(worksheet=tab_terpilih, ttl=0, header=2)
except Exception as e:
    st.error(f"❌ Gagal membaca tab **'{tab_terpilih}'**: {e}")
    st.stop()

# ==========================================================
# 📱 FITUR EDIT CEPAT KHUSUS HP (TANPA SCROLL HORIZONTAL)
# ==========================================================
with st.expander("📱 Fitur Edit Cepat Khusus HP (Klik untuk Buka/Tutup)", expanded=True):
    st.write("💡 **Cara Cepat Update Data di HP:**")
    
    # Buat daftar pilihan baris berdasarkan 3 kolom pertama (biasanya NO, Site ID, Site Name)
    pilihan_baris = []
    for idx, row in df.iterrows():
        info_baris = " | ".join([str(val) for val in row.iloc[:3] if pd.notna(val) and str(val).strip() != ""])
        if not info_baris:
            info_baris = f"Baris {idx + 1}"
        pilihan_baris.append((idx, info_baris))
    
    # 1. Pilih Site / Baris
    idx_terpilih, label_site = st.selectbox(
        "🔍 1. Cari & Pilih Site:",
        options=pilihan_baris,
        format_func=lambda x: x[1],
        key="hp_select_site"
    )
    
    # 2. Pilih Kolom Target (Bisa pilih 1 atau beberapa kolom sekaligus!)
    kolom_terpilih = st.multiselect(
        "🎯 2. Pilih Kolom yang Mau Diubah (misal: Start Dismantle):",
        options=list(df.columns),
        placeholder="Klik di sini & pilih nama kolom..."
    )
    
    # 3. Munculkan Input Box KHUSUS untuk kolom yang dipilih saja
    if kolom_terpilih:
        st.write("✏️ **3. Masukkan Nilai Baru:**")
        nilai_baru_dict = {}
        
        for col in kolom_terpilih:
            val_lama = df.at[idx_terpilih, col]
            val_lama_str = "" if pd.isna(val_lama) else str(val_lama)
            
            nilai_baru_dict[col] = st.text_input(
                label=f"Kolom [{col}]  —  (Nilai saat ini: {val_lama_str})",
                value=val_lama_str,
                key=f"hp_input_{col}"
            )
        
        st.write("") # Spasi
        # 4. Tombol Simpan Edit Cepat
        if st.button("⚡ Simpan Edit Cepat ke Google Sheets", type="primary", use_container_width=True):
            try:
                with st.spinner("Menyimpan ke Google Sheets..."):
                    for col, val in nilai_baru_dict.items():
                        df.at[idx_terpilih, col] = val
                    
                    conn.update(worksheet=tab_terpilih, data=df)
                    st.success(f"✅ Berhasil memperbarui data untuk: **{label_site}**!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal menyimpan: {e}")
    else:
        st.caption("👈 *Pilih minimal 1 kolom di atas agar kotak input nilai baru muncul.*")

st.divider()

# ==========================================================
# 📋 TABEL LENGKAP (SPREADSHEET EDITOR) + FILTER
# ==========================================================
st.subheader(f"📋 Tabel Data: Tab [{tab_terpilih}]")

col_search, _ = st.columns([4, 1])
with col_search:
    keyword = st.text_input(
        "🔍 Filter Tabel (Cari Site ID / Nama):",
        placeholder="Contoh: R1200302 / BANGUN PURBA / JAILOLO"
    )

if keyword:
    mask = df.astype(str).apply(lambda x: x.str.contains(keyword, case=False, na=False)).any(axis=1)
    df_display = df[mask]
    st.caption(f"Menampilkan **{len(df_display)}** baris yang cocok dengan kata kunci **'{keyword}'**.")
else:
    df_display = df

edited_df = st.data_editor(
    df_display,
    num_rows="dynamic",
    use_container_width=True,
    key=f"editor_tabel_{tab_terpilih}"
)

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 Simpan Perubahan Tabel", type="primary", use_container_width=True):
        try:
            with st.spinner("Menyimpan tabel ke Google Sheets..."):
                if keyword:
                    df.update(edited_df)
                    data_to_save = df
                else:
                    data_to_save = edited_df

                conn.update(worksheet=tab_terpilih, data=data_to_save)
                st.success("✅ Seluruh tabel berhasil diperbarui di Google Sheets.")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Gagal menyimpan perubahan tabel: {e}")
