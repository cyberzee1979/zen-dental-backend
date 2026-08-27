import streamlit as st
import sqlite3
from datetime import datetime
import os

# 1. Konfigurimi i faqes
st.set_page_config(
    page_title="Zen Dental Clinic",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Lidhja me Bazën e Të Dhënave (SQLite)
def init_db():
    conn = sqlite3.connect('klinika_zen.db')
    c = conn.cursor()
    # Tabela e rezervimeve
    c.execute('''
        CREATE TABLE IF NOT EXISTS rezervimet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emri TEXT,
            telefoni TEXT,
            sherbimi TEXT,
            data TEXT,
            ora TEXT,
            krijuar_me TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Tabela e vlerësimeve të buzëqeshjes (Smile Assessment)
    c.execute('''
        CREATE TABLE IF NOT EXISTS smile_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emri TEXT,
            email TEXT,
            qellimi TEXT,
            foto_emri TEXT,
            krijuar_me TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 3. Custom CSS për Stilin "Zen" (Minimalist, pastel, elegant)
st.markdown("""
    <style>
    /* Prapavija kryesore dhe ngjyrat */
    .stApp {
        background-color: #FAF7F2; /* Bezhë e ngrohtë Zen */
        color: #2C3E35; /* Ngjyrë e erët natyrale */
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Titujt me stil minimalist */
    h1, h2, h3 {
        color: #1A2E26 !important;
        font-weight: 300 !important;
        letter-spacing: -0.5px;
    }
    
    /* Containerët me hije të lehtë dhe qoshe të rrumbullakosura */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
    }

    /* Stilizimi i butonave */
    .stButton>button {
        background-color: #3B5249 !important;
        color: #FFFFFF !important;
        border-radius: 25px !important;
        border: none !important;
        padding: 10px 25px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #2C3E35 !important;
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# 4. Paneli Anësor (Sidebar) - Për Navigim & Login të Adminit
st.sidebar.title("🌿 Zen Dental")
menyja = st.sidebar.radio("Navigimi", ["Faqja Kryesore", "Smile Assessment", "Rezervo Termin", "Paneli i Mjekut (Admin)"])

# --- FAQJA KRYESORE (HERO SECTION) ---
if menyja == "Faqja Kryesore":
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown("<h1 style='font-size: 3rem;'>Përjetoni kujdesin dentar pa stres.</h1>", unsafe_allow_html=True)
        st.markdown("""
        <p style='font-size: 1.2rem; color: #556B2F;'>
        Mirësevini në Zen Dental. Ne kombinojmë teknologjinë më moderne digjitale me një ambient qetësues 
        për t'ju ofruar një përvojë plotësisht ndryshe nga ajo që jeni mësuar.
        </p>
        """, unsafe_allow_html=True)
        
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            st.info("✨ **Kujdes i Personalizuar**\nSkandim 3D digjital pa dhimbje.")
        with c2:
            st.success("🌿 **Ambient Relaksues**\nInspiruar nga konceptet SPA.")

    with col2:
        st.image("https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&q=80&w=800", caption="Zen Dental Ambienti")

    st.divider()
    
    # Seksioni i Shërbimeve Interaktive
    st.subheader("Shërbimet tona kryesore")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("### 🦷 Stomatologji Estetike")
        st.write("Fasetat (Veneers) dhe zbardhim profesional i dhëmbëve me teknologji laserik.")
    with s2:
        st.markdown("### 🔍 Invisalign & Drejtim")
        st.write("Drejtimi i dhëmbëve me drejtues transparentë dhe padukshëm.")
    with s3:
        st.markdown("### 🛡️ Implante Digjitale")
        st.write("Planifikim kompjuterik 3D për implante me saktësi maksimale.")

# --- SMILE ASSESSMENT (VLERËSIMI I BUZËQESHJES) ---
elif menyja == "Smile Assessment":
    st.title("✨ Vlerësimi Digjital i Buzëqeshjes")
    st.write("Plotësoni formën e mëposhtme dhe ngarkoni një foto për një konsulencë paraprake nga mjekët tanë.")
    
    with st.form("smile_form", clear_on_submit=True):
        emri = st.text_input("Emri dhe Mbiemri")
        email = st.text_input("Email ose Numri i Telefonit")
        
        qellimi = st.multiselect(
            "Çfarë dëshironi të përmirësoni te buzëqeshja juaj?",
            ["Drejtimin e dhëmbëve", "Zbardhimin / Shkëlqimin", "Zëvendësimin e dhëmbëve të munguar", "Formën dhe madhësinë (Veneers)", "Pastrim general / Kontrollë"]
        )
        
        foto = st.file_uploader("Ngarkoni një foto të buzëqeshjes (opsionale)", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Dërgo për Vlerësim")
        
        if submitted:
            if emri and email:
                foto_emri = ""
                if foto is not None:
                    # Ruajtja e fotos në folderin 'uploads'
                    if not os.path.exists('uploads'):
                        os.makedirs('uploads')
                    foto_emri = f"uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto.name}"
                    with open(foto_emri, "wb") as f:
                        f.write(foto.getbuffer())
                
                # Ruajtja në DB
                conn = sqlite3.connect('klinika_zen.db')
                c = conn.cursor()
                c.execute("INSERT INTO smile_assessments (emri, email, qellimi, foto_emri) VALUES (?, ?, ?, ?)",
                          (emri, email, ", ".join(qellimi), foto_emri))
                conn.commit()
                conn.close()
                
                st.balloons()
                st.success("Faleminderit! Kërkesa juaj u dërgua me sukses. Stafi ynë do t'ju kontaktojë brenda 24 orëve.")
            else:
                st.error("Ju lutemi plotësoni emrin dhe kontaktin.")

# --- REZERVO TERMIN ---
elif menyja == "Rezervo Termin":
    st.title("📅 Rezervo Terminin Tënd Online")
    st.write("Zgjidhni shërbimin dhe orarin që ju përshtatet më së miri.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        emri = st.text_input("Emri dhe Mbiemri*")
        telefoni = st.text_input("Numri i Telefonit*")
        sherbimi = st.selectbox("Zgjidhni Shërbimin", [
            "Kontrollë Rutinë & Pastrim", 
            "Konsulencë Estetike (Veneers/Zbardhim)", 
            "Konsulencë Invisalign", 
            "Implantologji", 
            "Urgjencë / Dhimbje Dhëmbi"
        ])

    with col2:
        data = st.date_input("Zgjidhni Datën")
        ora = st.selectbox("Zgjidhni Orarin e Lirë", [
            "09:00 - 10:00", 
            "10:30 - 11:30", 
            "13:00 - 14:00", 
            "15:00 - 16:00", 
            "17:00 - 18:00"
        ])
        
    st.write("")
    if st.button("Konfirmo Rezervimin"):
        if emri and telefoni:
            conn = sqlite3.connect('klinika_zen.db')
            c = conn.cursor()
            c.execute("INSERT INTO rezervimet (emri, telefoni, sherbimi, data, ora) VALUES (?, ?, ?, ?, ?)",
                      (emri, telefoni, sherbimi, str(data), ora))
            conn.commit()
            conn.close()
            
            st.success(f"U krye! Termini juaj u rezervua më **{data}** në orën **{ora}**.")
        else:
            st.warning("Ju lutemi plotësoni fushate obligative (Emrin dhe Telefonin).")

# --- PANELI I MJEKUT (ADMIN) ---
elif menyja == "Paneli i Mjekut (Admin)":
    st.title("🔒 Paneli i Administrimit")
    
    fjalekalimi = st.text_input("Vendosni fjalëkalimin e stafit", type="password")
    
    if fjalekalimi == "zen123":  # Fjalëkalimi shembull
        st.success("Aksesi u leua!")
        
        tab1, tab2 = st.tabs(["📅 Terminet e Rezervuara", "✨ Smile Assessments"])
        
        conn = sqlite3.connect('klinika_zen.db')
        c = conn.cursor()
        
        with tab1:
            st.subheader("Rezervimet nga Uebsajti")
            c.execute("SELECT id, emri, telefoni, sherbimi, data, ora, krijuar_me FROM rezervimet ORDER BY id DESC")
            rezervimet = c.fetchall()
            if rezervimet:
                st.dataframe(
                    rezervimet, 
                    column_config={"0": "ID", "1": "Emri", "2": "Telefoni", "3": "Shërbimi", "4": "Data", "5": "Ora", "6": "Regjistruar më"}
                )
            else:
                st.info("Nuk ka asnjë rezervim ende.")
                
        with tab2:
            st.subheader("Kërkesat për Smile Assessment")
            c.execute("SELECT emri, email, qellimi, foto_emri, krijuar_me FROM smile_assessments ORDER BY id DESC")
            assessments = c.fetchall()
            
            for item in assessments:
                st.markdown(f"**Pacienti:** {item[0]} ({item[1]})")
                st.markdown(f"**Qëllimi:** {item[2]}")
                if item[3] and os.path.exists(item[3]):
                    st.image(item[3], width=250)
                st.caption(f"Dërguar më: {item[4]}")
                st.divider()
                
        conn.close()
    elif fjalekalimi != "":
        st.error("Fjalëkalimi i gabuar!")