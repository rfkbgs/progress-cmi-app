import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Progress CMI - Realtime Editor", layout="wide")

st.title("📊 Progress CMI - Realtime Editor (Google Sheets)")

# 1. Buat koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Fungsi untuk membaca data (ttl=0 agar selalu ambil data terbaru saat di-refresh)
try:
    # Jika kamu mau spesifik baca worksheet/tab tertentu, tambahkan parameter worksheet="NamaTab"
    # Contoh: conn.read(worksheet="Reloc", ttl=0)
    df = conn.read(ttl=0)
except Exception as e:
    st.error(f"Gagal membaca data dari Google Sheets: {e}")
    st.stop()

# Tombol manual refresh
if st.button("🔄 Refresh Data Terbaru"):
    st.rerun()

st.subheader("📝 Edit Data Progress:")
st.caption("Ubah data langsung pada tabel di bawah ini, lalu klik tombol Simpan untuk memperbarui Google Sheets.")

# 3. Tampilkan tabel interaktif (Data Editor)
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="cmi_editor"
)

# 4. Tombol simpan perubahan ke Google Sheets
if st.button("💾 Simpan Perubahan ke Google Sheets", type="primary"):
    try:
        with st.spinner("Menyimpan perubahan ke Google Sheets..."):
            conn.update(data=edited_df)
            st.success("✅ Data berhasil diperbarui secara real-time di Google Sheets!")
            st.rerun()
    except Exception as e:
        st.error(f"❌ Gagal menyimpan perubahan: {e}")
