# 🔢 ALGORITMO 1.1.1 – I 6 PASSAGGI

### (1) **Definizione degli obiettivi**

Capire cosa si vuole ottenere dalla simulazione.

- Esempio: "Quanti tecnici assumere per massimizzare il profitto?"
- Gli obiettivi devono essere chiari e misurabili, altrimenti la simulazione non ha senso.

---

### (2) **Costruzione del modello concettuale**

Descrivere logicamente il sistema:

- Quali sono le **variabili di stato**? (es: "Macchina guasta o operativa", "Tecnico occupato o libero")
- Quali sono **rilevanti** e quali si possono ignorare?
- Non è ancora codice, ma una **mappa mentale del sistema**.

---

### (3) **Costruzione del modello di specifica**

Qui si raccolgono **dati reali o ipotesi statistiche** per quantificare il modello:

- Quanto spesso si guasta una macchina?
- Quanto dura una riparazione?
- Se non ho dati, posso usare modelli stocastici (es. distribuzioni esponenziali)
- Questa fase è **cruciale**: se fatta male, il resto è tempo sprecato.

---

### (4) **Implementazione del modello computazionale**

Si scrive il programma vero e proprio:

- Uso di un linguaggio generico (Python, Java…) o uno specifico per simulazione (SimPy, Arena…)
- Strutture comuni: **orologio della simulazione**, **code di eventi**, **statistiche raccolte**

---

### (5) **Verifica**

Controllo che il **programma** sia corretto rispetto alla **specifica tecnica**.

- "Abbiamo scritto bene il codice?"
- Non vuol dire ancora che il modello sia "giusto", solo che **fa ciò che deve fare**

---

### (6) **Validazione**

Controllo che il **modello simulato rappresenti davvero il sistema reale**.

- "Abbiamo modellato il sistema giusto?"
- Se aumento i tecnici, le macchine guaste devono diminuire: ha senso?
- Se il sistema esiste, si può **confrontare con dati reali**
- Se non esiste, si fanno **check di coerenza** e si usano esperti

---

# 🏭 ESEMPIO: Officina meccanica

### Scenario:

- 150 macchine → producono $20/h → lavorano 8h/die, 250 giorni l’anno  
- Quando si guastano, vengono riparate da tecnici  
- I tecnici costano $52,000/anno e lavorano 230 giorni  
- Ogni macchina è **indipendente**, ma i tecnici sono **in coda**: chi si libera, serve la prossima  
- **Domanda**: quanti tecnici assumere per massimizzare il profitto?

---

### Applicazione dei 6 step:

1. **Obiettivo**:  
   - Massimizzare il profitto totale nel tempo  
   - Bilanciare:  
     - **Reddito** dalle macchine operative  
     - **Costo** dei tecnici  

2. **Modello concettuale**:  
   - Stato delle macchine: "guasta" o "operativa"  
   - Stato dei tecnici: "occupato" o "disponibile"  
   - Modello a eventi: guasti, riparazioni, turni  

3. **Modello di specifica**:  
   - Distribuzione del tempo tra guasti  
   - Distribuzione del tempo di riparazione  
   - In assenza di dati reali → uso di distribuzioni ipotetiche (es. esponenziale)  

4. **Modello computazionale**:  
   - Codice con simulazione a eventi discreti  
   - Orologio simulazione, coda eventi, raccolta di statistiche  
   - Metriche: profitto netto, tempo medio di fermo, utilizzo tecnici  

5. **Verifica**:  
   - Il programma rispecchia il modello concettuale?
   - Esempio: i guasti vengono serviti nell’ordine corretto?

6. **Validazione**:  
   - Se esiste una versione reale del sistema → confronto diretto  
   - Altrimenti → controlli di coerenza  
   - Es: più tecnici = meno guasti in coda = più uptime  

---

## 🧭 COSA SI STA DESCRIVENDO?

Viene mostrato **come progettare e costruire correttamente una simulazione a eventi discreti**.  
Questi tipi di simulazioni si usano per rappresentare **sistemi in cui gli stati cambiano solo in certi momenti precisi nel tempo**, come ad esempio:

