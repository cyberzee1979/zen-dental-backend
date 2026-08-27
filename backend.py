from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sqlite3
import os
import shutil
import uvicorn
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# === KONFIGURIMI I LLOGARISË SË ADMINISTRATORIT ===
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Ferizaj2026$" # <--- NDRYSHO KËTË PARA SE TA PUBLIKOSH ONLINE
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- Modelet Pydantic ---
class BookingForm(BaseModel):
    emri: str
    telefoni: str
    mjeku: str
    sherbimi: str
    data_preferuar: str
    koha_preferuar: str

class LoginData(BaseModel):
    username: str
    password: str

class PerfundimForm(BaseModel):
    shenime: str
    cmimi: float = 0.0

class NdryshoShenimeForm(BaseModel):
    shenime: str
    cmimi: float = 0.0

class PasswordForm(BaseModel):
    password: str

class VleresimForm(BaseModel):
    emri: str
    komenti: str
    yje: int

class StatusVleresimiForm(BaseModel):
    status: str

class StatusSmileForm(BaseModel):
    status: str
    mjeku: Optional[str] = None

# Modeli i ri për Shpenzimet
class ShpenzimForm(BaseModel):
    materiali: str
    kompania: str
    cmimi: float
    data: str

def init_db():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rezervimet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emri TEXT,
            telefoni TEXT,
            mjeku TEXT,
            sherbimi TEXT,
            data TEXT,
            ora TEXT,
            status TEXT DEFAULT 'Aktiv',
            shenime TEXT,
            cmimi REAL DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stafi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emri TEXT,
            roli TEXT,
            pershkrimi TEXT,
            foto_url TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS galeria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulli TEXT,
            pershkrimi TEXT,
            foto_para_url TEXT,
            foto_pas_url TEXT,
            data_krijimit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vleresimet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emri TEXT,
            komenti TEXT,
            yje INTEGER,
            status TEXT DEFAULT 'Ne Pritje',
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS smile_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emri TEXT,
            kontakti TEXT,
            problemi TEXT,
            foto_url TEXT,
            status TEXT DEFAULT 'E Re',
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # --- TABELA E RE PËR SHPENZIMET E MATERIALEVE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shpenzimet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materiali TEXT,
            kompania TEXT,
            cmimi REAL,
            data TEXT,
            data_regjistrimit TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE rezervimet ADD COLUMN status TEXT DEFAULT 'Aktiv'")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE rezervimet ADD COLUMN shenime TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE rezervimet ADD COLUMN cmimi REAL DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE stafi ADD COLUMN username TEXT")
        cursor.execute("ALTER TABLE stafi ADD COLUMN password TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE smile_assessments ADD COLUMN shqyrtuar_nga TEXT")
    except sqlite3.OperationalError: pass
        
    cursor.execute("SELECT COUNT(*) FROM stafi")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stafi (emri, roli, pershkrimi, foto_url, username, password) VALUES (?, ?, ?, ?, ?, ?)",
            ("Dr. Agon Gashi", "Kirurg Oral & Implantolog", "Ekspert në kirurgji.", "", "agon", "123"))
        cursor.execute("INSERT INTO stafi (emri, roli, pershkrimi, foto_url, username, password) VALUES (?, ?, ?, ?, ?, ?)",
            ("Dr. Blerta Kelmendi", "Ortodonte & Estetikë", "Eksperte në estetikë.", "", "blerta", "123"))
            
    cursor.execute("SELECT COUNT(*) FROM galeria")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO galeria (titulli, pershkrimi, foto_para_url, foto_pas_url) VALUES (?, ?, ?, ?)",
            ("Faseta E-max (Veneers)", "Ndryshim total i formës dhe ngjyrës me 10 faseta në nofullën e sipërme.", "https://images.unsplash.com/photo-1606811841689-23dfddce3e95?w=500&q=80", "https://images.unsplash.com/photo-1590664095641-7fa05f689813?w=500&q=80"))

    cursor.execute("SELECT COUNT(*) FROM vleresimet")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO vleresimet (emri, komenti, yje, status) VALUES (?, ?, ?, ?)",
            ("Arbër Hoxha", "Shërbim i shkëlqyer dhe ambient shumë relaksues! Doktorët janë shumë profesionistë dhe më hoqën frikën nga dentisti.", 5, "E Aprovuar"))
            
    conn.commit()
    conn.close()

