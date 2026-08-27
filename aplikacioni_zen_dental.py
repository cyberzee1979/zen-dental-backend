import streamlit as st
import sqlite3
from datetime import datetime
import os

# ==========================================
# 1. KONFIGURIMI KRYESOR (MAIN LAYOUT)
# ==========================================
# Ky konfigurim shkruhet vetëm KËTU dhe aplikohet në të gjitha faqet!
st.set_page_config(
    page_title="Zen Dental Clinic",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializimi i Databazës
def init_db():
    conn = sqlite3.connect('klinika_zen.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rezervimet 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, emri TEXT, telefoni TEXT, sherbimi TEXT, data TEXT, ora TEXT, krijuar_me TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS smile_assessments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, emri TEXT, email TEXT, qellimi TEXT, foto_emri TEXT, krijuar_me TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# CSS Global (Aplikohet automatikisht kudo, pa e përsëritur)
st.markdown("""
    <style>
    .stApp {
        background-color: #FAF7F2; /* Ngjyra Zen Bezhë */
        color: #2C3E35;
    }
    h1, h2, h3 { color: #1A2E26 !important; font-weight: 300 !important; }
    div[data-testid="stVerticalBlock"] > div {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
    }
    .stButton>button {
        background-color: #3B5249 !important; color: #FFFFFF !important;
        border-radius: 25px !important; border: none !important;
        padding: 10px 25px !important; transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #2C3E35 !important; transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. DEFINIMI I FAQEVE (VIEWS)
# ==========================================

def faqja_kryesore():
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown("<h1 style='font-size: 3rem;'>Kujdes dentar pa stres.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.2rem; color: #556B2F;'>Kombinojmë teknologjinë moderne me një ambient qetësues.</p>", unsafe_allow_html=True)
        
        st.write("")
        c1, c2 = st.columns(2)
        with c1: st.info("✨ **Skanim 3D pa dhimbje.**")
        with c2: st.success("🌿 **Ambient Relaksues (SPA).**")

    with col2:
        st.image("https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&q=80&w=800", caption="Zen Dental Ambienti", use_container_width=True)

    st.divider()
    st.subheader("Shërbimet tona kryesore")
    s1, s2, s3 = st.columns(3)
    s1.markdown("### 🦷 Estetikë\nFasetat dhe zbardhim profesional.")
    s2.markdown("### 🔍 Invisalign\nDrejtim transparent i padukshëm.")
    s3.markdown("### 🛡️ Implante 3D\nPlanifikim kompjuterik me saktësi.")


def smile_assessment():
    st.title("✨ Vlerësimi Digjital i Buzëqeshjes")
    st.write("Ngarkoni një foto për një konsulencë paraprake nga mjekët tanë.")
    
    with st.form("smile_form", clear_on_submit=True):
        emri = st.text_input("Emri dhe Mbiemri")
        email = st.text_input("Email ose Numri i Telefonit")
        qellimi = st.multiselect("Çfarë dëshironi të përmirësoni?", ["Drejtim", "Zbardhim", "Zëvendësim", "Veneers"])
        foto = st.file_uploader("Ngarkoni foton (opsionale)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Dërgo për Vlerësim"):
            if emri and email:
                foto_emri = ""
                if foto:
                    if not os.path.exists('uploads'): os.makedirs('uploads')
                    foto_emri = f"uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto.name}"
                    with open(foto_emri, "wb") as f: f.write(foto.getbuffer())
                
                conn = sqlite3.connect('klinika_zen.db')
                conn.cursor().execute("INSERT INTO smile_assessments (emri, email, qellimi, foto_emri) VALUES (?, ?, ?, ?)",
                          (emri, email, ", ".join(qellimi), foto_emri))
                conn.commit()
                conn.close()
                st.success("Kërkesa u dërgua! Stafi do t'ju kontaktojë së shpejti.")
            else:
                st.error("Plotësoni emrin dhe kontaktin.")


def rezervo_termin():
    st.title("📅 Rezervo Terminin Tënd Online")
    col1, col2 = st.columns(2)
    
    with col1:
        emri = st.text_input("Emri dhe Mbiemri*")
        telefoni = st.text_input("Numri i Telefonit*")
        sherbimi = st.selectbox("Shërbimi", ["Kontrollë", "Konsulencë Estetike", "Invisalign", "Urgjencë"])

    with col2:
        data = st.date_input("Data")
        ora = st.selectbox("Orari", ["09:00 - 10:00", "10:30 - 11:30", "13:00 - 14:00", "15:00 - 16:00"])
        
    if st.button("Konfirmo Rezervimin"):
        if emri and telefoni:
            conn = sqlite3.connect('klinika_zen.db')
            conn.cursor().execute("INSERT INTO rezervimet (emri, telefoni, sherbimi, data, ora) VALUES (?, ?, ?, ?, ?)",
                      (emri, telefoni, sherbimi, str(data), ora))
            conn.commit()
            conn.close()
            st.success(f"Termini u rezervua më **{data}** në **{ora}**.")
        else:
            st.warning("Plotësoni Emrin dhe Telefonin.")


def paneli_admin():
    st.title("🔒 Paneli i Administrimit")
    if st.text_input("Fjalëkalimi", type="password") == "zen123":
        tab1, tab2 = st.tabs(["📅 Terminet", "✨ Assessments"])
        conn = sqlite3.connect('klinika_zen.db')
        
        with tab1:
            st.subheader("Rezervimet e reja")
            rez = conn.cursor().execute("SELECT emri, telefoni, sherbimi, data, ora FROM rezervimet ORDER BY id DESC").fetchall()
            if rez: st.dataframe(rez, column_config={"0":"Emri", "1":"Tel", "2":"Shërbimi", "3":"Data", "4":"Ora"})
                
        with tab2:
            st.subheader("Fotot e ngarkuara")
            ass = conn.cursor().execute("SELECT emri, email, qellimi, foto_emri FROM smile_assessments ORDER BY id DESC").fetchall()
            for item in ass:
                st.write(f"**{item[0]}** | {item[2]}")
                if item[3] and os.path.exists(item[3]): st.image(item[3], width=200)
                st.divider()
        conn.close()


# ==========================================
# 3. KRIJIMI I NAVIGIMIT KRYESOR
# ==========================================
st.sidebar.title("🌿 Zen Dental")
st.sidebar.markdown("Mirësevini! Zgjidhni një opsion:")

# Regjistrimi i faqeve si objekte navigimi
page_home = st.Page(faqja_kryesore, title="Faqja Kryesore", icon="🏠", default=True)
page_smile = st.Page(smile_assessment, title="Vlerëso Buzëqeshjen", icon="✨")
page_rezervo = st.Page(rezervo_termin, title="Rezervo Termin", icon="📅")
page_admin = st.Page(paneli_admin, title="Paneli i Mjekut", icon="🔒")

# Krijimi i menysë me kategori
pg = st.navigation({
    "Për Pacientët": [page_home, page_smile, page_rezervo],
    "Stafi i Klinikës": [page_admin]
})

# Ekzekutimi i faqes së zgjedhur
pg.run()