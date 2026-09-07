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
ADMIN_PASSWORD = "Demo2026" 
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
    numri_personal: str = ""

class LoginData(BaseModel):
    username: str
    password: str

class PerfundimForm(BaseModel):
    shenime: str
    cmimi: float = 0.0
    numri_personal: str = ""

class NdryshoShenimeForm(BaseModel):
    shenime: str
    cmimi: float = 0.0
    numri_personal: str = ""

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

class ShpenzimForm(BaseModel):
    materiali: str
    kompania: str
    cmimi: float
    data: str

class KontrataKesteForm(BaseModel):
    emri: str
    telefoni: str
    numri_personal: str
    mjeku: str
    sherbimi: str
    shuma_totale: float
    data_fillimit: str

class KestForm(BaseModel):
    shuma: float
    data: str

def init_db():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS rezervimet (id INTEGER PRIMARY KEY AUTOINCREMENT, emri TEXT, telefoni TEXT, mjeku TEXT, sherbimi TEXT, data TEXT, ora TEXT, status TEXT DEFAULT 'Aktiv', shenime TEXT, cmimi REAL DEFAULT 0, numri_personal TEXT DEFAULT '')""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS stafi (id INTEGER PRIMARY KEY AUTOINCREMENT, emri TEXT, roli TEXT, pershkrimi TEXT, foto_url TEXT, username TEXT UNIQUE, password TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS galeria (id INTEGER PRIMARY KEY AUTOINCREMENT, titulli TEXT, pershkrimi TEXT, foto_para_url TEXT, foto_pas_url TEXT, data_krijimit TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS vleresimet (id INTEGER PRIMARY KEY AUTOINCREMENT, emri TEXT, komenti TEXT, yje INTEGER, status TEXT DEFAULT 'Ne Pritje', data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS smile_assessments (id INTEGER PRIMARY KEY AUTOINCREMENT, emri TEXT, kontakti TEXT, problemi TEXT, foto_url TEXT, status TEXT DEFAULT 'E Re', shqyrtuar_nga TEXT, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS shpenzimet (id INTEGER PRIMARY KEY AUTOINCREMENT, materiali TEXT, kompania TEXT, cmimi REAL, data TEXT, data_regjistrimit TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS kontratat_keste (id INTEGER PRIMARY KEY AUTOINCREMENT, emri TEXT, telefoni TEXT, numri_personal TEXT, mjeku TEXT, sherbimi TEXT, shuma_totale REAL, data_fillimit TEXT, statusi TEXT DEFAULT 'Aktiv')""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS kestet (id INTEGER PRIMARY KEY AUTOINCREMENT, kontrata_id INTEGER, shuma REAL, data TEXT, data_regjistrimit TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (kontrata_id) REFERENCES kontratat_keste(id))""")
    
    # Migrimet
    try: cursor.execute("ALTER TABLE rezervimet ADD COLUMN status TEXT DEFAULT 'Aktiv'")
    except: pass
    try: cursor.execute("ALTER TABLE rezervimet ADD COLUMN shenime TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE rezervimet ADD COLUMN cmimi REAL DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE rezervimet ADD COLUMN numri_personal TEXT DEFAULT ''")
    except: pass
    try: cursor.execute("ALTER TABLE stafi ADD COLUMN username TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE stafi ADD COLUMN password TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE smile_assessments ADD COLUMN shqyrtuar_nga TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE kestet ADD COLUMN kontrata_id INTEGER")
    except: pass
        
    cursor.execute("SELECT COUNT(*) FROM stafi")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stafi (emri, roli, pershkrimi, foto_url, username, password) VALUES (?, ?, ?, ?, ?, ?)", ("Dr. Agon Gashi", "Kirurg Oral & Implantolog", "Ekspert në kirurgji.", "", "agon", "123"))
    conn.commit()
    conn.close()

init_db()

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
    except Exception as e: raise HTTPException(status_code=500, detail="Gabim në databazë")

@app.post("/api/booking")
def shto_rezervim(form: BookingForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rezervimet (emri, telefoni, mjeku, sherbimi, data, ora, numri_personal) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (form.emri, form.telefoni, form.mjeku, form.sherbimi, form.data_preferuar, form.koha_preferuar, form.numri_personal))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rezervimet/{mjeku_emri}")
def merr_rezervimet(mjeku_emri: str):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        if mjeku_emri == "admin" or mjeku_emri == "Çdo Mjek":
            cursor.execute("SELECT id, emri, telefoni, mjeku, sherbimi, data, ora, numri_personal FROM rezervimet WHERE status = 'Aktiv' ORDER BY data ASC, ora ASC")
        else:
            cursor.execute("SELECT id, emri, telefoni, mjeku, sherbimi, data, ora, numri_personal FROM rezervimet WHERE (mjeku = ? OR mjeku = 'Çdo Mjek') AND status = 'Aktiv' ORDER BY data ASC, ora ASC", (mjeku_emri,))
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "telefoni": r[2], "mjeku": r[3], "sherbimi": r[4], "data": r[5], "ora": r[6], "numri_personal": r[7]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rezervimet/{id}/perfunduar")
def perfundo_termin(id: int, form: PerfundimForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE rezervimet SET status = 'Perfunduar', shenime = ?, cmimi = ?, numri_personal = ? WHERE id = ?", (form.shenime, form.cmimi, form.numri_personal, id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rezervimet/{id}/ndrysho")
def ndrysho_arkiven(id: int, form: NdryshoShenimeForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE rezervimet SET shenime = ?, cmimi = ?, numri_personal = ? WHERE id = ?", (form.shenime, form.cmimi, form.numri_personal, id))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/arkiva/admin")
def merr_arkiven():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(id) as last_id, MAX(emri) as emri, telefoni, MAX(mjeku) as mjeku, MAX(sherbimi) as sherbimi, MAX(data) as data_fundit, MAX(ora) as ora, MAX(shenime) as shenime, SUM(cmimi) as totali_paguar, COUNT(id) as numri_vizitave, MAX(numri_personal) as numri_personal
            FROM rezervimet WHERE status = 'Perfunduar' 
            GROUP BY CASE WHEN numri_personal IS NOT NULL AND TRIM(numri_personal) != '' THEN numri_personal ELSE telefoni END
            ORDER BY data_fundit DESC, ora DESC
        """)
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "emri": r[1], "telefoni": r[2], "mjeku": r[3], "sherbimi": r[4], "data_fundit": r[5], "ora": r[6], "shenime": r[7], "totali_paguar": r[8], "vizita": r[9], "numri_personal": r[10]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historia/{identifikuesi}")
def merr_historine(identifikuesi: str):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, mjeku, sherbimi, data, shenime, cmimi, numri_personal FROM rezervimet WHERE (numri_personal = ? OR telefoni = ?) AND status = 'Perfunduar' ORDER BY data DESC", (identifikuesi, identifikuesi))
        rreshtat = cursor.fetchall()
        rezultati = [{"id": r[0], "mjeku": r[1], "sherbimi": r[2], "data": r[3], "shenime": r[4], "cmimi": r[5], "numri_personal": r[6]} for r in rreshtat]
        conn.close()
        return rezultati
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/kontratat_keste")
def shto_kontrate_keste(form: KontrataKesteForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO kontratat_keste (emri, telefoni, numri_personal, mjeku, sherbimi, shuma_totale, data_fillimit) VALUES (?, ?, ?, ?, ?, ?, ?)", (form.emri, form.telefoni, form.numri_personal, form.mjeku, form.sherbimi, form.shuma_totale, form.data_fillimit))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kontratat_keste")
def merr_kontratat_keste():
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT k.id, k.emri, k.telefoni, k.numri_personal, k.mjeku, k.sherbimi, k.shuma_totale, k.data_fillimit, COALESCE((SELECT SUM(shuma) FROM kestet WHERE kontrata_id = k.id), 0) as shuma_paguar FROM kontratat_keste k ORDER BY k.data_fillimit DESC")
        rezultati = [{"id": r[0], "emri": r[1], "telefoni": r[2], "numri_personal": r[3], "mjeku": r[4], "sherbimi": r[5], "shuma_totale": r[6], "data_fillimit": r[7], "shuma_paguar": r[8], "shuma_mbetur": r[6]-r[8]} for r in cursor.fetchall()]
        conn.close()
        return rezultati
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/kontratat_keste/{kontrata_id}/kestet")
def shto_kest(kontrata_id: int, form: KestForm):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO kestet (kontrata_id, shuma, data) VALUES (?, ?, ?)", (kontrata_id, form.shuma, form.data))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kontratat_keste/{kontrata_id}/kestet")
def merr_kestet(kontrata_id: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, shuma, data FROM kestet WHERE kontrata_id = ? ORDER BY data DESC, id DESC", (kontrata_id,))
        kestet = [{"id": r[0], "shuma": r[1], "data": r[2]} for r in cursor.fetchall()]
        conn.close()
        return kestet
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/kestet/{id}")
def fshi_kest(id: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM kestet WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shpenzimet")
def shto_shpenzim(form: ShpenzimForm):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO shpenzimet (materiali, kompania, cmimi, data) VALUES (?, ?, ?, ?)", (form.materiali, form.kompania, form.cmimi, form.data))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/shpenzimet")
def merr_shpenzimet():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, materiali, kompania, cmimi, data FROM shpenzimet ORDER BY data DESC")
    rez = [{"id": r[0], "materiali": r[1], "kompania": r[2], "cmimi": r[3], "data": r[4]} for r in cursor.fetchall()]
    conn.close()
    return rez

@app.delete("/api/shpenzimet/{id}")
def fshi_shpenzim(id: int):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shpenzimet WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/raporti/{viti_muaji}")
def gjenero_raport(viti_muaji: str):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        kerkim_data = viti_muaji + "%"

        cursor.execute("SELECT SUM(cmimi) FROM rezervimet WHERE status = 'Perfunduar' AND data LIKE ?", (kerkim_data,))
        te_hyrat_vizitat = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT data, emri, mjeku, cmimi, numri_personal FROM rezervimet WHERE status = 'Perfunduar' AND data LIKE ? ORDER BY data DESC", (kerkim_data,))
        vizitat_lista = [{"data": r[0], "emri": r[1], "mjeku": r[2], "cmimi": r[3], "numri_personal": r[4]} for r in cursor.fetchall()]
        
        cursor.execute("SELECT SUM(cmimi) FROM shpenzimet WHERE data LIKE ?", (kerkim_data,))
        shpenzimet = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT SUM(shuma) FROM kestet WHERE data LIKE ?", (kerkim_data,))
        te_hyrat_kestet = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT k.data, kon.emri, k.shuma, kon.numri_personal, kon.mjeku FROM kestet k JOIN kontratat_keste kon ON k.kontrata_id = kon.id WHERE k.data LIKE ? ORDER BY k.data DESC", (kerkim_data,))
        kestet_lista = [{"data": r[0], "emri": r[1], "shuma": r[2], "numri_personal": r[3], "mjeku": r[4]} for r in cursor.fetchall()]

        conn.close()
        return {
            "te_hyrat_pacientet": te_hyrat_vizitat,
            "vizitat_lista": vizitat_lista,
            "shpenzimet_materiale": shpenzimet,
            "te_hyrat_kestet": te_hyrat_kestet,
            "kestet_lista": kestet_lista,
            "fitimi_neto": te_hyrat_vizitat - shpenzimet
        }
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stafi")
def merr_stafin():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, emri, roli, pershkrimi, foto_url, username FROM stafi")
    rez = [{"id": r[0], "emri": r[1], "roli": r[2], "pershkrimi": r[3], "foto_url": r[4], "username": r[5]} for r in cursor.fetchall()]
    conn.close()
    return rez

@app.post("/api/stafi")
async def shto_staf(emri: str = Form(...), roli: str = Form(...), pershkrimi: str = Form(...), username: str = Form(...), password: str = Form(...), file: Optional[UploadFile] = File(None)):
    foto_url = ""
    if file:
        file_path = f"uploads/staf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        foto_url = file_path 
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO stafi (emri, roli, pershkrimi, foto_url, username, password) VALUES (?, ?, ?, ?, ?, ?)", (emri, roli, pershkrimi, foto_url, username, password))
        conn.commit()
    except sqlite3.IntegrityError: raise HTTPException(status_code=400, detail="Ky username ekziston tashmë!")
    finally: conn.close()
    return {"status": "success"}

@app.put("/api/stafi/{id_stafit}")
async def ndrysho_te_dhenat_stafit(id_stafit: int, emri: str = Form(...), roli: str = Form(...), pershkrimi: str = Form(...), username: str = Form(...), file: Optional[UploadFile] = File(None)):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    if file:
        file_path = f"uploads/staf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        cursor.execute("UPDATE stafi SET emri = ?, roli = ?, pershkrimi = ?, username = ?, foto_url = ? WHERE id = ?", (emri, roli, pershkrimi, username, file_path, id_stafit))
    else:
        cursor.execute("UPDATE stafi SET emri = ?, roli = ?, pershkrimi = ?, username = ? WHERE id = ?", (emri, roli, pershkrimi, username, id_stafit))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.put("/api/stafi/{id_stafit}/password")
def ndrysho_password(id_stafit: int, form: PasswordForm):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE stafi SET password = ? WHERE id = ?", (form.password, id_stafit))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/stafi/{id_stafit}")
def fshi_staf(id_stafit: int):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stafi WHERE id = ?", (id_stafit,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/galeria")
def merr_galerine():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulli, pershkrimi, foto_para_url, foto_pas_url FROM galeria ORDER BY data_krijimit DESC")
    rez = [{"id": r[0], "titulli": r[1], "pershkrimi": r[2], "foto_para_url": r[3], "foto_pas_url": r[4]} for r in cursor.fetchall()]
    conn.close()
    return rez

@app.post("/api/galeria")
async def shto_galeri(titulli: str = Form(...), pershkrimi: str = Form(...), foto_para: UploadFile = File(...), foto_pas: UploadFile = File(...)):
    path_para = f"uploads/galeri_para_{datetime.now().strftime('%Y%m%d%H%M%S')}_{foto_para.filename}"
    with open(path_para, "wb") as buffer: shutil.copyfileobj(foto_para.file, buffer)
    path_pas = f"uploads/galeri_pas_{datetime.now().strftime('%Y%m%d%H%M%S')}_{foto_pas.filename}"
    with open(path_pas, "wb") as buffer: shutil.copyfileobj(foto_pas.file, buffer)
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO galeria (titulli, pershkrimi, foto_para_url, foto_pas_url) VALUES (?, ?, ?, ?)", (titulli, pershkrimi, path_para, path_pas))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/galeria/{id}")
def fshi_galeri(id: int):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM galeria WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/smile")
async def shto_smile_assessment(emri: str = Form(...), kontakti: str = Form(...), problemi: str = Form(...), file: Optional[UploadFile] = File(None)):
    foto_url = ""
    if file:
        file_path = f"uploads/smile_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        foto_url = file_path
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO smile_assessments (emri, kontakti, problemi, foto_url) VALUES (?, ?, ?, ?)", (emri, kontakti, problemi, foto_url))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/smile")
def merr_smile_assessments():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, emri, kontakti, problemi, foto_url, status, data, shqyrtuar_nga FROM smile_assessments ORDER BY data DESC")
    rez = [{"id": r[0], "emri": r[1], "kontakti": r[2], "problemi": r[3], "foto_url": r[4], "status": r[5], "data": r[6], "shqyrtuar_nga": r[7]} for r in cursor.fetchall()]
    conn.close()
    return rez

