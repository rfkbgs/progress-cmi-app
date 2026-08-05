import streamlit as st
import pandas as pd
import requests
import msal
import io

# ==========================================
# 1. KONFIGURASI HALAMAN (MOBILE FRIENDLY)
# ==========================================
st.set_page_config(
    page_title="Progress CMI-rfk",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("📊 Progress CMI-rfk")
st.caption("Monitoring & Update Proyek Real-Time via OneDrive")

# ==========================================
# 2. AUTENTIKASI MICROSOFT GRAPH API
# ==========================================
def get_access_token():
    try:
        azure_conf = st.secrets["azure"]
        authority = f"https://login.microsoftonline.com/{azure_conf['TENANT_ID']}"
        app = msal.ConfidentialClientApplication(
            azure_conf["CLIENT_ID"],
            authority=authority,
            client_credential=azure_conf["CLIENT_SECRET"]
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        
        if "access_token" in result:
            return result["access_token"]
        else:
            st.error("❌ Gagal mendapatkan token akses dari Azure.")
            st.json(result)  # Tampilkan detail error autentikasi jika token gagal
            return None
    except Exception as e:
        st.error(f"❌ Error Autentikasi: {e}")
        return None

# ==========================================
# 3. FUNGSI BACA DATA DARI ONEDRIVE
# ==========================================
@st.cache_data(ttl=10)
def load_all_sheets():
    token = get_access_token()
    if not token:
        return None
    
    user_email = st.secrets["azure"]["USER_EMAIL"]
    file_name = "Progress CMI-rfk.xlsx"
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{file_name}:/content"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Baca SEMUA tab (sheet_name=None) menjadi dictionary: {'NamaSheet': DataFrame}
        excel_data = pd.read_excel(io.BytesIO(response.content), sheet_name=None)
        return excel_data
    else:
        # --- DETEKTOR ERROR MICROSOFT ---
        st.error(f"❌ Gagal mengambil data dari OneDrive! (Status Code: {response.status_code})")
        st.warning("Pesan Error Asli dari Microsoft Graph API:")
        st.code(response.text, language="json")
        return None

# ==========================================
# 4. FUNGSI SIMPAN DATA KE ONEDRIVE
# ==========================================
def save_all_sheets_to_onedrive(sheets_dict):
    token = get_access_token()
    if not token:
        return False
        
    user_email = st.secrets["azure"]["USER_EMAIL"]
    file_name = "Progress CMI-rfk.xlsx"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{file_name}:/content"
    
    # Simpan kembali semua sheet agar tab lain tidak hilang
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in sheets_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    
    response = requests.put(url, headers=headers, data=output)
    if response.status_code in [200, 201]:
        st.cache_data.clear()
        return True
    else:
        st.error(f"❌ Gagal menyimpan ke OneDrive (Status Code: {response.status_code})")
        st.code(response.text, language="json")
        return False

# ==========================================
# 5. ANTARMUKA PENGGUNA (UI / UX)
# ==========================================

# Tombol Refresh Manual
col_refresh, _ = st.columns([1, 2])
with col_refresh:
    if st.button("🔄 Refresh Data Terbaru", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# Load Data dari OneDrive
sheets_data = load_all_sheets()

if sheets_data is not None:
    # Pilihan Tab/Sheet
    sheet_names = list(sheets_data.keys())
    selected_sheet = st.selectbox("📁 Pilih Tab / Sheet:", sheet_names)
    
    df_current = sheets_data[selected_sheet]
    
    # Mode Pencarian Cepat
    search_query = st.text_input("🔍 Cari data pada tabel ini:", placeholder="Ketik kata kunci...")
    if search_query:
        mask = df_current.astype(str).apply(
            lambda x: x.str.contains(search_query, case=False, na=False)
        ).any(axis=1)
        df_display = df_current[mask]
    else:
        df_display = df_current

    # Tampilkan Data Editor
    st.write(f"**Menampilkan Sheet:** `{selected_sheet}`")
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        num_rows="dynamic",
        key=f"editor_{selected_sheet}"
    )

    st.divider()

    # Tombol Simpan Perubahan ke OneDrive
    if st.button("💾 Simpan Perubahan ke OneDrive", type="primary", use_container_width=True):
        with st.spinner("Mengunggah data ke OneDrive..."):
            sheets_data[selected_sheet] = edited_df
            
            success = save_all_sheets_to_onedrive(sheets_data)
            if success:
                st.success("✅ Berhasil! File Excel di OneDrive sudah diperbarui.")
                st.rerun()
else:
    st.info("💡 Tidak dapat menampilkan tabel karena gagal terhubung ke file OneDrive di atas.")
