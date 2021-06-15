from sympy.solvers import solve
from sympy import Symbol
import numpy as np

p1_strats = ["Smoke ", 
             "Barrel"]

p1_payoff = np.array([[-5,25],
                      [0,10]])


p2_strats = ["Lock ", "Stock"]

p2_payoff = np.array([[-5,0],
                      [15,10]])

p = Symbol('p')
q = Symbol('q')

print(f"P1 playes '{p1_strats[0]}' with propability p and '{p1_strats[1]}' with propability 1-p")
print(f"P2 playes '{p2_strats[0]}' with propability q and {p2_strats[1]}' with propability 1-q")
print()
for i in range(len(p1_payoff)):
    print(f"E(U1({p1_strats[i]}, q)) = {p1_payoff[i][0]} * q + {p1_payoff[i][1]} * (1-q)")

print(f"E(U1({p1_strats[0]}, q)) =E(U1({p1_strats[1]}, q))")
q_star = solve(p1_payoff[0][0] * q + p1_payoff[0][1] * (1-q) - (p1_payoff[1][0] * q + p1_payoff[1][1] * (1-q)),q)
print(f"==> q*= {q_star}")
print()
for i in range(len(p2_payoff)):
    print(f"E(U2({p2_strats[i]})) = {p2_payoff[0][i]} * p + {p2_payoff[1][i]} * (p-1)")

print(f"E(U1({p2_strats[0]}, p)) =E(U1({p2_strats[1]}, p))")
p_star = solve(p2_payoff[0][0] * p + p2_payoff[1][0] * (1-p) - (p2_payoff[0][1] * p + p2_payoff[1][1] * (1-p)),p)
print(f"==> p*= {p_star}")

print(f"Mixed strategy(p*={p_star}, q*={q_star})")