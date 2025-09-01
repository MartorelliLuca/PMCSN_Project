gammaArrival=0.184992

giorniDiarrivi=143
giorniAfterArrivi=20


giorniTotali=giorniDiarrivi+giorniAfterArrivi

gammaArrival=gammaArrival*(giorniDiarrivi/giorniTotali)
print(gammaArrival)
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

lambda5=output[0][lambda5]

dipendenti=200
pratiche=70
totale=dipendenti*pratiche

lambdaPerPerson=lambda5/totale

print((1/lambdaPerPerson)/(60*60))
print(1/lambdaPerPerson)

print(output)