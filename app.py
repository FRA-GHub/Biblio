import streamlit as st
import sqlite3
import pandas as pd

# ---------------------------------------------------------
# Configurazione Pagina
# ---------------------------------------------------------
st.set_page_config(page_title="I Miei Libri", page_icon="📚", layout="centered")

# ---------------------------------------------------------
# Gestione Database SQLite
# ---------------------------------------------------------
def get_connection():
    conn = sqlite3.connect("biblioteca.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS libri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo TEXT NOT NULL,
            autore TEXT NOT NULL,
            descrizione TEXT,
            valutazione INTEGER CHECK(valutazione >= 1 AND valutazione <= 10),
            ubicazione TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_libro(titolo, autore, descrizione, valutazione, ubicazione):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO libri (titolo, autore, descrizione, valutazione, ubicazione)
        VALUES (?, ?, ?, ?, ?)
    """, (titolo, autore, descrizione, valutazione, ubicazione))
    conn.commit()
    conn.close()

def get_libri():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM libri ORDER BY id DESC", conn)
    conn.close()
    return df

def get_libro_by_id(libro_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM libri WHERE id = ?", (libro_id,))
    row = c.fetchone()
    conn.close()
    return row

def update_libro(libro_id, titolo, autore, descrizione, valutazione, ubicazione):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE libri 
        SET titolo = ?, autore = ?, descrizione = ?, valutazione = ?, ubicazione = ?
        WHERE id = ?
    """, (titolo, autore, descrizione, valutazione, ubicazione, libro_id))
    conn.commit()
    conn.close()

def delete_libro(libro_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM libri WHERE id = ?", (libro_id,))
    conn.commit()
    conn.close()

# Inizializza DB all'avvio
init_db()

# ---------------------------------------------------------
# Interfaccia Utente (Streamlit UI)
# ---------------------------------------------------------
st.title("📚 Catalogo Libri")

menu = st.sidebar.radio("Navigazione", ["📖 Catalogo", "➕ Nuovo Libro", "✏️ Modifica / Elimina"])

# 1. SCHERMATA: CATALOGO CON FILTRI AVANZATI
if menu == "📖 Catalogo":
    st.subheader("Elenco e Ricerca Libri")
    df = get_libri()
    
    if df.empty:
        st.info("Nessun libro presente. Vai su '➕ Nuovo Libro' per iniziare ad aggiungerne!")
    else:
        # Sezione Filtri espandibile
        with st.expander("🔍 Filtri di ricerca avanzati", expanded=True):
            # 1. Ricerca testuale rapida
            testo_ricerca = st.text_input("Cerca per parola chiave (nel titolo o descrizione):", placeholder="es. avventura, nome...")

            col1, col2 = st.columns(2)
            
            with col1:
                # 2. Filtro Autore
                autori_unici = sorted([a for a in df["autore"].dropna().unique() if a.strip()])
                autori_selezionati = st.multiselect("Filtra per Autore:", options=autori_unici)
                
            with col2:
                # 3. Filtro Ubicazione
                ubicazioni_uniche = sorted([u for u in df["ubicazione"].dropna().unique() if u.strip()])
                ubicazioni_selezionate = st.multiselect("Filtra per Ubicazione:", options=ubicazioni_uniche)

            # 4. Filtro per Range di Voto
            voto_min, voto_max = st.slider("Filtra per Valutazione (Voto)", min_value=1, max_value=10, value=(1, 10))

        # --- Applicazione dei Filtri al DataFrame ---
        df_filtrato = df.copy()

        # Filtro testo (titolo o descrizione)
        if testo_ricerca:
            df_filtrato = df_filtrato[
                df_filtrato["titolo"].str.contains(testo_ricerca, case=False, na=False) |
                df_filtrato["descrizione"].str.contains(testo_ricerca, case=False, na=False)
            ]

        # Filtro per Autori selezionati
        if autori_selezionati:
            df_filtrato = df_filtrato[df_filtrato["autore"].isin(autori_selezionati)]

        # Filtro per Ubicazioni selezionate
        if ubicazioni_selezionate:
            df_filtrato = df_filtrato[df_filtrato["ubicazione"].isin(ubicazioni_selezionate)]

        # Filtro per Valutazione
        df_filtrato = df_filtrato[
            (df_filtrato["valutazione"] >= voto_min) & 
            (df_filtrato["valutazione"] <= voto_max)
        ]

        # Indicatore numero risultati trovati
        st.caption(f"Trovati **{len(df_filtrato)}** libri su {len(df)} totali")

        # Tabella visualizzata
        df_display = df_filtrato.rename(columns={
            "id": "ID",
            "titolo": "Titolo",
            "autore": "Autore",
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
        descrizione = st.text_area("Descrizione breve", placeholder="Breve trama o appunti...")
        valutazione = st.slider("Valutazione (1-10)", min_value=1, max_value=10, value=7)
        ubicazione = st.text_input("Ubicazione", placeholder="es. Mensola studio 2, Comodino...")
        
        submitted = st.form_submit_button("💾 Salva Libro")
        if submitted:
            if not titolo.strip() or not autore.strip():
                st.error("I campi 'Titolo' e 'Autore' sono obbligatori!")
            else:
                add_libro(titolo.strip(), autore.strip(), descrizione.strip(), valutazione, ubicazione.strip())
                st.success(f"Libro '{titolo}' aggiunto con successo!")

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
            _, curr_titolo, curr_autore, curr_desc, curr_val, curr_ubic = libro_selezionato
            
            with st.form("form_modifica"):
                st.text(f"ID Libro univoco: {libro_id}")
                nuovo_titolo = st.text_input("Titolo", value=curr_titolo)
                nuovo_autore = st.text_input("Autore", value=curr_autore)
                nuova_desc = st.text_area("Descrizione breve", value=curr_desc if curr_desc else "")
                nuova_val = st.slider("Valutazione (1-10)", min_value=1, max_value=10, value=int(curr_val) if curr_val else 5)
                nuova_ubic = st.text_input("Ubicazione", value=curr_ubic if curr_ubic else "")
                
                btn_aggiorna = st.form_submit_button("🔄 Aggiorna Dati")
                
            if btn_aggiorna:
                if not nuovo_titolo.strip() or not nuovo_autore.strip():
                    st.error("I campi 'Titolo' e 'Autore' non possono essere vuoti.")
                else:
                    update_libro(libro_id, nuovo_titolo.strip(), nuovo_autore.strip(), nuova_desc.strip(), nuova_val, nuova_ubic.strip())
                    st.success("Dati aggiornati correttamente!")
                    st.rerun()

            st.divider()
            with st.expander("🗑️ Zona Pericolo - Elimina Libro"):
                st.warning("L'eliminazione è irreversibile.")
                if st.button("Elimina definitivamente questo libro"):
                    delete_libro(libro_id)
                    st.success("Libro eliminato.")
                    st.rerun()
