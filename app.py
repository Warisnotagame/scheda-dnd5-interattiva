import gradio as gr
import json
import os
from datetime import datetime

# ============================================================
# CELLA 1 — Setup, caratteristiche e modificatori
# ============================================================

def calcola_modificatore(punteggio):
    return (punteggio - 10) // 2

def formatta_modificatore(mod):
    return f"+{mod}" if mod >= 0 else str(mod)

def aggiorna_modificatori(forza, destrezza, costituzione, intelligenza, saggezza, carisma):
    mod_for = formatta_modificatore(calcola_modificatore(forza))
    mod_des = formatta_modificatore(calcola_modificatore(destrezza))
    mod_cos = formatta_modificatore(calcola_modificatore(costituzione))
    mod_int = formatta_modificatore(calcola_modificatore(intelligenza))
    mod_sag = formatta_modificatore(calcola_modificatore(saggezza))
    mod_car = formatta_modificatore(calcola_modificatore(carisma))
    return mod_for, mod_des, mod_cos, mod_int, mod_sag, mod_car

def raccogli_stato_scheda(nome, razza, classe, background, livello,
                            forza, destrezza, costituzione, intelligenza, saggezza, carisma):
    stato = {
        "nome": nome, "razza": razza, "classe": classe,
        "background": background, "livello": livello,
        "caratteristiche": {
            "forza": forza, "destrezza": destrezza, "costituzione": costituzione,
            "intelligenza": intelligenza, "saggezza": saggezza, "carisma": carisma
        }
    }
    return json.dumps(stato, indent=2, ensure_ascii=False)

# ============================================================
# CELLA 2 — Bonus competenza, tiri salvezza, abilità
# ============================================================

def calcola_bonus_competenza(livello):
    return 2 + (livello - 1) // 4

ABILITA = {
    "Acrobazia": "destrezza", "Addestrare Animali": "saggezza", "Arcano": "intelligenza",
    "Atletica": "forza", "Furtività": "destrezza", "Indagare": "intelligenza",
    "Inganno": "carisma", "Intimidire": "carisma", "Intrattenere": "carisma",
    "Intuizione": "saggezza", "Medicina": "saggezza", "Natura": "intelligenza",
    "Percezione": "saggezza", "Persuasione": "carisma", "Religione": "intelligenza",
    "Rapidità di Mano": "destrezza", "Sopravvivenza": "saggezza", "Storia": "intelligenza",
}

def calcola_valore_abilita(punteggio_caratteristica, livello, competente):
    mod = calcola_modificatore(punteggio_caratteristica)
    if competente:
        mod += calcola_bonus_competenza(livello)
    return formatta_modificatore(mod)

def aggiorna_salvezze(livello, forza, destrezza, costituzione, intelligenza, saggezza, carisma,
                       comp_for, comp_des, comp_cos, comp_int, comp_sag, comp_car):
    punteggi = [forza, destrezza, costituzione, intelligenza, saggezza, carisma]
    competenze = [comp_for, comp_des, comp_cos, comp_int, comp_sag, comp_car]
    return [calcola_valore_abilita(p, livello, c) for p, c in zip(punteggi, competenze)]

def aggiorna_abilita(livello, forza, destrezza, costituzione, intelligenza, saggezza, carisma, *competenze_abilita):
    valori_caratteristiche = {
        "forza": forza, "destrezza": destrezza, "costituzione": costituzione,
        "intelligenza": intelligenza, "saggezza": saggezza, "carisma": carisma
    }
    risultati = []
    for (nome_abilita, caratteristica_rif), competente in zip(ABILITA.items(), competenze_abilita):
        punteggio = valori_caratteristiche[caratteristica_rif]
        risultati.append(calcola_valore_abilita(punteggio, livello, competente))
    return risultati

def aggiorna_bonus_competenza_display(livello):
    return formatta_modificatore(calcola_bonus_competenza(livello))

# ============================================================
# CELLA 3 — Classi e progressioni (12 classi complete)
# ============================================================

DADI_VITA_CLASSE = {
    "Barbaro": 12, "Bardo": 8, "Chierico": 8, "Druido": 8, "Guerriero": 10,
    "Ladro": 8, "Mago": 6, "Monaco": 8, "Paladino": 10, "Ranger": 10,
    "Stregone": 6, "Warlock": 8,
}

SLOT_INCANTESIMO = {
    "Mago": {
        1: [2,0,0,0,0,0,0,0,0], 2: [3,0,0,0,0,0,0,0,0], 3: [4,2,0,0,0,0,0,0,0],
        4: [4,3,0,0,0,0,0,0,0], 5: [4,3,2,0,0,0,0,0,0], 6: [4,3,3,0,0,0,0,0,0],
        7: [4,3,3,1,0,0,0,0,0], 8: [4,3,3,2,0,0,0,0,0], 9: [4,3,3,3,1,0,0,0,0],
        10:[4,3,3,3,2,0,0,0,0],
    },
}
for _c in ["Chierico", "Bardo", "Druido", "Stregone"]:
    SLOT_INCANTESIMO[_c] = SLOT_INCANTESIMO["Mago"]

SLOT_INCANTESIMO_MEZZI = {
    1: [0,0,0,0,0], 2: [2,0,0,0,0], 3: [3,0,0,0,0], 4: [3,0,0,0,0],
    5: [4,2,0,0,0], 6: [4,2,0,0,0], 7: [4,3,0,0,0], 8: [4,3,0,0,0],
    9: [4,3,2,0,0], 10:[4,3,2,0,0],
}
for _c in ["Paladino", "Ranger"]:
    SLOT_INCANTESIMO[_c] = SLOT_INCANTESIMO_MEZZI

SLOT_PATTO_WARLOCK = {
    1: {"slot": 1, "livello_slot": 1}, 2: {"slot": 2, "livello_slot": 1},
    3: {"slot": 2, "livello_slot": 2}, 4: {"slot": 2, "livello_slot": 2},
    5: {"slot": 2, "livello_slot": 3}, 6: {"slot": 2, "livello_slot": 3},
    7: {"slot": 2, "livello_slot": 4}, 8: {"slot": 2, "livello_slot": 4},
    9: {"slot": 2, "livello_slot": 5}, 10:{"slot": 2, "livello_slot": 5},
}

def calcola_dado_vita(classe):
    valore = DADI_VITA_CLASSE.get(classe, 8)
    return f"d{valore}"

