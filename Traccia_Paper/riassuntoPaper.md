# 📄 MANET Simulation Studies: The Incredibles

**Autori**: Stuart Kurkowski, Tracy Camp, Michael Colagrosso  
**Conferenza**: ACM MobiHoc (2000–2005)  
**Titolo originale**: *MANET Simulation Studies: The Incredibles*  

---

## 🎯 Obiettivo

Valutare la **credibilità** e l'affidabilità degli studi di simulazione nelle reti ad hoc mobili (MANET), concentrandosi su 4 criteri fondamentali:

1. **Ripetibilità**
2. **Imparzialità**
3. **Rigore metodologico**
4. **Solidità statistica**

---

## 🔍 Metodo

Analisi di **151 articoli** pubblicati in MobiHoc (2000–2005).  
- **114** usano simulazioni (75.5%)
- **0** dichiarano la disponibilità del codice
- Solo **8 su 114** (7%) affrontano il bias di inizializzazione
- **0** menzionano il PRNG (Pseudo-Random Number Generator) utilizzato
- Solo **14 su 112** mostrano **intervalli di confidenza**

---

## ⚠️ Problemi principali

### 🟥 1. Mancanza di ripetibilità
- 30% non specifica nemmeno il simulatore
- Nessun paper rende disponibili i file di configurazione o il codice
- Versione del simulatore raramente indicata

### 🟨 2. Studi non imparziali
- Uso di un solo scenario
- Parametri importanti spesso omessi (es. traffico, range, area)

### 🟧 3. Mancanza di rigore
- Scenari troppo semplici (es. hop-count < 2)
- Nessuna definizione chiara delle variabili
- Nessuna verifica della correttezza del modello o codice

### 🟦 4. Debolezza statistica
- Poche simulazioni replicate
- Statistiche calcolate senza verifica iid
- Intervalli di confidenza quasi sempre assenti

---

## ❌ Errori comuni (Simulation Pitfalls)

### 🔧 Setup
- Tipo di simulazione non dichiarato (terminante vs steady-state)
- PRNG non validato
- Parametri lasciati a default (es. `transmission_range`)

### 🧪 Esecuzione
- Seed non impostato → run identici
- Nessuna gestione del bias iniziale
- Dati output non sufficienti o mal etichettati

### 📊 Analisi output
- Uso di un solo run → campione non rappresentativo
- Nessun metodo batch/replica
- Mancanza di confidenza nei risultati

### 📰 Pubblicazione
- Grafici senza unità/legende
- Parametri fondamentali non documentati
- Nessun link al codice o file `.tcl`

---

## 🧰 Strumenti raccomandati

- **Akaroa-2**: monitoraggio stato stazionario, PRNG robusto
- **iNSpect**: visualizzatore per NS-2
- **SWAN**: simulazione MANET interattiva
- **SCORES** *(in sviluppo)*: verifica rigore degli scenari

---

## ✅ Conclusioni

- **< 15%** degli studi è davvero **ripetibile**
- Solo **12%** usa metodi **statistici robusti**
- La maggior parte degli studi è vulnerabile a:
  - bias,
  - errori metodologici,
  - risultati non confrontabili.

---

## 📌 Raccomandazione

È necessaria una maggiore:
- **trasparenza nella pubblicazione**,
- **rigorosità nella simulazione**,
- **diffusione di strumenti** per aiutare nuovi ricercatori.

---
