import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ---------------------------------------------------------
# Configurazione Pagina
# ---------------------------------------------------------
st.set_page_config(page_title="I Miei Libri", page_icon="📚", layout="centered")

# ---------------------------------------------------------
# Connessione a Supabase
# ---------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ---------------------------------------------------------
# Funzioni CRUD (Database)
# ---------------------------------------------------------
def get_libri():
    try:
        response = supabase.table("libri").select("*").order("id", desc=True).execute()
        data = response.data
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame(columns=["id", "titolo", "autore", "edizione_anno", "descrizione", "valutazione", "ubicazione"])
    except Exception as e:
        st.error(f"Errore di connessione a Supabase: {e}")
        return pd.DataFrame()

def add_libro(titolo, autore, descrizione, valutazione, ubicazione, edizione_anno=""):
    payload = {
        "titolo": titolo,
        "autore": autore,
        "descrizione": descrizione,
        "valutazione": valutazione,
        "ubicazione": ubicazione,
        "edizione_anno": edizione_anno
    }
    supabase.table("libri").insert(payload).execute()

def get_libro_by_id(libro_id):
    response = supabase.table("libri").select("*").eq("id", libro_id).execute()
    if response.data:
        return response.data[0]
    return None

def update_libro(libro_id, titolo, autore, descrizione, valutazione, ubicazione, edizione_anno=""):
    payload = {
        "titolo": titolo,
        "autore": autore,
        "descrizione": descrizione,
        "valutazione": valutazione,
        "ubicazione": ubicazione,
        "edizione_anno": edizione_anno
    }
    supabase.table("libri").update(payload).eq("id", libro_id).execute()

def delete_libro(libro_id):
    supabase.table("libri").delete().eq("id", libro_id).execute()

# ---------------------------------------------------------
# Interfaccia Utente (Streamlit UI)
# ---------------------------------------------------------
st.title("📚 Catalogo Libri")

menu = st.sidebar.radio("Navigazione", ["📖 Catalogo", "➕ Nuovo Libro", "✏️ Modifica / Elimina"])

# 1. SCHERMATA: CATALOGO CON FILTRI
if menu == "📖 Catalogo":
    st.subheader("Elenco e Ricerca Libri")
    df = get_libri()
    
    if df.empty:
        st.info("Nessun libro presente nel database. Vai su '➕ Nuovo Libro' per aggiungerne uno!")
    else:
        with st.expander("🔍 Filtri di ricerca avanzati", expanded=True):
            testo_ricerca = st.text_input("Cerca per parola chiave (nel titolo o descrizione):", placeholder="es. avventura, nome...")

            col1, col2 = st.columns(2)
            with col1:
                autori_unici = sorted([str(a) for a in df["autore"].dropna().unique() if str(a).strip()])
                autori_selezionati = st.multiselect("Filtra per Autore:", options=autori_unici)
                
            with col2:
                ubicazioni_uniche = sorted([str(u) for u in df["ubicazione"].dropna().unique() if str(u).strip()])
                ubicazioni_selezionate = st.multiselect("Filtra per Ubicazione:", options=ubicazioni_uniche)

            voto_min, voto_max = st.slider("Filtra per Valutazione (Voto)", min_value=1, max_value=10, value=(1, 10))

        # Applicazione Filtri
        df_filtrato = df.copy()

        if testo_ricerca:
            df_filtrato = df_filtrato[
                df_filtrato["titolo"].astype(str).str.contains(testo_ricerca, case=False, na=False) |
                df_filtrato["descrizione"].astype(str).str.contains(testo_ricerca, case=False, na=False)
            ]

        if autori_selezionati:
            df_filtrato = df_filtrato[df_filtrato["autore"].isin(autori_selezionati)]

        if ubicazioni_selezionate:
            df_filtrato = df_filtrato[df_filtrato["ubicazione"].isin(ubicazioni_selezionate)]

        # Gestione valori nulli su valutazione
        df_filtrato["valutazione"] = pd.to_numeric(df_filtrato["valutazione"], errors="coerce").fillna(0)
        df_filtrato = df_filtrato[
            (df_filtrato["valutazione"] >= voto_min) & 
            (df_filtrato["valutazione"] <= voto_max)
        ]

        st.caption(f"Trovati **{len(df_filtrato)}** libri su {len(df)} totali")

        colonne_da_mostrare = ["id", "titolo", "autore", "edizione_anno", "descrizione", "valutazione", "ubicazione"]
        df_display = df_filtrato[[c for c in colonne_da_mostrare if c in df_filtrato.columns]].rename(columns={
            "id": "ID",
            "titolo": "Titolo",
            "autore": "Autore",
            "edizione_anno": "Edizione / Anno",
            "descrizione": "Descrizione",
            "valutazione": "Voto (1-10)",
            "ubicazione": "Ubicazione"
        })
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# 2. SCHERMATA: AGGIUNGI LIBRO
elif menu == "➕ Nuovo Libro":
    st.subheader("Inserisci un nuovo libro")
    
    with st.form("form_nuovo_libro", clear_on_submit=True):
        titolo = st.text_input("Titolo *", placeholder="es. Il nome della rosa")
        autore = st.text_input("Autore *", placeholder="es. Umberto Eco")
        edizione_anno = st.text_input("Edizione / Anno", placeholder="es. 1980, Bompiani 2012...")
        descrizione = st.text_area("Descrizione breve", placeholder="Breve trama o appunti...")
        valutazione = st.slider("Valutazione (1-10)", min_value=1, max_value=10, value=7)
        ubicazione = st.text_input("Ubicazione", placeholder="es. Mensola studio 2, Comodino...")
        
        submitted = st.form_submit_button("💾 Salva Libro")
        if submitted:
            if not titolo.strip() or not autore.strip():
                st.error("I campi 'Titolo' e 'Autore' sono obbligatori!")
            else:
                add_libro(titolo.strip(), autore.strip(), descrizione.strip(), valutazione, ubicazione.strip(), edizione_anno.strip())
                st.success(f"Libro '{titolo}' salvato su Supabase!")