- Arrivo di un cliente in coda  
- Guasto o riparazione di una macchina  
- Spedizione di un prodotto  

---

## 🧠 Conclusione

> Questo processo a 6 step è la **base metodologica per costruire una simulazione a eventi discreti solida e credibile**.

Ogni passo serve a garantire:
- che il modello risponda alle domande giuste
- che sia corretto
- e che i risultati siano **attendibili e interpretabili**


____________________________________________________________________________________________________________________________________________________________________
____________________________________________________________________________________________________________________________________________________________________
____________________________________________________________________________________________________________________________________________________________________
____________________________________________________________________________________________________________________________________________________________________



# 🔁 Algorithm 1.1.2 – Uso del modello simulativo

Una volta completato il processo di sviluppo del modello (vedi Algorithm 1.1.1), è il momento di **usare il modello per fare esperimenti, analizzare i risultati e prendere decisioni**. Questo processo comprende i seguenti passaggi:

---

## (7) **Progettare gli esperimenti di simulazione**

- Definire quali **parametri variare** e con quali valori.
- Se i parametri sono molti, le **combinazioni esplodono** → serve un disegno degli esperimenti ben strutturato (DOE).
- Esempi di parametri: numero di tecnici, politica di riparazione, tempo medio di guasto, ecc.

---

## (8) **Eseguire i run di produzione**

- Ogni run deve essere fatto **in modo sistematico**, registrando:
  - le **condizioni iniziali**
  - i **parametri in input**
  - e l’**output statistico**
- Evita di salvare "dati grezzi" troppo dettagliati (es. ogni singolo evento) → consumano molto spazio e possono sempre essere **ricreati**.

---

## (9) **Analizzare i risultati**

- La simulazione produce output **stocastico**, quindi l’analisi deve essere **statistica**.
- Le osservazioni sono spesso **correlate temporalmente**, quindi:
  - non usare formule classiche per media/varianza **senza verificare indipendenza**
  - usa tecniche come **batch means**, **repliche indipendenti**, **intervalli di confidenza**
- Esempi di strumenti: media, deviazione standard, istogrammi, percentili, correlazioni.

---

## (10) **Prendere decisioni**

- I risultati devono portare a **decisioni operative**.
- Es: il grafico "profitto vs numero tecnici" mostra:
  - la soluzione ottima
  - quanto il sistema è sensibile a variazioni
- La validità del modello si rafforza se le previsioni si verificano dopo l’implementazione.

---

## (11) **Documentare i risultati**

- Se hai ottenuto insight: **scrivili chiaramente** (osservazioni, ipotesi, conclusioni).
- Se **non** hai ottenuto insight: analizza **perché**.
- Una buona documentazione include:
  - Diagramma del sistema
  - Ipotesi su guasti e riparazioni
  - Modello di specifica
  - Codice usato
  - Tabelle e grafici dei risultati
  - Descrizione dell’analisi statistica

---

# 🏭 ESEMPIO 1.1.2 – Officina meccanica (continuazione)

### (7) Progettare esperimenti

- Variare il **numero di tecnici** per trovare il profitto massimo
- Definire **condizioni iniziali**: es. tutte le macchine partono operative?
- Per ogni configurazione, fare **più repliche** per ridurre la variabilità stocastica

---

### (8) Eseguire i run

- Evitare di archiviare ogni singolo guasto o riparazione
- L’**abilità di rigenerare i dati** è un punto di forza della simulazione

---

### (9) Analizzare risultati

- Se si osserva il numero di macchine guaste ogni ora → i dati saranno **correlati**
- L’analisi va fatta con attenzione → evitare assunzioni di indipendenza

---

### (10) Prendere decisioni

- Il grafico **profitto vs numero tecnici** aiuta a:
  - Identificare l’**ottimo**
  - Valutare quanto sia "robusta" la soluzione
- Una volta deciso, si può implementare la politica, salvo vincoli esterni

---

### (11) Documentare

- Inserire: schema del sistema, assunzioni, codice, risultati, interpretazioni
- Una buona documentazione rende più facile:
  - Riutilizzare il modello
  - Migliorarlo in futuro
  - Evitare errori già commessi

---
