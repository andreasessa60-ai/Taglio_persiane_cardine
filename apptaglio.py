import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64

# Configurazione Pagina
st.set_page_config(page_title="Ottimizzatore Taglio 6500", layout="centered")

def calcola_ottimizzazione(pezzi_input, spessore_p, lama, barra_totale, sfrido_fisso):
    barra_utile = barra_totale - sfrido_fisso
    pezzi_totali = []
    
    for p in pezzi_input:
        m_reale = p['m_int'] + (spessore_p if p['sx'] == '45°' else 0) + (spessore_p if p['dx'] == '45°' else 0)
        for _ in range(p['qta']):
            pezzi_totali.append({'int': p['m_int'], 'reale': m_reale, 'tagli': f"{p['sx']}/{p['dx']}"})
    
    pezzi_totali.sort(key=lambda x: x['reale'], reverse=True)
    barre = []
    
    for p in pezzi_totali:
        if p['reale'] > barra_utile:
            continue
        inserito = False
        for b in barre:
            usato = sum(item['reale'] for item in b) + (len(b) * lama)
            if usato + p['reale'] + lama <= barra_utile:
                b.append(p)
                inserito = True
                break
        if not inserito:
            barre.append([p])
    return barre

# --- INTERFACCIA STREAMLIT ---
st.title("🪟 Ottimizzatore Taglio V3")
st.markdown("### Configurazione Barra")

col1, col2 = st.columns(2)
with col1:
    sp_profilo = st.number_input("Spessore Profilo (mm)", value=50)
with col2:
    sp_lama = st.number_input("Spessore Lama (mm)", value=8)

st.divider()
st.markdown("### Inserimento Misure")

# Tabella dinamica per input
if 'rows' not in st.session_state:
    st.session_state.rows = [{'m_int': 0.0, 'qta': 1, 'sx': '90°', 'dx': '90°'}]

def aggiungi_riga():
    st.session_state.rows.append({'m_int': 0.0, 'qta': 1, 'sx': '90°', 'dx': '90°'})

for i, row in enumerate(st.session_state.rows):
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    st.session_state.rows[i]['m_int'] = c1.number_input(f"Misura Int (mm)", key=f"m_{i}", value=row['m_int'])
    st.session_state.rows[i]['qta'] = c2.number_input(f"Q.tà", key=f"q_{i}", value=row['qta'], min_value=1)
    st.session_state.rows[i]['sx'] = c3.selectbox(f"Taglio SX", ["90°", "45°"], key=f"sx_{i}")
    st.session_state.rows[i]['dx'] = c4.selectbox(f"Taglio DX", ["90°", "45°"], key=f"dx_{i}")

st.button("➕ Aggiungi Riga", on_click=aggiungi_riga)

if st.button("🚀 CALCOLA OTTIMIZZAZIONE", type="primary"):
    risultati = calcola_ottimizzazione(st.session_state.rows, sp_profilo, sp_lama, 6500, 60)
    
    st.success(f"Totale barre necessarie: {len(risultati)}")
    
    for idx, b in enumerate(risultati):
        somma_reale = sum(p['reale'] for p in b) + (len(b) * sp_lama)
        scarto = (6500 - 60) - somma_reale
        
        # Colore in base allo scarto
        if scarto <= 250: color = "green"
        elif scarto <= 700: color = "orange"
        else: color = "red"
        
        with st.expander(f"📏 BARRA {idx+1} - Scarto: {int(scarto)}mm", expanded=True):
            st.markdown(f"**Stato:** :{color}[● {color.upper()}]")
            for p in b:
                st.write(f"• {p['int']}mm (Tagli: {p['tagli']}) → Ingombro: {p['reale']}mm")