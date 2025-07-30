# C0S3 D4 F4R3
Questi sono obiettivi iniziali che ho definito per chiarire meglio l'ambito del progetto. Naturalmente, potranno essere modificati, rimossi, aggiunti, arricchiti o riorganizzati in base alle esigenze future.

## Test
- [ ] Non completato
- [X] Completato

## Traccia del Progetto
- [ ] Definire lo schema del sistema reale (distinto da quello della simulazione).
    In partica quello che stava sul pdf che abbiamo fatto vedere la seconda volta che ci abbiamo parlato.
- [ ] Analizzare il transitorio e decidere tra orizzonte di simulazione finito o infinito.
    Guardare https://github.com/GRonz00/
    Effettuare l'analisi del transitorio su un giorno fissato
- [ ] Definire l'obiettivo finale della simulazione ad hoc.
## Requisiti Generali
- [ ] Definire i dati e le metriche da produrre al termine della simulazione.
    penso tempi di attesa e numeri nelle code
- [ ] Specificare quali stati e informazioni delle entità (richieste/persone) salvare durante il passaggio nei blocchi del sistema.
## Decisioni Implementative
- [ ] Implementare le distribuzioni di probabilità in modo che ognuna utilizzi uno stream RNG dedicato (per garantire la replicabilità degli esperimenti, es. gli arrivi, anche modificando la struttura del modello).
- [ ] Decidere se salvare i dati grezzi durante la simulazione per un'elaborazione posticipata, o elaborarli man mano che vengono prodotti.
    Salvare ogni giorno tutte le medie
- [ ] Scegliere un formato di salvataggio dati efficiente (es. per 20M di entità, JSON occupa ~10GB, formati binari come Parquet/Pickle ~1-5GB).
- [ ] Creare file di configurazione per i parametri dei blocchi (es. nome, tassi di servizio), da sviluppare parallelamente ai blocchi stessi, questo per rendere piu semplice la configurazione del sistema.
 

## Sviluppo
- [ ] Implementare il modello di simulazione completo.
- [ ] Implementare tutti i blocchi funzionali della simulazione.
- [ ] Implementare i diversi stati delle entità.
- [ ] Implementare un meccanismo di generazione utenti con tasso di arrivo variabile nel tempo.
- [ ] Creare degli script in python per produrre grafici sui dati ottenuti 

## Documentazione
(non serve in verita niente di tutto questo, ma per non lasciare la sezione vuota ora ho aggiunto qualcosa)
- [ ] Scrivere la documentazione utente e sviluppatore.
- [ ] Generare la documentazione API aggiornata con Sphinx.



_____________________________________________________________

Modificare sta cosa del tasso di arrivo in modo che sia dinamico:
- inizia con array di mesi
- creare un array di dimensione dei giorni da simulare.
- quando genero l'utente guardo la data di generazione, se siamo quando genero in start