init_db()

# ==========================================
# ENDPOINTET EKZISTUESE (TË PANDRYSHUARA)
# ==========================================

@app.post("/api/login")
def kycja(data: LoginData):
    username_i_paster = data.username.strip().lower()
    
    if username_i_paster == ADMIN_USERNAME.lower() and data.password == ADMIN_PASSWORD:
        return {"status": "success", "role": "admin", "name": "Administrator"}
        
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT emri, password FROM stafi WHERE LOWER(username) = ?", (username_i_paster,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[1] == data.password:
            return {"status": "success", "role": user[0], "name": user[0]}
            
        raise HTTPException(status_code=401, detail="Kredenciale të gabuara")
    except Exception as e:
         raise HTTPException(status_code=500, detail="Gabim në databazë")

@app.post("/api/booking")
def shto_rezervim(form: BookingForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rezervimet (emri, telefoni, mjeku, sherbimi, data, ora) VALUES (?, ?, ?, ?, ?, ?)",
            (form.emri, form.telefoni, form.mjeku, form.sherbimi, form.data_preferuar, form.koha_preferuar)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Rezervimi u ruajt me sukses!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rezervimet/{mjeku_emri}")
def merr_rezervimet(mjeku_emri: str):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        
        if mjeku_emri == "admin" or mjeku_emri == "Çdo Mjek":
            cursor.execute("SELECT id, emri, telefoni, mjeku, sherbimi, data, ora FROM rezervimet WHERE status = 'Aktiv' ORDER BY data ASC, ora ASC")
        else:
            cursor.execute("SELECT id, emri, telefoni, mjeku, sherbimi, data, ora FROM rezervimet WHERE (mjeku = ? OR mjeku = 'Çdo Mjek') AND status = 'Aktiv' ORDER BY data ASC, ora ASC", (mjeku_emri,))
            
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "telefoni": r[2], "mjeku": r[3], "sherbimi": r[4], "data": r[5], "ora": r[6]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rezervimet/{id}/perfunduar")
def perfundo_termin(id: int, form: PerfundimForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rezervimet SET status = 'Perfunduar', shenime = ?, cmimi = ? WHERE id = ?", 
            (form.shenime, form.cmimi, id)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rezervimet/{id}/ndrysho")
def ndrysho_arkiven(id: int, form: NdryshoShenimeForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE rezervimet SET shenime = ?, cmimi = ? WHERE id = ?", (form.shenime, form.cmimi, id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/arkiva/admin")
def merr_arkiven():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, emri, telefoni, mjeku, sherbimi, data, ora, shenime, cmimi FROM rezervimet WHERE status = 'Perfunduar' ORDER BY data DESC, ora DESC")
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "telefoni": r[2], "mjeku": r[3], "sherbimi": r[4], "data": r[5], "ora": r[6], "shenime": r[7], "cmimi": r[8]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historia/{telefoni}")
def merr_historine(telefoni: str):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT mjeku, sherbimi, data, shenime, cmimi FROM rezervimet WHERE telefoni = ? AND status = 'Perfunduar' ORDER BY data DESC", (telefoni,))
        rreshtat = cursor.fetchall()
        rezultati = [{"mjeku": r[0], "sherbimi": r[1], "data": r[2], "shenime": r[3], "cmimi": r[4]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stafi")
def merr_stafin():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, emri, roli, pershkrimi, foto_url, username FROM stafi")
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "roli": r[2], "pershkrimi": r[3], "foto_url": r[4], "username": r[5]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stafi")
async def shto_staf(emri: str = Form(...), roli: str = Form(...), pershkrimi: str = Form(...), username: str = Form(...), password: str = Form(...), file: Optional[UploadFile] = File(None)):
    foto_url = ""
    try:
        if file:
            filename = f"staf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file_path = f"uploads/{filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            foto_url = file_path 
            
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO stafi (emri, roli, pershkrimi, foto_url, username, password) VALUES (?, ?, ?, ?, ?, ?)", 
            (emri, roli, pershkrimi, foto_url, username, password)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Ky username ekziston tashmë! Zgjidhni një tjetër.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/stafi/{id_stafit}")
async def ndrysho_te_dhenat_stafit(
    id_stafit: int,
    emri: str = Form(...),
    roli: str = Form(...),
    pershkrimi: str = Form(...),
    username: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()

        if file:
            filename = f"staf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file_path = f"uploads/{filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            cursor.execute("SELECT foto_url FROM stafi WHERE id = ?", (id_stafit,))
            foto_vjeter = cursor.fetchone()
            if foto_vjeter and foto_vjeter[0] and os.path.exists(foto_vjeter[0]):
                os.remove(foto_vjeter[0])

            cursor.execute(
                "UPDATE stafi SET emri = ?, roli = ?, pershkrimi = ?, username = ?, foto_url = ? WHERE id = ?",
                (emri, roli, pershkrimi, username, file_path, id_stafit)
            )
        else:
            cursor.execute(
                "UPDATE stafi SET emri = ?, roli = ?, pershkrimi = ?, username = ? WHERE id = ?",
                (emri, roli, pershkrimi, username, id_stafit)
            )
        
        conn.commit()
        conn.close()
        return {"status": "success"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Ky username ekziston tashmë! Zgjidhni një tjetër.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/stafi/{id_stafit}/password")
def ndrysho_password(id_stafit: int, form: PasswordForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE stafi SET password = ? WHERE id = ?", (form.password, id_stafit))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/stafi/{id_stafit}")
def fshi_staf(id_stafit: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT foto_url FROM stafi WHERE id = ?", (id_stafit,))
        foto = cursor.fetchone()
        
        if foto and foto[0] and os.path.exists(foto[0]):
            os.remove(foto[0])
            
        cursor.execute("DELETE FROM stafi WHERE id = ?", (id_stafit,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/galeria")
def merr_galerine():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, titulli, pershkrimi, foto_para_url, foto_pas_url FROM galeria ORDER BY data_krijimit DESC")
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "titulli": r[1], "pershkrimi": r[2], "foto_para_url": r[3], "foto_pas_url": r[4]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/galeria")
async def shto_galeri(
    titulli: str = Form(...), 
    pershkrimi: str = Form(...), 
    foto_para: UploadFile = File(...), 
    foto_pas: UploadFile = File(...)
):
    try:
        filename_para = f"galeri_para_{datetime.now().strftime('%Y%m%d%H%M%S')}_{foto_para.filename}"
        path_para = f"uploads/{filename_para}"
        with open(path_para, "wb") as buffer:
            shutil.copyfileobj(foto_para.file, buffer)
            
        filename_pas = f"galeri_pas_{datetime.now().strftime('%Y%m%d%H%M%S')}_{foto_pas.filename}"
        path_pas = f"uploads/{filename_pas}"
        with open(path_pas, "wb") as buffer:
            shutil.copyfileobj(foto_pas.file, buffer)
            
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO galeria (titulli, pershkrimi, foto_para_url, foto_pas_url) VALUES (?, ?, ?, ?)", 
            (titulli, pershkrimi, path_para, path_pas)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/galeria/{id}")
def fshi_galeri(id: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT foto_para_url, foto_pas_url FROM galeria WHERE id = ?", (id,))
        fotot = cursor.fetchone()
        if fotot:
            if fotot[0] and os.path.exists(fotot[0]) and not fotot[0].startswith('http'):
                os.remove(fotot[0])
            if fotot[1] and os.path.exists(fotot[1]) and not fotot[1].startswith('http'):
                os.remove(fotot[1])
        
        cursor.execute("DELETE FROM galeria WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/smile")
async def shto_smile_assessment(emri: str = Form(...), kontakti: str = Form(...), problemi: str = Form(...), file: Optional[UploadFile] = File(None)):
    foto_url = ""
    try:
        if file:
            filename = f"smile_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file_path = f"uploads/{filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            foto_url = file_path
            
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO smile_assessments (emri, kontakti, problemi, foto_url) VALUES (?, ?, ?, ?)",
            (emri, kontakti, problemi, foto_url)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/smile")
def merr_smile_assessments():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, emri, kontakti, problemi, foto_url, status, data, shqyrtuar_nga FROM smile_assessments ORDER BY data DESC")
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "kontakti": r[2], "problemi": r[3], "foto_url": r[4], "status": r[5], "data": r[6], "shqyrtuar_nga": r[7]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/smile/{id}/status")
def ndrysho_status_smile(id: int, form: StatusSmileForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE smile_assessments SET status = ?, shqyrtuar_nga = ? WHERE id = ?", (form.status, form.mjeku, id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/smile/{id}")
def fshi_smile_assessment(id: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT foto_url FROM smile_assessments WHERE id = ?", (id,))
        foto = cursor.fetchone()
        
        if foto and foto[0] and os.path.exists(foto[0]):
            os.remove(foto[0])
            
        cursor.execute("DELETE FROM smile_assessments WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vleresimet")
def shto_vleresim(form: VleresimForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vleresimet (emri, komenti, yje) VALUES (?, ?, ?)",
            (form.emri, form.komenti, form.yje)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vleresimet/aprovuara")
def merr_vleresimet_faqe():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, emri, komenti, yje, data FROM vleresimet WHERE status = 'E Aprovuar' ORDER BY data DESC")
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "komenti": r[2], "yje": r[3], "data": r[4]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vleresimet/admin")
def merr_vleresimet_admin():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, emri, komenti, yje, status, data FROM vleresimet ORDER BY data DESC")
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "komenti": r[2], "yje": r[3], "status": r[4], "data": r[5]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/vleresimet/{id}/status")
def ndrysho_status_vleresimi(id: int, form: StatusVleresimiForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE vleresimet SET status = ? WHERE id = ?", (form.status, id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vleresimet/{id}")
def fshi_vleresim(id: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vleresimet WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# ENDPOINTET E REJA PËR SHPENZIMET & RAPORTET
# ==========================================

@app.post("/api/shpenzimet")
def shto_shpenzim(form: ShpenzimForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO shpenzimet (materiali, kompania, cmimi, data) VALUES (?, ?, ?, ?)",
            (form.materiali, form.kompania, form.cmimi, form.data)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Shpenzimi u regjistrua."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shpenzimet")
def merr_shpenzimet():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, materiali, kompania, cmimi, data FROM shpenzimet ORDER BY data DESC")
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "materiali": r[1], "kompania": r[2], "cmimi": r[3], "data": r[4]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/shpenzimet/{id}")
def fshi_shpenzim(id: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shpenzimet WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/raporti/{muaji_viti}")
def gjenero_raport(muaji_viti: str):
    """
    muaji_viti duhet të jetë në formatin 'YYYY-MM', p.sh. '2026-08'
    """
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        
        # 1. Të Hyrat (Nga rezervimet e përfunduara ku data fillon me YYYY-MM)
        cursor.execute("""
            SELECT SUM(cmimi) FROM rezervimet 
            WHERE status = 'Perfunduar' AND data LIKE ?
        """, (muaji_viti + "%",))
        te_hyrat = cursor.fetchone()[0] or 0.0
        
        # 2. Shpenzimet (Nga materialet ku data fillon me YYYY-MM)
        cursor.execute("""
            SELECT SUM(cmimi) FROM shpenzimet 
            WHERE data LIKE ?
        """, (muaji_viti + "%",))
        shpenzimet = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        fitimi_neto = te_hyrat - shpenzimet
        
        return {
            "muaji": muaji_viti,
            "te_hyrat_pacientet": te_hyrat,
            "shpenzimet_materiale": shpenzimet,
            "fitimi_neto": fitimi_neto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Serveri po ndizet në [https://zen-dental-backend.onrender.com](https://zen-dental-backend.onrender.com)")
    uvicorn.run(app, host="0.0.0.0", port=8000)