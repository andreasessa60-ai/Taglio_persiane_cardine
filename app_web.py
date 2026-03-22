import streamlit as st
import math
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(
    page_title="Taglio Infissi Pro",
    page_icon="🛠️",
    layout="centered"
)

# --- CSS AVANZATO PER UI/UX ---
st.markdown("""
<style>
    /* Sfondo e font generale */
    .stApp { background-color: #f8f9fa; }
    
    /* Titoli */
    h1 { color: #1e3a8a; font-family: 'Segoe UI', sans-serif; }
    
    /* Box dei risultati metrici */
    [data-testid="stMetricValue"] { font-size: 24px; color: #1e40af; }
    
    /* Container delle barre */
    .barra-box {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #1e3a8a;
    }
    
    .barra-container {
        width: 100%;
        background-color: #e5e7eb;
        border-radius: 8px;
        height: 35px;
        display: flex;
        overflow: hidden;
        margin-top: 10px;
    }
    
    .pezzo {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 11px;
        border-right: 1px solid rgba(255,255,255,0.2);
    }
    
    .anta-color { background: linear-gradient(90deg, #3b82f6, #2563eb); }
    .zoccolo-color { background: linear-gradient(90deg, #f59e0b, #d97706); }
    .sfrido-color { background-color: #d1d5db; color: #4b5563; font-style: italic; }
    
    /* Bottoni */
    .stButton>button {
        border-radius: 8px;
        height: 3em;
        transition: all 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGICA DI CALCOLO ---
def ottimizza_logica(lista_misure, zoc_fin, zoc_port, prof_w):
    BARRA_UTILE = 6440
    LAMA = 5
    p_anta, p_zocc, g_tot = [], [], 0
    
    for m in lista_misure:
        h_t = math.floor(m["H"] - 49)
        l_t = math.floor((m["L"] - (49*2)) if m["ante"]==1 else (m["L"] - (49*2) - 143)/2)
        rif = f"{int(m['L'])}x{int(m['H'])}"
        
        for _ in range(m["qta"]):
            num_zoccoli = (zoc_fin if m["tipo"] == "Finestra" else zoc_port) * m["ante"]
            for i in range(m["ante"]):
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
    pdf.cell(190, 15, "DISTINTA DI TAGLIO PROFESSIONALE", 1, 1, 'C')
    
    def stampa(tit, b, r, g, bl):
        if not b: return
        pdf.ln(5); pdf.set_fill_color(r, g, bl); pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, tit, 1, 1, 'L', True)
        for i, barra in enumerate(b, 1):
            pdf.set_font("Arial", 'B', 10); pdf.cell(190, 8, f"BARRA {i}", 1, 1, 'L')
            pdf.set_font("Arial", '', 9)
            for p in barra: pdf.cell(10); pdf.cell(180, 6, f"{p['m']} mm | {p['t']} | {p['d']}", "B", 1)
    
    stampa("PROFILI ANTA", barre_a, 219, 234, 254)
    stampa("PROFILI ZOCCOLO", barre_z, 254, 243, 199)
    return pdf.output(dest='S').encode('latin-1')

# --- UI APP ---
st.title("🛠️ Officina Pro v2.8")

# 1. Impostazioni Commessa
with st.expander("📋 Impostazioni Profilo e Zoccoli", expanded=False):
    c1, c2, c3 = st.columns(3)
    z_fin = c1.number_input("Zoccoli Finestra", value=0)
    z_port = c2.number_input("Zoccoli Portafinestra", value=1)
    prof = c3.number_input("Spessore Profilo (mm)", value=30)

if 'misure' not in st.session_state: st.session_state.misure = []

# 2. Inserimento Rapido
st.markdown("### ➕ Nuovo Infisso")
with st.container(border=True):
    col_l, col_h = st.columns(2)
    l_in = col_l.number_input("Luce Larghezza (mm)", min_value=0, step=1, key="l")
    h_in = col_h.number_input("Luce Altezza (mm)", min_value=0, step=1, key="h")
    
    col_a, col_t, col_q = st.columns([1, 2, 1])
    ante_in = col_a.selectbox("Ante", [1, 2])
    tipo_in = col_t.radio("Modello", ["Finestra", "Portafinestra"], horizontal=True)
    qta_in = col_q.number_input("Quantità", min_value=1, value=1)
    
    if st.button("AGGIUNGI ALLA LISTA", type="primary", use_container_width=True):
        if l_in > 0 and h_in > 0:
            st.session_state.misure.append({"L": l_in, "H": h_in, "ante": ante_in, "tipo": tipo_in, "qta": qta_in})
            st.toast("Infisso aggiunto!")

# 3. Elenco e Azioni
if st.session_state.misure:
    st.markdown("---")
    st.markdown("### 📝 Riepilogo Ordine")
    
    # Lista moderna con badge
    for idx, m in enumerate(st.session_state.misure):
        st.markdown(f"**#{idx+1}** | **{m['qta']}pz** {m['tipo']} {int(m['L'])}x{int(m['H'])} ({m['ante']} ante)")
    
    col_del1, col_del2 = st.columns(2)
    if col_del1.button("🔙 Elimina Ultimo", use_container_width=True):
        st.session_state.misure.pop(); st.rerun()
    if col_del2.button("🗑️ Svuota Tutto", use_container_width=True):
        st.session_state.misure = []; st.rerun()

    # 4. Risultati e PDF
    ba, bz, gt = ottimizza_logica(st.session_state.misure, z_fin, z_port, prof)
    
    st.markdown("### 🚀 Totali Materiale")
    m1, m2, m3 = st.columns(3)
    m1.metric("Barre Anta", f"{len(ba)}")
    m2.metric("Barre Zocc.", f"{len(bz)}")
    m3.metric("Guarnizione", f"{round((gt*1.05)/1000, 1)}m")
    
    pdf_bytes = genera_pdf(ba, bz, gt)
    st.download_button(
        label="📥 SCARICA DISTINTA PDF",
        data=pdf_bytes,
        file_name=f"Taglio_{datetime.now().strftime('%d%m_%H%M')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # 5. Visualizzazione Grafica
    st.markdown("### 👀 Schema di Taglio")
    
    BARRA_MAX = 6500
    LAMA = 5
    
    if ba:
        st.caption("PROFILI ANTA")
        for i, b in enumerate(ba, 1):
            usato = sum(p['m'] for p in b) + LAMA * (len(b)-1)
            sfrido = BARRA_MAX - usato
            st.markdown(f'<div class="info-testo">Barra {i} (Sfrido: {int(sfrido)}mm)</div>', unsafe_allow_html=True)
            html_b = '<div class="barra-container">'
            for p in b:
                w = (p['m']/BARRA_MAX)*100
                html_b += f'<div class="pezzo anta-color" style="width: {w}%;">{p["m"]}</div>'
            if sfrido > 20:
                w_s = (sfrido/BARRA_MAX)*100
                html_b += f'<div class="pezzo sfrido-color" style="width: {w_s}%;">{int(sfrido)}</div>'
            html_b += '</div>'
            st.markdown(html_b, unsafe_allow_html=True)

    if bz:
        st.caption("PROFILI ZOCCOLO")
        for i, b in enumerate(bz, 1):
            usato = sum(p['m'] for p in b) + LAMA * (len(b)-1)
            sfrido = BARRA_MAX - usato
            st.markdown(f'<div class="info-testo">Barra {i} (Sfrido: {int(sfrido)}mm)</div>', unsafe_allow_html=True)
            html_b = '<div class="barra-container">'
            for p in b:
                w = (p['m']/BARRA_MAX)*100
                html_b += f'<div class="pezzo zoccolo-color" style="width: {w}%;">{p["m"]}</div>'
            if sfrido > 20:
                w_s = (sfrido/BARRA_MAX)*100
                html_b += f'<div class="pezzo sfrido-color" style="width: {w_s}%;">{int(sfrido)}</div>'
            html_b += '</div>'
            st.markdown(html_b, unsafe_allow_html=True)