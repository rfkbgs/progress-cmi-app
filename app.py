import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Konfigurasi Halaman Web
st.set_page_config(
    page_title="Progress CMI - Realtime Editor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Progress CMI - Realtime Editor (Google Sheets)")
st.caption("Aplikasi monitoring & update data proyek secara real-time.")

# 2. Inisialisasi Koneksi ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Sidebar: Pilih Tab / Worksheet yang Mau Dibuka
# (Sesuaikan daftar nama ini persis seperti nama tab di bagian bawah Google Sheets kamu)
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

# Tombol manual refresh di sidebar
if st.sidebar.button("🔄 Refresh Data Terbaru", use_container_width=True):
    st.rerun()

st.divider()

# 4. Baca Data dari Google Sheets (sesuai tab yang dipilih)
try:
    with st.spinner(f"Mengambil data dari tab '{tab_terpilih}'..."):
        # ttl=0 memastikan data selalu fresh (tanpa cache lama)
        df = conn.read(worksheet=tab_terpilih, ttl=0)
except Exception as e:
    st.error(f"❌ Gagal membaca tab **'{tab_terpilih}'**.")
    st.warning("💡 **Tips Solusi 404:** Pastikan nama tab yang dipilih sama persis (huruf besar/kecil dan spasinya) dengan yang ada di Google Sheets kamu.")
    st.stop()

# 5. Tampilkan Tabel Interaktif (Data Editor)
st.subheader(f"📝 Edit Data: Tab [{tab_terpilih}]")
st.info("💡 Kamu bisa langsung mengetik di dalam tabel, menambah baris baru di paling bawah, atau menghapus baris. Jangan lupa klik tombol **Simpan** setelah selesai edit!")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",        # Mengizinkan penambahan/penghapusan baris
    use_container_width=True,  # Tabel melebar memenuhi layar
    key=f"editor_{tab_terpilih}"
)

# 6. Tombol Simpan Perubahan ke Google Sheets
col1, col2 = st.columns([1, 4])
with col1:
    tombol_simpan = st.button("💾 Simpan Perubahan", type="primary", use_container_width=True)

if tombol_simpan:
    try:
        with st.spinner(f"Menyimpan perubahan ke tab '{tab_terpilih}'..."):
            # PENTING: sertakan parameter worksheet agar tidak salah alamat ke Sheet1
            conn.update(worksheet=tab_terpilih, data=edited_df)
            st.success(f"✅ Berhasil! Data pada tab '{tab_terpilih}' sudah diperbarui di Google Sheets.")
            st.rerun()
    except Exception as e:
        st.error(f"❌ Gagal menyimpan perubahan: {e}")