def calcola_pf_massimi_suggeriti(classe, livello, mod_costituzione):
    dado = DADI_VITA_CLASSE.get(classe, 8)
    media_dado = (dado // 2) + 1
    pf = dado + mod_costituzione
    if livello > 1:
        pf += (media_dado + mod_costituzione) * (livello - 1)
    return max(pf, 1)

def calcola_slot_incantesimo(classe, livello):
    if classe == "Warlock":
        livello_usato = min(livello, max(SLOT_PATTO_WARLOCK.keys()))
        dati = SLOT_PATTO_WARLOCK[livello_usato]
        return f"Patto Magico: {dati['slot']} slot di livello {dati['livello_slot']} (ricarica con riposo BREVE)"
    if classe not in SLOT_INCANTESIMO:
        return "Nessuno slot incantesimo (classe non incantatrice o non gestita)"
    tabella_classe = SLOT_INCANTESIMO[classe]
    livello_usato = min(livello, max(tabella_classe.keys()))
    slot = tabella_classe[livello_usato]
    testo = " | ".join([f"Lv{i+1}: {s}" for i, s in enumerate(slot) if s > 0])
    return testo if testo else "Nessuno slot disponibile a questo livello"

def aggiorna_progressione_classe(classe, livello, costituzione):
    dado = calcola_dado_vita(classe)
    mod_cos = calcola_modificatore(costituzione)
    pf_suggeriti = calcola_pf_massimi_suggeriti(classe, int(livello), mod_cos)
    slot = calcola_slot_incantesimo(classe, int(livello))
    return dado, pf_suggeriti, slot

# ============================================================
# CELLA 4 — Salvataggio e caricamento
# ============================================================

CARTELLA_SALVATAGGI = "schede_salvate"
os.makedirs(CARTELLA_SALVATAGGI, exist_ok=True)

def salva_scheda_completa(nome, razza, classe, background, livello,
                            forza, destrezza, costituzione, intelligenza, saggezza, carisma,
                            pf_massimi, pf_attuali,
                            comp_for, comp_des, comp_cos, comp_int, comp_sag, comp_car,
                            *competenze_abilita):
    stato = {
        "nome": nome, "razza": razza, "classe": classe, "background": background, "livello": livello,
        "caratteristiche": {
            "forza": forza, "destrezza": destrezza, "costituzione": costituzione,
            "intelligenza": intelligenza, "saggezza": saggezza, "carisma": carisma
        },
        "pf_massimi": pf_massimi, "pf_attuali": pf_attuali,
        "competenze_salvezza": {
            "forza": comp_for, "destrezza": comp_des, "costituzione": comp_cos,
            "intelligenza": comp_int, "saggezza": comp_sag, "carisma": comp_car
        },
        "competenze_abilita": dict(zip(ABILITA.keys(), competenze_abilita))
    }
    nome_file_sicuro = (nome.strip() or "personaggio_senza_nome").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    percorso_file = os.path.join(CARTELLA_SALVATAGGI, f"{nome_file_sicuro}_{timestamp}.json")
    with open(percorso_file, "w", encoding="utf-8") as f:
        json.dump(stato, f, indent=2, ensure_ascii=False)
    return percorso_file

def carica_scheda_da_file(file_caricato):
    if file_caricato is None:
        return ("", "", "Guerriero", "", 1, 10, 10, 10, 10, 10, 10, 10, 10,
                False, False, False, False, False, False, *([False] * len(ABILITA)))
    with open(file_caricato.name, "r", encoding="utf-8") as f:
        stato = json.load(f)
    car = stato.get("caratteristiche", {})
    comp_salv = stato.get("competenze_salvezza", {})
    comp_abil = stato.get("competenze_abilita", {})
    valori_competenze_abilita = [comp_abil.get(n, False) for n in ABILITA.keys()]
    return (
        stato.get("nome", ""), stato.get("razza", ""), stato.get("classe", "Guerriero"),
        stato.get("background", ""), stato.get("livello", 1),
        car.get("forza", 10), car.get("destrezza", 10), car.get("costituzione", 10),
        car.get("intelligenza", 10), car.get("saggezza", 10), car.get("carisma", 10),
        stato.get("pf_massimi", 10), stato.get("pf_attuali", 10),
        comp_salv.get("forza", False), comp_salv.get("destrezza", False), comp_salv.get("costituzione", False),
        comp_salv.get("intelligenza", False), comp_salv.get("saggezza", False), comp_salv.get("carisma", False),
        *valori_competenze_abilita
    )

# ============================================================
# CELLA 5 — Catalogo mostri/PNG
# ============================================================

CATALOGO_MOSTRI = {
    "Goblin": {"ca": 15, "pf_max": 7, "velocita": "9 m", "gs": "1/4",
        "attacco": "Scimitarra +4 (1d6+2 tagliente)", "note": "Disciplina Nimbile"},
    "Orco": {"ca": 13, "pf_max": 15, "velocita": "9 m", "gs": "1/2",
        "attacco": "Ascia Possente +5 (1d12+3 tagliente)", "note": "Aggressivo"},
    "Lupo": {"ca": 13, "pf_max": 11, "velocita": "12 m", "gs": "1/4",
        "attacco": "Morso +4 (2d4+2 perforante)", "note": "TS Forza CD11 o prono"},
    "Scheletro": {"ca": 13, "pf_max": 13, "velocita": "9 m", "gs": "1/4",
        "attacco": "Spada Corta +4 (1d6+2 perforante)", "note": "Immune veleno, vulnerabile contundente"},
    "Banditi": {"ca": 12, "pf_max": 11, "velocita": "9 m", "gs": "1/8",
        "attacco": "Spada Corta +3 (1d6+1 perforante)", "note": "Soldato semplice"},
    "Orso Bruno": {"ca": 11, "pf_max": 34, "velocita": "12 m", "gs": "1",
        "attacco": "Artigli +5 (2d8+4 tagliente)", "note": "Olfatto e udito acuti"},
    "Troll": {"ca": 15, "pf_max": 84, "velocita": "9 m", "gs": "5",
        "attacco": "Morso/Artigli +7", "note": "Rigenerazione 10 PF/turno"},
    "Drago Giovane (generico)": {"ca": 18, "pf_max": 178, "velocita": "12 m / volo 24 m", "gs": "10",
        "attacco": "Morso +10 (2d10+6) + soffio", "note": "Resistenza leggendaria"},
}

def carica_dati_mostro(nome_mostro):
    if nome_mostro not in CATALOGO_MOSTRI:
        return "-", 0, "-", "-", "-", "-"
    m = CATALOGO_MOSTRI[nome_mostro]
    return m["ca"], m["pf_max"], m["velocita"], m["gs"], m["attacco"], m["note"]

def aggiungi_al_combattimento(nome_mostro, lista_attuale):
    if nome_mostro not in CATALOGO_MOSTRI:
        return lista_attuale, lista_attuale
    m = CATALOGO_MOSTRI[nome_mostro]
    numero_istanza = sum(1 for riga in lista_attuale if riga[0].startswith(nome_mostro)) + 1
    nuova_riga = [f"{nome_mostro} #{numero_istanza}", m["ca"], m["pf_max"], m["pf_max"], m["gs"]]
    lista_aggiornata = lista_attuale + [nuova_riga]
    return lista_aggiornata, lista_aggiornata

def svuota_combattimento():
    return [], []

# ============================================================
# CELLA 6 — CSS pergamena
# ============================================================

CSS_PERGAMENA = """
@import url('https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap');

:root {
    --colore-pergamena: #f4e8d0;
    --colore-pergamena-scura: #e6d4a8;
    --colore-bordo: #6b4423;
    --colore-bordo-chiaro: #8b5a2b;
    --colore-testo: #3d2817;
    --colore-accento: #8b1a1a;
    --colore-oro: #b8860b;
}

.gradio-container {
    background-color: var(--colore-pergamena) !important;
    background-image:
        repeating-linear-gradient(0deg, rgba(139,90,43,0.02) 0px, transparent 2px, transparent 4px),
        radial-gradient(circle at 15% 20%, rgba(139,90,43,0.06) 0%, transparent 45%),
        radial-gradient(circle at 85% 80%, rgba(139,90,43,0.06) 0%, transparent 45%) !important;
    font-family: 'Georgia', 'Times New Roman', serif !important;
    color: var(--colore-testo) !important;
    font-size: 14px !important;
}

.gradio-container h1 {
    color: var(--colore-accento) !important;
    text-align: center !important;
    font-variant: small-caps !important;
    letter-spacing: 2px !important;
    border-bottom: 3px double var(--colore-bordo) !important;
    padding-bottom: 10px !important;
    margin-bottom: 16px !important;
}

.gradio-container h2, .gradio-container h3 {
    color: var(--colore-bordo) !important;
    font-variant: small-caps !important;
    letter-spacing: 1px !important;
    border-left: 4px solid var(--colore-accento) !important;
    padding: 2px 0 2px 10px !important;
    margin: 10px 0 6px 0 !important;
    background: linear-gradient(90deg, var(--colore-pergamena-scura) 0%, transparent 100%) !important;
    font-size: 0.95em !important;
}

.tabs {
    border: 3px solid var(--colore-bordo) !important;
    border-radius: 6px !important;
    background-color: var(--colore-pergamena-scura) !important;
    padding: 4px !important;
}

button[role="tab"] {
    font-variant: small-caps !important;
    font-weight: bold !important;
    letter-spacing: 1px !important;
    color: var(--colore-bordo) !important;
    border-radius: 4px 4px 0 0 !important;
}

button[role="tab"][aria-selected="true"] {
    background-color: var(--colore-accento) !important;
    color: var(--colore-pergamena) !important;
}

.gradio-container .gr-group, .gradio-container [class*="group"] {
    border: 1.5px solid var(--colore-bordo-chiaro) !important;
    border-radius: 5px !important;
    background-color: rgba(255,253,247,0.5) !important;
    padding: 4px !important;
    margin-bottom: 4px !important;
}

.gradio-container input, .gradio-container textarea, .gradio-container select {
    background-color: #fffdf7 !important;
    border: 1.5px solid var(--colore-bordo-chiaro) !important;
    border-radius: 3px !important;
    color: var(--colore-testo) !important;
    padding: 4px 6px !important;
    font-size: 0.92em !important;
}

.gradio-container input:focus, .gradio-container textarea:focus {
    border-color: var(--colore-accento) !important;
    box-shadow: 0 0 4px rgba(139,26,26,0.35) !important;
}

.gradio-container label span {
    color: var(--colore-bordo) !important;
    font-weight: bold !important;
    font-variant: small-caps !important;
    font-size: 0.85em !important;
}

.gradio-container button.primary, .gradio-container button[variant="primary"] {
    background: linear-gradient(180deg, #8b1a1a 0%, #6b1414 100%) !important;
    border: 2px solid var(--colore-oro) !important;
    color: #f4e8d0 !important;
    font-variant: small-caps !important;
    font-weight: bold !important;
    border-radius: 5px !important;
}
.gradio-container button.primary:hover {
    background: linear-gradient(180deg, #a32222 0%, #8b1a1a 100%) !important;
}
.gradio-container button.secondary {
    background-color: var(--colore-pergamena-scura) !important;
    border: 1.5px solid var(--colore-bordo) !important;
    color: var(--colore-bordo) !important;
    font-variant: small-caps !important;
}

.gradio-container input[type="checkbox"] {
    accent-color: var(--colore-accento) !important;
    width: 16px !important;
    height: 16px !important;
    box-shadow: none !important;
    outline: none !important;
}

.gradio-container table {
    border: 2px solid var(--colore-bordo) !important;
    font-size: 0.88em !important;
}
.gradio-container table th {
    background-color: var(--colore-bordo) !important;
    color: var(--colore-pergamena) !important;
    font-variant: small-caps !important;
}
.gradio-container table td {
    background-color: #fffdf7 !important;
}

.gradio-container .form, .gradio-container .block {
    gap: 4px !important;
}
.gradio-container .gap {
    gap: 6px !important;
}

.gradio-container .prose {
    border: none !important;
    padding: 0 !important;
    background: none !important;
}
.gradio-container .prose p {
    background-color: rgba(255,253,247,0.6) !important;
    border: 1px solid var(--colore-bordo-chiaro) !important;
    border-radius: 4px !important;
    padding: 8px 10px !important;
    display: block !important;
}

.gradio-container input[type="text"],
.gradio-container input[type="number"],
.gradio-container textarea,
.gradio-container .gr-text-input input {
    font-family: 'Kalam', cursive !important;
    font-weight: 700 !important;
    font-size: 1.05em !important;
    color: #1a1a2e !important;
}

[title*="resize" i],
[title*="Resize" i],
[aria-label*="resize" i] {
    display: none !important;
    pointer-events: none !important;
}
"""

# ============================================================
# CELLA 7 — Catalogo incantesimi + tracker danni/cure
# ============================================================

CATALOGO_INCANTESIMI = {
    # ---------- TRUCCHETTI (Livello 0) ----------
    "Mano Magica": {"livello": 0, "classi": ["Mago", "Bardo", "Stregone", "Warlock"],
        "descrizione": "Crei una mano spettrale che può manipolare oggetti leggeri (fino a 4,5 kg) a distanza fino a 9 m, aprire/chiudere porte non chiuse a chiave, versare liquidi. Non può attaccare o trasportare oggetti più di 9 m da te."},
    "Luce": {"livello": 0, "classi": ["Mago", "Bardo", "Chierico", "Stregone"],
        "descrizione": "Tocchi un oggetto: emette luce viva in un raggio di 6 m (e luce fioca per altri 6 m) per 1 ora. Il colore è a tua scelta."},
    "Dardo Infuocato": {"livello": 0, "classi": ["Mago", "Stregone"],
        "descrizione": "Tiro per colpire a distanza contro una creatura: 1d10 danni da fuoco. Se colpisci materiale infiammabile non indossato, lo incendi. Il danno aumenta a livelli più alti."},
    "Pietà del Moribondo": {"livello": 0, "classi": ["Chierico", "Druido"],
        "descrizione": "Tocchi una creatura morente (a 0 PF): la stabilizzi automaticamente, senza bisogno di tiri salvezza contro la morte."},
    "Fiamma Sacra": {"livello": 0, "classi": ["Chierico"],
        "descrizione": "Fiamma radiosa scende su una creatura che vedi entro 18 m. Tiro salvezza Destrezza o subisce 1d8 danni radiosi. Il bersaglio non ottiene vantaggio dalla copertura per questo tiro salvezza."},
    "Taumaturgia": {"livello": 0, "classi": ["Chierico"],
        "descrizione": "Manifesti un piccolo prodigio, un segno della presenza divina, finché l'incantesimo dura (fino a 1 minuto). Scegli un effetto: voce tonante, aprire/sbattere porte, far tremare il terreno, far ardere/spegnere fiamme, ecc."},
    "Druidismo": {"livello": 0, "classi": ["Druido"],
        "descrizione": "Crei uno dei seguenti effetti naturali a tua scelta: far germogliare un fiore, creare una folata di vento profumato, far cambiare colore a foglie, creare una piccola luce naturale o suono d'animale innocuo."},
    "Resistenza": {"livello": 0, "classi": ["Chierico", "Druido"],
        "descrizione": "Tocchi una creatura volontaria: ottiene 1d4 da aggiungere a un tiro salvezza a sua scelta, entro 1 minuto dal lancio."},
    "Riparare": {"livello": 0, "classi": ["Mago"],
        "descrizione": "Tocchi un oggetto non magico danneggiato: lo ripari completamente in un'unica azione (rottura, foro, strappo)."},
    "Prestidigitazione": {"livello": 0, "classi": ["Mago", "Bardo", "Stregone", "Warlock"],
        "descrizione": "Trucco magico minore: crei un effetto sensoriale istantaneo (scintilla, odore, suono), accendi/spegni una candela, pulisci/sporchi un piccolo oggetto, raffreddi/scaldi/insapori cibo, crei un piccolo simbolo per 1 ora, crei un oggetto illusorio non animato in mano."},
    "Globo di Forza": {"livello": 0, "classi": ["Mago"],
        "descrizione": "Crei una sfera energetica luminosa che fluttua a mezz'aria entro 18 m: emette luce e galleggia, controllabile mentalmente."},
    "Spruzzo Acido": {"livello": 0, "classi": ["Mago", "Stregone"],
        "descrizione": "Scagli una bolla d'acido contro una o due creature entro 18 m, vicine tra loro: tiro salvezza Destrezza o 1d6 danni da acido."},
    "Lama Spettrale": {"livello": 0, "classi": ["Mago", "Stregone", "Warlock"],
        "descrizione": "Crei un'arma spettrale fluttuante che attacchi: tiro per colpire a distanza, 1d8 danni da forza."},
    "Tocco Gelido": {"livello": 0, "classi": ["Mago", "Stregone"],
        "descrizione": "Crei una mano spettrale gelida: tiro per colpire a distanza, 1d8 danni necrotici, il bersaglio non può riguadagnare PF fino al tuo prossimo turno."},
    "Bagliore": {"livello": 0, "classi": ["Chierico", "Druido"],
        "descrizione": "Lampo di luce verso una creatura entro 18 m: tiro salvezza Costituzione o subisce 1d8 danni radiosi e diventa accecata fino al tuo prossimo turno."},
    "Vento Pungente": {"livello": 0, "classi": ["Druido"],
        "descrizione": "Crei una raffica di vento tagliente: 1d6 danni da forza a una creatura entro 9 m, che fallisce un TS Costituzione, e viene spinta indietro di 3 m."},
    "Imitare Suoni": {"livello": 0, "classi": ["Bardo"],
        "descrizione": "Imiti un suono che hai sentito (voce, animale, oggetto) per un singolo utilizzo entro la durata. Ascoltatori sospettosi possono tentare TS Saggezza (Intuizione) per smascherarti."},
    "Insulto Mordace": {"livello": 0, "classi": ["Bardo"],
        "descrizione": "Insulti verbalmente una creatura entro 18 m: TS Saggezza o ottiene svantaggio al prossimo tiro per colpire, prova di abilità o tiro salvezza prima della fine del tuo prossimo turno."},

    # ---------- 1° LIVELLO ----------
    "Scudo della Fede": {"livello": 1, "classi": ["Chierico", "Paladino"],
        "descrizione": "Bonus +2 alla CA per 10 minuti su te o un alleato vicino."},
    "Cura Ferite": {"livello": 1, "classi": ["Chierico", "Druido", "Paladino", "Ranger", "Bardo"],
        "descrizione": "Tocchi una creatura: recupera 1d8 + mod. caratteristica incantatrice PF."},
    "Individuazione della Magia": {"livello": 1, "classi": ["Mago", "Chierico", "Bardo", "Druido", "Paladino", "Ranger", "Stregone", "Warlock"],
        "descrizione": "Per 10 minuti percepisci la presenza di magia entro 9 m."},
    "Scudo": {"livello": 1, "classi": ["Mago", "Stregone"],
        "descrizione": "(reazione). +5 alla CA fino all'inizio del tuo prossimo turno, immune ai Missile Magico."},
    "Missile Magico": {"livello": 1, "classi": ["Mago", "Stregone"],
        "descrizione": "3 dardi di energia, 1d4+1 danni da forza ciascuno, colpiscono automaticamente."},
    "Sonno": {"livello": 1, "classi": ["Mago", "Bardo", "Stregone"],
        "descrizione": "Fa addormentare creature entro un'area, totale 5d8 PF di creature interessate, le più ferite per prime."},
    "Comando": {"livello": 1, "classi": ["Chierico", "Paladino"],
        "descrizione": "Una creatura deve obbedire a una parola singola (Fuggi, Cadi, Fermati, ecc.) se fallisce TS Saggezza."},

    # ---------- 2° LIVELLO ----------
    "Ragnatela": {"livello": 2, "classi": ["Mago", "Druido"],
        "descrizione": "Riempie un'area di ragnatele appiccicose che intrappolano le creature, TS Destrezza per non restare bloccate."},
    "Invisibilità": {"livello": 2, "classi": ["Mago", "Bardo", "Stregone", "Warlock"],
        "descrizione": "Una creatura toccata diventa invisibile fino a 1 ora o finché non attacca/lancia incantesimi."},
    "Individuazione dei Pensieri": {"livello": 2, "classi": ["Mago", "Bardo", "Stregone"],
        "descrizione": "Per 1 minuto leggi i pensieri superficiali di una creatura entro 9 m."},
    "Arma Spirituale": {"livello": 2, "classi": ["Chierico"],
        "descrizione": "Crei un'arma spettrale che attacca: 1d8 + mod. caratteristica incantatrice danni da forza."},

    # ---------- 3° LIVELLO ----------
    "Palla di Fuoco": {"livello": 3, "classi": ["Mago", "Stregone"],
        "descrizione": "Sfera di fuoco esplosiva in un punto a tua scelta entro 45 m: ogni creatura in un raggio di 6 m, TS Destrezza o 8d6 danni da fuoco (metà se supera il tiro). Incendia oggetti infiammabili non indossati nell'area."},
    "Dissolvi Magie": {"livello": 3, "classi": ["Mago", "Chierico", "Bardo", "Paladino", "Druido", "Warlock"],
        "descrizione": "Tocchi una creatura, oggetto o effetto magico entro 18 m: termina un incantesimo attivo su di esso (di livello pari o inferiore a 3 automaticamente, superiore con prova di abilità incantatrice)."},
    "Volo": {"livello": 3, "classi": ["Mago", "Stregone"],
        "descrizione": "Tocchi una creatura volontaria: ottiene velocità di volo di 18 m per 10 minuti."},
    "Contromagia": {"livello": 3, "classi": ["Mago", "Stregone", "Warlock"],
        "descrizione": "(reazione) Interrompi una creatura che sta lanciando un incantesimo entro 18 m: se è di 3° livello o inferiore, fallisce automaticamente. Se di livello superiore, prova di abilità incantatrice contro CD 10 + livello dell'incantesimo."},
    "Velocità": {"livello": 3, "classi": ["Mago", "Stregone"],
        "descrizione": "Una creatura toccata raddoppia la velocità, ottiene +2 alla CA, vantaggio ai TS di Destrezza, e un'azione bonus aggiuntiva, per 1 minuto."},
    "Respirare sott'Acqua": {"livello": 3, "classi": ["Druido", "Ranger", "Stregone"],
        "descrizione": "Fino a 10 creature volontarie toccate possono respirare sott'acqua per 24 ore."},
    "Aura Sacra": {"livello": 3, "classi": ["Chierico", "Paladino"],
        "descrizione": "Emani un'aura sacra di 9 m per 1 minuto: alleati ottengono vantaggio ai TS contro effetti malvagi, nemici di allineamento malvagio subiscono svantaggio agli attacchi contro di te."},
    "Camuffare Sé Stessi": {"livello": 3, "classi": ["Mago", "Bardo", "Stregone", "Warlock"],
        "descrizione": "Cambi il tuo aspetto (altezza, peso, lineamenti, voce) per 1 ora. Una creatura può investigare con prova di Intelligenza (Indagare) contro la tua CD per scoprire l'inganno."},
    "Animare Morti": {"livello": 3, "classi": ["Mago", "Chierico"],
        "descrizione": "Anima ossa o cadavere entro 3 m: crea uno scheletro o zombi sotto il tuo controllo per 24 ore (rituale di necromanzia, da usare con discrezione narrativa)."},
    "Tempesta di Spuntoni": {"livello": 3, "classi": ["Druido"],
        "descrizione": "Il terreno in un'area di 6 m si ricopre di spuntoni rocciosi: creature che vi entrano o iniziano il turno lì, TS Destrezza o 2d6 danni perforanti e terreno difficile."},
}

def incantesimi_per_classe(classe):
    disponibili = [nome for nome, dati in CATALOGO_INCANTESIMI.items() if classe in dati["classi"]]
    return sorted(disponibili, key=lambda n: CATALOGO_INCANTESIMI[n]["livello"])

def aggiorna_elenco_classe(classe):
    disponibili = incantesimi_per_classe(classe)
    valore_iniziale = disponibili[0] if disponibili else None
    return gr.update(choices=disponibili, value=valore_iniziale)

def mostra_descrizione_incantesimo(nome_incantesimo):
    if not nome_incantesimo or nome_incantesimo not in CATALOGO_INCANTESIMI:
        return "Seleziona un incantesimo per vederne la descrizione."
    dati = CATALOGO_INCANTESIMI[nome_incantesimo]
    livello_testo = "Trucchetto" if dati["livello"] == 0 else f"{dati['livello']}° livello"
    return f"**{nome_incantesimo}** ({livello_testo})\n\n{dati['descrizione']}"

def aggiungi_incantesimo_conosciuto(nome_incantesimo, lista_attuale):
    if not nome_incantesimo:
        return lista_attuale, lista_attuale, gr.update(choices=lista_attuale)
    if nome_incantesimo not in lista_attuale:
        lista_attuale = lista_attuale + [nome_incantesimo]
    return lista_attuale, lista_attuale, gr.update(choices=lista_attuale)

def rimuovi_incantesimo_conosciuto(nome_incantesimo, lista_attuale):
    if nome_incantesimo in lista_attuale:
        lista_attuale = [n for n in lista_attuale if n != nome_incantesimo]
    return lista_attuale, lista_attuale, gr.update(choices=lista_attuale)

def applica_danno(danno_subito, pf_attuali, pf_temporanei):
    danno_subito = int(danno_subito) if danno_subito else 0
    pf_attuali = int(pf_attuali) if pf_attuali else 0
    pf_temporanei = int(pf_temporanei) if pf_temporanei else 0
    if danno_subito <= 0:
        return pf_attuali, pf_temporanei, 0
    if pf_temporanei > 0:
        if danno_subito <= pf_temporanei:
            pf_temporanei -= danno_subito
            danno_subito = 0
        else:
            danno_subito -= pf_temporanei
            pf_temporanei = 0
    pf_attuali = max(pf_attuali - danno_subito, 0)
    return pf_attuali, pf_temporanei, 0

def applica_cura(cura_ricevuta, pf_attuali, pf_massimi):
    cura_ricevuta = int(cura_ricevuta) if cura_ricevuta else 0
    pf_attuali = int(pf_attuali) if pf_attuali else 0
    pf_massimi = int(pf_massimi) if pf_massimi else 0
    pf_attuali = min(pf_attuali + cura_ricevuta, pf_massimi)
    return pf_attuali, 0

# ============================================================
# CELLA 8 — Interfaccia completa
# ============================================================

with gr.Blocks(title="Scheda D&D Interattiva") as app:

    with gr.Tabs():

        # ============ TAB GESTIONE ============
        with gr.Tab("🛠️ Gestione"):
            gr.Markdown("# Gestione Scheda")
            with gr.Row():
                btn_salva = gr.Button("💾 Salva Scheda")
                file_output_salvataggio = gr.File(label="Scarica qui il file salvato", interactive=False)
                file_carica = gr.File(label="📂 Carica Scheda (.json)", file_types=[".json"])

            gr.Markdown("## Catalogo Mostri/PNG")
            with gr.Row():
                selettore_mostro = gr.Dropdown(label="Scegli un mostro/PNG", choices=list(CATALOGO_MOSTRI.keys()), value="Goblin")
                btn_aggiungi = gr.Button("➕ Aggiungi al Combattimento")
            with gr.Row():
                anteprima_ca = gr.Textbox(label="CA", interactive=False)
                anteprima_pf = gr.Textbox(label="PF Massimi", interactive=False)
                anteprima_velocita = gr.Textbox(label="Velocità", interactive=False)
                anteprima_gs = gr.Textbox(label="Grado Sfida", interactive=False)
            with gr.Row():
                anteprima_attacco = gr.Textbox(label="Attacco Principale", interactive=False)
                anteprima_note = gr.Textbox(label="Note/Abilità Speciali", interactive=False)

            gr.Markdown("## Combattimento Attivo")
            stato_combattimento = gr.State([])
            tabella_combattimento = gr.Dataframe(
                headers=["Nome", "CA", "PF Max", "PF Attuali", "GS"],
                datatype=["str", "number", "number", "number", "str"],
                row_count=(0, "dynamic"),
                column_count=(5, "fixed"),
                interactive=True
            )
            btn_svuota = gr.Button("🗑️ Svuota Combattimento")

        # ============ TAB PAGINA 1 ============
        with gr.Tab("📜 Pagina 1"):

            with gr.Row():
                nome = gr.Textbox(label="Nome Personaggio", value="", scale=2)
                razza = gr.Textbox(label="Razza", value="", scale=1)
                classe = gr.Dropdown(label="Classe & Livello", choices=["Barbaro", "Bardo", "Chierico", "Druido", "Guerriero", "Ladro", "Mago", "Monaco", "Paladino", "Ranger", "Stregone", "Warlock", "Altro"], value="Guerriero", allow_custom_value=True, scale=1)
                livello = gr.Number(label="Livello", value=1, minimum=1, maximum=20, precision=0, scale=1)
                background = gr.Textbox(label="Background", value="", scale=1)
                allineamento = gr.Textbox(label="Allineamento", value="", scale=1)

            with gr.Row():

                with gr.Column(scale=2, min_width=160):
                    gr.Markdown("### Caratteristiche")
                    with gr.Group():
                        forza = gr.Number(label="Forza", value=10, minimum=1, maximum=30, precision=0)
                        mod_for = gr.Textbox(label="Mod", value="+0", interactive=False)
                    with gr.Group():
                        destrezza = gr.Number(label="Destrezza", value=10, minimum=1, maximum=30, precision=0)
                        mod_des = gr.Textbox(label="Mod", value="+0", interactive=False)
                    with gr.Group():
                        costituzione = gr.Number(label="Costituzione", value=10, minimum=1, maximum=30, precision=0)
                        mod_cos = gr.Textbox(label="Mod", value="+0", interactive=False)
                    with gr.Group():
                        intelligenza = gr.Number(label="Intelligenza", value=10, minimum=1, maximum=30, precision=0)
                        mod_int = gr.Textbox(label="Mod", value="+0", interactive=False)
                    with gr.Group():
                        saggezza = gr.Number(label="Saggezza", value=10, minimum=1, maximum=30, precision=0)
                        mod_sag = gr.Textbox(label="Mod", value="+0", interactive=False)
                    with gr.Group():
                        carisma = gr.Number(label="Carisma", value=10, minimum=1, maximum=30, precision=0)
                        mod_car = gr.Textbox(label="Mod", value="+0", interactive=False)

                with gr.Column(scale=3, min_width=220):
                    gr.Markdown("### Combattimento")
                    with gr.Row():
                        bonus_competenza = gr.Textbox(label="Bonus Comp.", value="+2", interactive=False)
                        ispirazione = gr.Checkbox(label="Ispirazione", value=False)
                    with gr.Row():
                        ca = gr.Number(label="CA", value=10, precision=0)
                        iniziativa = gr.Textbox(label="Iniziativa", value="+0", interactive=False)
                        velocita_pg = gr.Textbox(label="Velocità", value="9 m")

                    gr.Markdown("**Punti Ferita**")
                    with gr.Row():
                        pf_massimi = gr.Number(label="PF Massimi", value=10, precision=0)
                        pf_attuali = gr.Number(label="PF Attuali", value=10, precision=0)
                        pf_temporanei = gr.Number(label="PF Temp.", value=0, precision=0)
                    with gr.Row():
                        danno_subito = gr.Number(label="Danno Subito", value=0, precision=0, minimum=0)
                        btn_applica_danno = gr.Button("⚔️ Applica Danno")
                    with gr.Row():
                        cura_ricevuta = gr.Number(label="Cura Ricevuta", value=0, precision=0, minimum=0)
                        btn_applica_cura = gr.Button("✨ Applica Cura")

                    with gr.Row():
                        dado_vita = gr.Textbox(label="Dado Vita", value="d10", interactive=False)

                    gr.Markdown("**Tiri Salvezza contro la Morte**")
                    with gr.Row():
                        ts_morte_successi = gr.CheckboxGroup(label="Successi", choices=["1", "2", "3"], value=[])
                        ts_morte_fallimenti = gr.CheckboxGroup(label="Fallimenti", choices=["1", "2", "3"], value=[])

                    gr.Markdown("### Tiri Salvezza")
                    with gr.Row():
                        comp_for = gr.Checkbox(label="FOR", value=False, scale=1)
                        salv_for = gr.Textbox(value="+0", interactive=False, scale=1, show_label=False)
                        comp_des = gr.Checkbox(label="DES", value=False, scale=1)
                        salv_des = gr.Textbox(value="+0", interactive=False, scale=1, show_label=False)
                    with gr.Row():
                        comp_cos = gr.Checkbox(label="COS", value=False, scale=1)
                        salv_cos = gr.Textbox(value="+0", interactive=False, scale=1, show_label=False)
                        comp_int = gr.Checkbox(label="INT", value=False, scale=1)
                        salv_int = gr.Textbox(value="+0", interactive=False, scale=1, show_label=False)
                    with gr.Row():
                        comp_sag = gr.Checkbox(label="SAG", value=False, scale=1)
                        salv_sag = gr.Textbox(value="+0", interactive=False, scale=1, show_label=False)
                        comp_car = gr.Checkbox(label="CAR", value=False, scale=1)
                        salv_car = gr.Textbox(value="+0", interactive=False, scale=1, show_label=False)

                with gr.Column(scale=3, min_width=220):
                    gr.Markdown("### Abilità")
                    campi_abilita = {}
                    campi_competenza_abilita = {}
                    for nome_abilita, carat in ABILITA.items():
                        with gr.Row():
                            comp = gr.Checkbox(label="", value=False, scale=0, min_width=30)
                            val = gr.Textbox(value="+0", interactive=False, scale=1, min_width=40, show_label=False)
                            campi_competenza_abilita[nome_abilita] = comp
                            campi_abilita[nome_abilita] = val
                            gr.Markdown(f"{nome_abilita} ({carat[:3].upper()})")

                    percezione_passiva = gr.Textbox(label="Saggezza (Percezione) Passiva", value="10", interactive=False)

            gr.Markdown("### Altre Competenze & Linguaggi")
            altre_competenze = gr.Textbox(label="", lines=3, show_label=False)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Attacchi & Incantesimi")
                    attacchi_testo = gr.Textbox(label="", lines=6, show_label=False, placeholder="Nome | Bonus Att. | Danni/Tipo")
                with gr.Column(scale=1):
                    gr.Markdown("### Equipaggiamento")
                    equipaggiamento = gr.Textbox(label="", lines=6, show_label=False)

            gr.Markdown("### Privilegi & Tratti")
            privilegi_tratti = gr.Textbox(label="", lines=4, show_label=False)

            gr.Markdown("## Anteprima dati scheda (debug)")
            output_json = gr.Textbox(label="Stato attuale", lines=6, interactive=False)

        # ============ TAB PAGINA 2 ============
        with gr.Tab("🎭 Pagina 2"):
            gr.Markdown("# Personalità & Storia")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Tratti Caratteriali")
                    tratti_caratteriali = gr.Textbox(label="", lines=4, show_label=False)
                with gr.Column():
                    gr.Markdown("### Ideali")
                    ideali = gr.Textbox(label="", lines=4, show_label=False)

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Legami")
                    legami = gr.Textbox(label="", lines=4, show_label=False)
                with gr.Column():
                    gr.Markdown("### Difetti")
                    difetti = gr.Textbox(label="", lines=4, show_label=False)

            gr.Markdown("### Aspetto")
            with gr.Row():
                eta = gr.Textbox(label="Età", scale=1)
                altezza = gr.Textbox(label="Altezza", scale=1)
                peso = gr.Textbox(label="Peso", scale=1)
                occhi = gr.Textbox(label="Occhi", scale=1)
                capelli = gr.Textbox(label="Capelli", scale=1)
                carnagione = gr.Textbox(label="Carnagione", scale=1)

            descrizione_aspetto = gr.Textbox(label="Descrizione Aspetto", lines=4)

            gr.Markdown("### Storia")
            storia_personaggio = gr.Textbox(label="", lines=6, show_label=False)

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Alleati & Organizzazioni")
                    alleati_organizzazioni = gr.Textbox(label="", lines=4, show_label=False)
                with gr.Column():
                    gr.Markdown("### Tesoro")
                    tesoro = gr.Textbox(label="", lines=4, show_label=False)

            gr.Markdown("### Tratti & Privilegi Aggiuntivi")
            tratti_privilegi_aggiuntivi = gr.Textbox(label="", lines=4, show_label=False)

        # ============ TAB PAGINA 3 ============
        with gr.Tab("✨ Pagina 3"):
            gr.Markdown("# Incantesimi")

            with gr.Row():
                caratteristica_incantatrice = gr.Textbox(label="Caratteristica da Incantatore", value="")
                cd_incantesimi = gr.Textbox(label="CD Tiro Salvezza Incantesimi", value="")
                bonus_attacco_incantesimi = gr.Textbox(label="Bonus di Attacco Incantesimi", value="")

            gr.Markdown("## Scegli un Incantesimo per la tua Classe")
            with gr.Row():
                selettore_incantesimo_classe = gr.Dropdown(label="Incantesimi disponibili per la tua classe", choices=[], scale=2)
                btn_aggiungi_incantesimo = gr.Button("➕ Aggiungi a Conosciuti")

            descrizione_incantesimo_anteprima = gr.Markdown("Seleziona un incantesimo per vederne la descrizione.")

            gr.Markdown("## Incantesimi Conosciuti")
            stato_incantesimi_conosciuti = gr.State([])
            with gr.Row():
                lista_incantesimi_conosciuti = gr.Dropdown(label="I tuoi incantesimi", choices=[], scale=2)
                btn_rimuovi_incantesimo = gr.Button("🗑️ Rimuovi")
            descrizione_incantesimo_conosciuto = gr.Markdown("Qui vedrai la descrizione dell'incantesimo selezionato dalla tua lista.")

            gr.Markdown("## Slot Incantesimo")
            slot_incantesimo_display = gr.Textbox(label="Slot Disponibili per Livello", value="", interactive=False)

    # ================= COLLEGAMENTI EVENTI =================

    input_caratteristiche = [forza, destrezza, costituzione, intelligenza, saggezza, carisma]
    output_modificatori = [mod_for, mod_des, mod_cos, mod_int, mod_sag, mod_car]
    input_competenze_salvezza = [comp_for, comp_des, comp_cos, comp_int, comp_sag, comp_car]
    output_salvezze = [salv_for, salv_des, salv_cos, salv_int, salv_sag, salv_car]
    input_competenze_abilita = list(campi_competenza_abilita.values())
    output_abilita = list(campi_abilita.values())

    for campo in input_caratteristiche:
        campo.change(show_progress="hidden", fn=aggiorna_modificatori, inputs=input_caratteristiche, outputs=output_modificatori)

    livello.change(show_progress="hidden", fn=aggiorna_bonus_competenza_display, inputs=livello, outputs=bonus_competenza)

    for campo in [livello] + input_caratteristiche + input_competenze_salvezza:
        campo.change(show_progress="hidden", fn=aggiorna_salvezze,
            inputs=[livello] + input_caratteristiche + input_competenze_salvezza,
            outputs=output_salvezze)

    for campo in [livello] + input_caratteristiche + input_competenze_abilita:
        campo.change(show_progress="hidden", fn=aggiorna_abilita,
            inputs=[livello] + input_caratteristiche + input_competenze_abilita,
            outputs=output_abilita)

    dado_vita_slot_dummy = gr.Textbox(visible=False)
    for campo in [classe, livello, costituzione]:
        campo.change(show_progress="hidden", fn=aggiorna_progressione_classe,
            inputs=[classe, livello, costituzione],
            outputs=[dado_vita, pf_massimi, dado_vita_slot_dummy])

    destrezza.change(show_progress="hidden", fn=lambda d: formatta_modificatore(calcola_modificatore(d)), inputs=destrezza, outputs=iniziativa)

    def aggiorna_percezione_passiva(saggezza, comp_percezione):
        mod = calcola_modificatore(saggezza)
        return str(10 + mod)
    saggezza.change(show_progress="hidden", fn=aggiorna_percezione_passiva, inputs=[saggezza, campi_competenza_abilita["Percezione"]], outputs=percezione_passiva)
    campi_competenza_abilita["Percezione"].change(show_progress="hidden", fn=aggiorna_percezione_passiva, inputs=[saggezza, campi_competenza_abilita["Percezione"]], outputs=percezione_passiva)

    tutti_i_campi = [nome, razza, classe, background, livello] + input_caratteristiche
    for campo in tutti_i_campi:
        campo.change(show_progress="hidden", fn=raccogli_stato_scheda, inputs=tutti_i_campi, outputs=output_json)

    campi_salvataggio = ([nome, razza, classe, background, livello] + input_caratteristiche +
        [pf_massimi, pf_attuali] + input_competenze_salvezza + input_competenze_abilita)
    btn_salva.click(show_progress="hidden", fn=salva_scheda_completa, inputs=campi_salvataggio, outputs=file_output_salvataggio)
    file_carica.upload(show_progress="hidden", fn=carica_scheda_da_file, inputs=file_carica, outputs=campi_salvataggio)

    selettore_mostro.change(show_progress="hidden", fn=carica_dati_mostro, inputs=selettore_mostro,
        outputs=[anteprima_ca, anteprima_pf, anteprima_velocita, anteprima_gs, anteprima_attacco, anteprima_note])
    btn_aggiungi.click(show_progress="hidden", fn=aggiungi_al_combattimento, inputs=[selettore_mostro, stato_combattimento],
        outputs=[stato_combattimento, tabella_combattimento])
    btn_svuota.click(show_progress="hidden", fn=svuota_combattimento, inputs=None, outputs=[stato_combattimento, tabella_combattimento])

    # --- TRACKER DANNI E CURE ---
    btn_applica_danno.click(
        show_progress="hidden",
        fn=applica_danno,
        inputs=[danno_subito, pf_attuali, pf_temporanei],
        outputs=[pf_attuali, pf_temporanei, danno_subito]
    )
    btn_applica_cura.click(
        show_progress="hidden",
        fn=applica_cura,
        inputs=[cura_ricevuta, pf_attuali, pf_massimi],
        outputs=[pf_attuali, cura_ricevuta]
    )

    # --- EVENTI PAGINA 3: INCANTESIMI ---
    classe.change(show_progress="hidden", fn=aggiorna_elenco_classe, inputs=classe, outputs=selettore_incantesimo_classe)
    selettore_incantesimo_classe.change(show_progress="hidden", fn=mostra_descrizione_incantesimo, inputs=selettore_incantesimo_classe, outputs=descrizione_incantesimo_anteprima)

    btn_aggiungi_incantesimo.click(
        show_progress="hidden",
        fn=aggiungi_incantesimo_conosciuto,
        inputs=[selettore_incantesimo_classe, stato_incantesimi_conosciuti],
        outputs=[stato_incantesimi_conosciuti, stato_incantesimi_conosciuti, lista_incantesimi_conosciuti]
    )
    btn_rimuovi_incantesimo.click(
        show_progress="hidden",
        fn=rimuovi_incantesimo_conosciuto,
        inputs=[lista_incantesimi_conosciuti, stato_incantesimi_conosciuti],
        outputs=[stato_incantesimi_conosciuti, stato_incantesimi_conosciuti, lista_incantesimi_conosciuti]
    )
    lista_incantesimi_conosciuti.change(show_progress="hidden", fn=mostra_descrizione_incantesimo, inputs=lista_incantesimi_conosciuti, outputs=descrizione_incantesimo_conosciuto)

    classe.change(show_progress="hidden", fn=lambda c, l: calcola_slot_incantesimo(c, int(l)), inputs=[classe, livello], outputs=slot_incantesimo_display)
    livello.change(show_progress="hidden", fn=lambda c, l: calcola_slot_incantesimo(c, int(l)), inputs=[classe, livello], outputs=slot_incantesimo_display)


if __name__ == "__main__":
    app.launch(css=CSS_PERGAMENA)
