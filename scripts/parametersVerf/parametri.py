gammaArrival=0.184992

giorniDiarrivi=143
giorniAfterArrivi=20


giorniTotali=giorniDiarrivi+giorniAfterArrivi

gammaArrival=gammaArrival*(giorniDiarrivi/giorniTotali)
print(gammaArrival)
#0.16229359509202454
#la parte sopra per la parte di verifica puo essere scelta in modo arbritario, io ho scelto il gammma medio che abbiamo e aggiunto 30 giorni di labda 0 



pa=0.96 # probabilita del successo della richiesta
pf=0.04 # probabilita di fallimento del login

pn=0.15 # probabilita di di falliemnto della complilazione

pd=0.22 # probabilita di richiesta diretta
pc=1-pd



from sympy import *
from sympy.solvers.solveset import linsolve

lambda1,lambda2,lambda3,lambda4,lambda5= symbols('lambda1, lambda2, lambda3, lambda4, lambda5')

equation1 = Eq(lambda1, gammaArrival + (1-pa)*lambda5 + lambda2*pf)
equation2 = Eq(lambda2, lambda1)
equation3 = Eq(lambda3, lambda2*(1-pf)*pc + lambda3*pn)
equation4 = Eq(lambda4, lambda2*(1-pf)*pd)
equation5 = Eq(lambda5, lambda3*(1-pn) + lambda4)


output = solve([equation1,equation2,equation3,equation4,equation5],dict=True)

#lambdaMedia=0.16229359509202454

lambda1=output[0][lambda1]
lambda2=output[0][lambda2]
lambda3=output[0][lambda3]
lambda4=output[0][lambda4]
lambda5=output[0][lambda5]
#[lambda1:0.176099821063395, lambda2:0.176099821063395, lambda3:0.155133583543847, lambda4:0.0371922822085891, lambda5:0.169055828220859]
print(f"[lambda1:{lambda1}, lambda2:{lambda2}, lambda3:{lambda3}, lambda4:{lambda4}, lambda5:{lambda5}]")

mu1=lambda1*1.5
mu2=lambda2*1.5
mu3=lambda3*1.5
mu4=lambda4*1.5
mu5=lambda5*1.5
#[mu1:0.264149731595093, mu2:0.264149731595093, mu3:0.232700375315771, mu4:0.0557884233128836, mu5:0.253583742331289]


print(f"[mu1:{mu1}, mu2:{mu2}, mu3:{mu3}, mu4:{mu4}, mu5:{mu5}]")



#[s1:3.78573165288265, s2:3.78573165288265, s3:4.29737166793571, s4:17.9248657806944, s5:3.94347047175277]
print(f"[s1:{1/mu1}, s2:{1/mu2}, s3:{1/mu3}, s4:{1/mu4}, s5:{1/mu5}]")
#Per semplicita utilizzo tutti i centri con 1 servente



tq1=lambda1/((mu1-lambda1)*mu1)
tq2=lambda2/((mu2-lambda2)*mu2)
tq3=lambda3/((mu3-lambda3)*mu3)
tq4=lambda4/((mu4-lambda4)*mu4)
tq5=lambda5/((mu5-lambda5)*mu5)

#[tq1:7.57146330576531, tq2:7.57146330576531, tq3:8.59474333587141, tq4:35.8497315613888, tq5:7.88694094350553]
print(f"[tq1:{tq1}, tq2:{tq2}, tq3:{tq3}, tq4:{tq4}, tq5:{tq5}]")

r1=1/mu1+tq1
r2=1/mu2+tq2        
r3=1/mu3+tq3
r4=1/mu4+tq4
r5=1/mu5+tq5
#[r1:11.3571949586480, r2:11.3571949586480, r3:12.8921150038071, r4:53.7745973420831, r5:11.8304114152583]
print(f"[r1:{r1}, r2:{r2}, r3:{r3}, r4:{r4}, r5:{r5}]")


#simula con  i parametri di alpha e mu calcolati sopra, leggo il file json per caricare i dati
#SIMULARE CON LA VERSIONE CON TUTTE LE CODE EXPONENZIALI

import json

def read_daily_stats(filename):
    """
    Reads a json-lines file, skips the first line, and returns a list of dicts for each daily summary.
    """
    rows = []
    with open(filename, 'r') as f:
        first = True
        for line in f:
            if first:
                first = False
                continue  # skip metadata
            if line.strip():
                rows.append(json.loads(line))
    return rows


centers=["Autenticazione","Instradamento","CompilazionePrecompilata","InvioDiretto","InValutazione"]

data=read_daily_stats("src/transient_analysis_json/daily_stats.json")


centersData={center:{
    "queue_time": [],
    "executing_time": [],
    "visits": []
} for center in centers}

for row in data:
    stats=row["stats"]
    for center in centers:    
        centersData[center]["queue_time"].append(stats[center]["queue_time"])
        centersData[center]["executing_time"].append(stats[center]["executing_time"])
        centersData[center]["visits"].append(stats[center]["visited"])


for center in centers:
    qt=centersData[center]["queue_time"]
    et=centersData[center]["executing_time"]
    v=centersData[center]["visits"]
    mean_qt=sum(qt)/len(qt)
    mean_et=sum(et)/len(et)
    mean_v=sum(v)/len(v)
    centersData[center]["queue_time"]=mean_qt
    centersData[center]["executing_time"]=mean_et
    centersData[center]["visits"]=mean_v

#print(centersData)

mapping={"Autenticazione":(lambda1,mu1,tq1,r1), 
         "Instradamento":(lambda2,mu2,tq2,r2), 
         "CompilazionePrecompilata":(lambda3,mu3,tq3,r3), 
         "InvioDiretto":(lambda4,mu4,tq4,r4), 
         "InValutazione":(lambda5,mu5,tq5,r5)}
for center in centers:
    theo_lambda,theo_mu,theo_tq,theo_r=mapping[center]
    sim_lambda=centersData[center]["visits"]/(24*60*60)
    sim_tq=centersData[center]["queue_time"]
    sim_s=centersData[center]["executing_time"]
    print(f"\n{center}")
    def pretty_stat(name, theo, sim):
        error = abs(sim - theo) / abs(theo) if theo != 0 else 0
        tick = '\u2705' if error <= 0.05 else ''
        print(f"  {name}: theo={theo:.5f}, sim={sim:.5f}  {tick}")
    pretty_stat("lambda", theo_lambda, sim_lambda)
    pretty_stat("tq", theo_tq, sim_tq)
    pretty_stat("s", 1/theo_mu, sim_s)


    """
Autenticazione
  lambda: theo=0.17610, sim=0.17590  ✅
  tq: theo=7.57146, sim=7.50732  ✅
  s: theo=3.78573, sim=3.78376  ✅

Instradamento
  lambda: theo=0.17610, sim=0.17590  ✅
  tq: theo=7.57146, sim=7.48230  ✅
  s: theo=3.78573, sim=3.78696  ✅

CompilazionePrecompilata
  lambda: theo=0.15513, sim=0.15504  ✅
  tq: theo=8.59474, sim=8.63456  ✅
  s: theo=4.29737, sim=4.29475  ✅

InvioDiretto
  lambda: theo=0.03719, sim=0.03727  ✅
  tq: theo=35.84973, sim=35.69820  ✅
  s: theo=17.92487, sim=17.94613  ✅

InValutazione
  lambda: theo=0.16906, sim=0.16894  ✅
  tq: theo=7.88694, sim=7.77659  ✅
  s: theo=3.94347, sim=3.94402  ✅
    """