# 3. SCHERMATA: MODIFICA / ELIMINA
elif menu == "✏️ Modifica / Elimina":
    st.subheader("Aggiorna i dati di un libro")
    df = get_libri()
    
    if df.empty:
        st.info("Nessun libro disponibile da modificare.")
    else:
        opzioni = {f"ID {row['id']} - {row['titolo']} ({row['autore']})": row['id'] for _, row in df.iterrows()}
        scelta = st.selectbox("Seleziona il libro da modificare:", list(opzioni.keys()))
        libro_id = opzioni[scelta]
        
        libro_selezionato = get_libro_by_id(libro_id)
        
        if libro_selezionato:
            with st.form("form_modifica"):
                st.text(f"ID Libro univoco: {libro_id}")
                nuovo_titolo = st.text_input("Titolo", value=libro_selezionato.get("titolo", ""))
                nuovo_autore = st.text_input("Autore", value=libro_selezionato.get("autore", ""))
                nuova_edizione_anno = st.text_input("Edizione / Anno", value=libro_selezionato.get("edizione_anno") or "")
                nuova_desc = st.text_area("Descrizione breve", value=libro_selezionato.get("descrizione") or "")
                val_corr = libro_selezionato.get("valutazione")
                nuova_val = st.slider("Valutazione (1-10)", min_value=1, max_value=10, value=int(val_corr) if val_corr else 5)
                nuova_ubic = st.text_input("Ubicazione", value=libro_selezionato.get("ubicazione") or "")
                
                btn_aggiorna = st.form_submit_button("🔄 Aggiorna Dati")
                
            if btn_aggiorna:
                if not nuovo_titolo.strip() or not nuovo_autore.strip():
                    st.error("I campi 'Titolo' e 'Autore' non possono essere vuoti.")
                else:
                    update_libro(libro_id, nuovo_titolo.strip(), nuovo_autore.strip(), nuova_desc.strip(), nuova_val, nuova_ubic.strip(), nuova_edizione_anno.strip())
                    st.success("Dati aggiornati correttamente su Supabase!")
                    st.rerun()

            st.divider()
            with st.expander("🗑️ Zona Pericolo - Elimina Libro"):
                st.warning("L'eliminazione è irreversibile.")
                if st.button("Elimina definitivamente questo libro"):
                    delete_libro(libro_id)
                    st.success("Libro eliminato.")
                    st.rerun()