@app.put("/api/smile/{id}/status")
def ndrysho_status_smile(id: int, form: StatusSmileForm):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE smile_assessments SET status = ?, shqyrtuar_nga = ? WHERE id = ?", (form.status, form.mjeku, id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/smile/{id}")
def fshi_smile_assessment(id: int):
    try:
        conn = sqlite3.connect("databaza_klinikes.db")
        cursor = conn.cursor()
        
        # Gjej foton qe ta fshijme fizikisht
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
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vleresimet (emri, komenti, yje) VALUES (?, ?, ?)", (form.emri, form.komenti, form.yje))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/vleresimet/aprovuara")
def merr_vleresimet_faqe():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, emri, komenti, yje, data FROM vleresimet WHERE status = 'E Aprovuar' ORDER BY data DESC")
    rez = [{"id": r[0], "emri": r[1], "komenti": r[2], "yje": r[3], "data": r[4]} for r in cursor.fetchall()]
    conn.close()
    return rez

@app.get("/api/vleresimet/admin")
def merr_vleresimet_admin():
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, emri, komenti, yje, status, data FROM vleresimet ORDER BY data DESC")
    rez = [{"id": r[0], "emri": r[1], "komenti": r[2], "yje": r[3], "status": r[4], "data": r[5]} for r in cursor.fetchall()]
    conn.close()
    return rez

@app.put("/api/vleresimet/{id}/status")
def ndrysho_status_vleresimi(id: int, form: StatusVleresimiForm):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE vleresimet SET status = ? WHERE id = ?", (form.status, id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/vleresimet/{id}")
def fshi_vleresim(id: int):
    conn = sqlite3.connect("databaza_klinikes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vleresimet WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    print("🚀 Serveri po ndizet në https://zen-dental-backend.onrender.com")
    uvicorn.run(app, host="0.0.0.0", port=8000)