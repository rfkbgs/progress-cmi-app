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

# 4. Baca Data dari Google Sheets
# PENTING: header=2 digunakan agar Python membaca Baris ke-3 Excel sebagai nama kolom
# (karena indeks Python mulai dari 0 -> 0=Baris 1, 1=Baris 2, 2=Baris 3)
try:
    with st.spinner(f"Mengambil data dari tab '{tab_terpilih}'..."):
        df = conn.read(worksheet=tab_terpilih, ttl=0, header=2)
except Exception as e:
    st.error(f"❌ Gagal membaca tab **'{tab_terpilih}'**: {e}")
    st.stop()

# 5. Fitur Pencarian / Filter Cepat
st.subheader(f"📝 Edit Data: Tab [{tab_terpilih}]")

col_search, col_reset = st.columns([4, 1])
with col_search:
    keyword = st.text_input(
        "🔍 Cari Site ID / Nama Site / kata kunci lain (opsional):",
        placeholder="Contoh: R1200302 / BANGUN PURBA / JAILOLO"
    )

# Filter dataframe jika ada kata kunci pencarian
if keyword:
    mask = df.astype(str).apply(
        lambda x: x.str.contains(keyword, case=False, na=False)
    ).any(axis=1)
    df_display = df[mask]
    st.caption(f"Menampilkan **{len(df_display)}** baris yang cocok dengan kata kunci **'{keyword}'**.")
else:
    df_display = df

# 6. Tabel Editor Interaktif (Judul kolom sekarang sudah bersih dari Unnamed: ...)
edited_df = st.data_editor(
    df_display,
    num_rows="dynamic",
    use_container_width=True,
    key=f"editor_{tab_terpilih}"
)

# 7. Tombol Simpan Perubahan ke Google Sheets
col1, col2 = st.columns([1, 4])
with col1:
    tombol_simpan = st.button("💾 Simpan Perubahan", type="primary", use_container_width=True)

if tombol_simpan:
    try:
        with st.spinner("Menyimpan perubahan ke Google Sheets..."):
            # Jika tabel sedang difilter, update hanya baris yang diedit ke dataframe utama
            if keyword:
                df.update(edited_df)
                data_to_save = df
            else:
                data_to_save = edited_df

            # Update data ke Google Sheets
            conn.update(worksheet=tab_terpilih, data=data_to_save)
            st.success("✅ Berhasil! Data di Google Sheets sudah diperbarui.")
            st.rerun()
    except Exception as e:
        st.error(f"❌ Gagal menyimpan perubahan: {e}")
