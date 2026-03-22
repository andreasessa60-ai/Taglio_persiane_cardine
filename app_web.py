import streamlit as st
import math
from fpdf import FPDF
from datetime import datetime

# Configurazione stile Smartphone
st.set_page_config(page_title="Taglio Infissi Pro", layout="centered")

def ottimizza_logica(lista_misure, zoc_fin, zoc_port, prof_w):
    BARRA_UTILE = 6440
    LAMA = 5
    p_anta, p_zocc, g_tot = [], [], 0
    
    for m in lista_misure:
        h_t = math.floor(m["H"] - 49)
        l_t = math.floor((m["L"] - (49*2)) if m["ante"]==1 else (m["L"] - (49*2) - 143)/2)
        num_zoccoli = (zoc_fin if m["tipo"] == "Finestra" else zoc_port) * m["ante"]
        
        for i in range(m["ante"]):
            rif = f"{m['tipo']} {int(m['L'])}x{int(m['H'])}"
            p_anta.extend([
                {"m": h_t, "t": "45-90", "d": f"M.DX {rif}"}, 
                {"m": h_t, "t": "90-45", "d": f"M.SX {rif}"}, 
                {"m": l_t, "t": "45-45", "d": f"T.SU {rif}"}
            ])
            g_tot += ((h_t + prof_w) * 2) + (l_t + (prof_w * 2))
            
        for _ in range(num_zoccoli):
            p_zocc.append({"m": l_t, "t": "90-90", "d": f"Zoc. {rif}"})
    
    def fit(lista):
        res = []
        for p in sorted(lista, key=lambda x: x['m'], reverse=True):
            ins = False
            for b in res:
                if (sum(x['m'] for x in b) + (len(b)*LAMA) + p['m']) <= BARRA_UTILE:
                    b.append(p); ins = True; break
            if not ins: res.append([p])
        return res
    
    return fit(p_anta), fit(p_zocc), g_tot

def genera_pdf(barre_a, barre_z, g_tot):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 15, "DISTINTA DI TAGLIO - OFFICINA", 1, 1, 'C')
    
    def stampa(tit, b, r, g, bl):
        if not b: return
        pdf.ln(5); pdf.set_fill_color(r, g, bl); pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, tit, 1, 1, 'L', True)
        for i, barra in enumerate(b, 1):
            pdf.set_font("Arial", 'B', 10); pdf.cell(190, 8, f"BARRA {i}", 1, 1, 'L')
            pdf.set_font("Arial", '', 9)
            for p in barra: pdf.cell(10); pdf.cell(180, 6, f"{p['m']} mm | {p['t']} | {p['d']}", "B", 1)
    
    stampa("PROFILI ANTA", barre_a, 200, 220, 255)
    stampa("PROFILI ZOCCOLO", barre_z, 255, 230, 200)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACCIA STREAMLIT ---
st.title("🪟 Taglio Infissi v2.5")

# 1. PARAMETRI OBBLIGATORI
with st.container():
    st.warning("⚙️ Impostazioni Commessa")
    c1, c2, c3 = st.columns(3)
    z_fin = c1.number_input("Zoccoli Fin.", value=0)
    z_port = c2.number_input("Zoccoli Port.", value=1)
    prof = c3.number_input("Spess. Profilo", value=30)

if 'misure' not in st.session_state: st.session_state.misure = []

# 2. INSERIMENTO (Ottimizzato per dita)
with st.form("input_form", clear_on_submit=True):
    col_l, col_h = st.columns(2)
    l_in = col_l.number_input("Larghezza (mm)", min_value=0, step=1)
    h_in = col_h.number_input("Altezza (mm)", min_value=0, step=1)
    
    col_a, col_t = st.columns(2)
    ante_in = col_a.selectbox("Ante", [1, 2])
    tipo_in = col_t.radio("Tipo", ["Finestra", "Portafinestra"])
    
    submit = st.form_submit_button("➕ AGGIUNGI INFISSO", use_container_width=True)
    if submit and l_in > 0 and h_in > 0:
        st.session_state.misure.append({"L": l_in, "H": h_in, "ante": ante_in, "tipo": tipo_in})

# 3. RIEPILOGO E PDF
if st.session_state.misure:
    st.write("---")
    for idx, m in enumerate(st.session_state.misure):
        st.text(f"#{idx+1}: {m['tipo']} {m['L']}x{m['H']} ({m['ante']} ante)")
    
    if st.button("🗑️ Svuota Lista"):
        st.session_state.misure = []; st.rerun()

    ba, bz, gt = ottimizza_logica(st.session_state.misure, z_fin, z_port, prof)
    
    st.info(f"📊 Barre Anta: {len(ba)} | Barre Zocc: {len(bz)}")
    
    pdf_bytes = genera_pdf(ba, bz, gt)
    st.download_button("📥 SCARICA PDF PER OFFICINA", data=pdf_bytes, 
                       file_name="distinta_taglio.pdf", mime="application/pdf", 
                       use_container_width=True)