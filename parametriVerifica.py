gammaArrival=0.15



print(gammaArrival)
pa=0.96 # probabilita del successo della richiesta
pf=0.04 # probabilita di fallimento del login

pn=0.15 # probabilita di di falliemnto della complilazione

pd=0.22 # probabilita di richiesta diretta
pc=1-pd



def getExponentialToeoreticalWaitTime(ro: float,serviceTIme) -> float:
        return (ro*serviceTIme)/((1-ro)*2)

from sympy import *
from sympy.solvers.solveset import linsolve

lambda1,lambda2,lambda3,lambda4,lambda5= symbols('lambda1, lambda2, lambda3, lambda4, lambda5')

equation1 = Eq(lambda1, gammaArrival + (1-pa)*lambda5 + lambda2*pf)
equation2 = Eq(lambda2, lambda1)
equation3 = Eq(lambda3, lambda2*(1-pf)*pc + lambda3*pn)
equation4 = Eq(lambda4, lambda2*(1-pf)*pd)
equation5 = Eq(lambda5, lambda3*(1-pn) + lambda4)



output = solve([equation1,equation2,equation3,equation4,equation5],dict=True)

lambda1=output[0][lambda1]
lambda2=output[0][lambda2]   
lambda3=output[0][lambda3]
lambda4=output[0][lambda4]
lambda5=output[0][lambda5]


