import streamlit as st
import pandas as pd
import openpyxl

# 1. Pengaturan Halaman
st.set_page_config(page_title="Progress CMI", page_icon="📊", layout="centered")
st.title("📊 Monitoring & Update Progress CMI")

EXCEL_FILE = "Progress CMI-All Project.xlsx"

# --- FITUR AUTO-DETECT HEADER ---
def load_data_otomatis(sheet_name):
    # Baca 10 baris pertama untuk melacak posisi judul kuning
    df_temp = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=None, nrows=10)
    
    header_row_idx = 0
    for i, row in df_temp.iterrows():
        teks_baris = " ".join([str(val).lower() for val in row.values])
        if "site id" in teks_baris or "site name" in teks_baris or "tenant" in teks_baris:
            header_row_idx = i
            break
            
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=header_row_idx)
    df = df.dropna(how="all")
    return df, header_row_idx

def update_sel_excel(sheet_name, excel_row, excel_col, nilai_baru):
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb[sheet_name]
    ws.cell(row=excel_row, column=excel_col, value=nilai_baru)
    wb.save(EXCEL_FILE)

# 2. Pilih Sheet
sheet_pilihan = st.selectbox("📂 Pilih Sheet / Kategori:", ["Reloc", "Account"])

try:
    df, header_idx = load_data_otomatis(sheet_pilihan)

    st.markdown("---")
    st.subheader("⚡ Update Cepat Data Site")

    # --- LANGKAH 1: PILIH KOLOM IDENTITAS ---
    daftar_kolom = list(df.columns)
    
    default_site_col = 0
    for idx, col in enumerate(daftar_kolom):
        if "site name" in str(col).lower() or "site id" in str(col).lower():
            default_site_col = idx
            break

    kolom_site = st.selectbox(
        "1️⃣ Pilih Kolom Identitas Site (Acuan Pencarian):", 
        daftar_kolom, 
        index=default_site_col
    )
    
    daftar_site = df[kolom_site].dropna().astype(str).unique().tolist()
    daftar_site = [site for site in daftar_site if site.lower() != "nan" and site.strip() != ""]

    if len(daftar_site) == 0:
        st.warning("⚠️ Kolom yang dipilih tidak berisi data teks site. Silakan pilih kolom lain di atas.")
    else:
        # --- LANGKAH 2: CARI & PILIH SITE ---
        site_dipilih = st.selectbox("2️⃣ Ketik & Pilih Nama / ID Site:", daftar_site)

        baris_cocok = df[df[kolom_site].astype(str) == site_dipilih]
        
        if not baris_cocok.empty:
            idx = baris_cocok.index[0]

            # --- LANGKAH 3: PILIH KOLOM YANG INGIN DIUPDATE ---
            kolom_target = st.selectbox("3️⃣ Pilih Judul Kolom yang Ingin Diupdate:", daftar_kolom)
            col_idx = daftar_kolom.index(kolom_target)

            nilai_lama = df.at[idx, kolom_target]
            if pd.isna(nilai_lama):
                nilai_lama = "-"

            # --- LANGKAH 4: FORM INPUT YANG LEBIH SIMPEL & BERSIH ---
            with st.form("form_update_cmi"):
                nilai_baru = st.text_input(
                    f"✏️ Masukkan nilai baru untuk '{kolom_target}':", 
                    value=str(nilai_lama) if nilai_lama != "-" else ""
                )
                
                tombol_simpan = st.form_submit_button("💾 Simpan Perubahan")

                if tombol_simpan:
                    excel_row = idx + header_idx + 2
                    excel_col = col_idx + 1

                    update_sel_excel(sheet_pilihan, excel_row, excel_col, nilai_baru)
                    
                    st.success(f"✅ Berhasil! '{kolom_target}' pada **{site_dipilih}** diperbarui menjadi **{nilai_baru}**.")
                    st.rerun()
        else:
            st.error("Data site tidak ditemukan.")

    # --- TAMPILAN TABEL DATA ---
    st.markdown("---")
    st.subheader("📋 Tabel Data Keseluruhan")
    st.metric(label="Total Site Terdaftar", value=f"{len(df)} Site")
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")