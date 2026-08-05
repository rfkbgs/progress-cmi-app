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
try:
    with st.spinner(f"Mengambil data dari tab '{tab_terpilih}'..."):
        df = conn.read(worksheet=tab_terpilih, ttl=0)
except Exception as e:
    st.error(f"❌ Gagal membaca tab **'{tab_terpilih}'**: {e}")
    st.stop()

# 5. Buat 2 Menu Tab: Edit Cepat & Tabel Lengkap
tab_edit_cepat, tab_tabel_lengkap = st.tabs(["⚡ Menu Edit Cepat (Form Site)", "📋 Tabel Lengkap (Spreadsheet)"])

# ==========================================
# TAB 1: MENU EDIT CEPAT (FORM PER SITE)
# ==========================================
with tab_edit_cepat:
    st.subheader(f"⚡ Edit Cepat: Tab [{tab_terpilih}]")
    st.caption("Pilih baris atau Site ID yang ingin diubah tanpa perlu menggeser tabel horizontal.")
    
    # Deteksi baris data nyata (melewati baris header Excel yang merged/kosong di atas)
    # Kita buat daftar pilihan baris agar fleksibel di semua tab
    pilihan_baris = []
    for idx, row in df.iterrows():
        # Ambil ringkasan label dari kolom ke-1 & ke-2 (biasanya Site ID & Site Name)
        val_0 = str(row.iloc[0]) if pd.notna(row.iloc[0]) else "-"
        val_1 = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else "-"
        val_2 = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else "-"
        label = f"Baris {idx + 1} | {val_0} - {val_1} ({val_2})"
        pilihan_baris.append((idx, label))
    
    # Dropdown pilih baris yang mau diedit
    idx_terpilih, _ = st.selectbox(
        "🔍 Cari & Pilih Baris / Site ID:",
        options=pilihan_baris,
        format_func=lambda x: x[1],
        key="select_quick_edit"
    )
    
    # Form input untuk baris yang dipilih
    with st.form("form_edit_cepat"):
        st.write(f"**Mengubah Data Baris ke-{idx_terpilih + 1}:**")
        row_data = df.loc[idx_terpilih]
        
        # Tampilkan input secara grid 3 kolom agar rapi
        cols = st.columns(3)
        updated_values = {}
        
        for i, col_name in enumerate(df.columns):
            val_sekarang = row_data[col_name]
            val_sekarang_str = "" if pd.isna(val_sekarang) else str(val_sekarang)
            
            # Gunakan penamaan kolom yang nyaman dibaca
            label_col = f"Kolom {i+1}: {col_name}" if "Unnamed" in str(col_name) else str(col_name)
            
            with cols[i % 3]:
                updated_values[col_name] = st.text_input(
                    label=label_col,
                    value=val_sekarang_str,
                    key=f"input_{idx_terpilih}_{i}"
                )
        
        st.divider()
        submit_quick = st.form_submit_button("⚡ Simpan Edit Cepat ke Google Sheets", type="primary", use_container_width=True)
        
        if submit_quick:
            try:
                with st.spinner("Menyimpan perubahan dari Edit Cepat..."):
                    # Update baris di dataframe
                    for col_name, new_val in updated_values.items():
                        df.at[idx_terpilih, col_name] = new_val
                    
                    # Kirim ke Google Sheets
                    conn.update(worksheet=tab_terpilih, data=df)
                    st.success(f"✅ Baris ke-{idx_terpilih + 1} berhasil diperbarui di Google Sheets!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal menyimpan: {e}")

# ==========================================
# TAB 2: TABEL LENGKAP (SPREADSHEET EDITOR)
# ==========================================
with tab_tabel_lengkap:
    st.subheader(f"📋 Editor Tabel Lengkap: Tab [{tab_terpilih}]")
    st.caption("Edit langsung seperti di Excel. Jangan lupa klik tombol 'Simpan Tabel' di bawah setelah selesai.")
    
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_tabel_{tab_terpilih}"
    )
    
    col_a, col_b = st.columns([1, 4])
    with col_a:
        if st.button("💾 Simpan Tabel Lengkap", type="primary", use_container_width=True):
            try:
                with st.spinner("Menyimpan tabel ke Google Sheets..."):
                    conn.update(worksheet=tab_terpilih, data=edited_df)
                    st.success("✅ Seluruh tabel berhasil diperbarui di Google Sheets!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal menyimpan: {e}")
