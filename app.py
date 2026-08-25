import streamlit as st
import sqlite3
import pandas as pd

# ---------------------------------------------------------
# Configurazione Pagina (Mobile-friendly)
# ---------------------------------------------------------
st.set_page_config(page_title="La Mia Libreria", page_icon="📚", layout="centered")

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

# Inizializza il DB all'avvio
init_db()

# ---------------------------------------------------------
# Interfaccia Utente (Streamlit UI)
# ---------------------------------------------------------
st.title("📚 Il Mio Catalogo Libri")

menu = st.sidebar.radio("Navigazione", ["📖 Catalogo", "➕ Nuovo Libro", "✏️ Modifica / Elimina"])

# 1. SCHERMATA: CATALOGO
if menu == "📖 Catalogo":
    st.subheader("Elenco Libri")
    df = get_libri()
    
    if df.empty:
        st.info("Nessun libro inserito finora. Vai su '➕ Nuovo Libro' per aggiungerne uno.")
    else:
        # Ricerca per filtro rapido
        filtro = st.text_input("🔍 Cerca per titolo, autore o ubicazione", "")
        if filtro:
            df = df[
                df["titolo"].str.contains(filtro, case=False, na=False) |
                df["autore"].str.contains(filtro, case=False, na=False) |
                df["ubicazione"].str.contains(filtro, case=False, na=False)
            ]
        
        # Rinominazione colonne per visualizzazione pulita
        df_display = df.rename(columns={
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
        # Selezione tramite menu a tendina
        opzioni = {f"ID {row['id']} - {row['titolo']} ({row['autore']})": row['id'] for _, row in df.iterrows()}
        scelta = st.selectbox("Seleziona il libro da modificare:", list(opzioni.keys()))
        libro_id = opzioni[scelta]
        
        # Recupera dati correnti
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
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    btn_aggiorna = st.form_submit_button("🔄 Aggiorna Dati")
                
            if btn_aggiorna:
                if not nuovo_titolo.strip() or not nuovo_autore.strip():
                    st.error("I campi 'Titolo' e 'Autore' non possono essere vuoti.")
                else:
                    update_libro(libro_id, nuovo_titolo.strip(), nuovo_autore.strip(), nuova_desc.strip(), nuova_val, nuova_ubic.strip())
                    st.success("Dati aggiornati correttamente!")
                    st.rerun()

            # Opzione di eliminazione separata per sicurezza
            st.divider()
            with st.expander("🗑️ Zona Pericolo - Elimina Libro"):
                st.warning("L'eliminazione è irreversibile.")
                if st.button("Elimina definitivamente questo libro"):
                    delete_libro(libro_id)
                    st.success("Libro eliminato.")
                    st.rerun()