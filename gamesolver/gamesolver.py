import flask
import json
import numpy as np
import sympy as sp
app = flask.Flask(__name__)
app.secret_key = "secret43"

def get_mixed_strategy_equilibria(astrats, bstrats, adoms, bdoms):
    # Start for p1 is going to be ascii 97 which is a
    # Start for p2 is going to be ascii 65 which is A
    # Both leave room for 26 letters :) nobody is going to fill in a 26x26 matrix
    #Step 1: Define variables:
    
    width = flask.session.get("width")
    height = flask.session.get("height") 
    p1_vars = []
    for i in range(height-1):
        if i in adoms:
            continue
        random_symbol = chr(97+i)
        p1_vars.append(sp.Symbol(random_symbol))

    p2_vars = []
    for i in range(width-1):
        if i in bdoms:
            continue
        random_symbol = chr(65+i)
        p2_vars.append(sp.Symbol(random_symbol))
    
    # Start generating the expressiones for strategies of player one
    p1_utilities = []
    for y in range(height):
        if y in adoms:
            continue
        terms = []
        x_index = 0
        for x in range(width):
            if x in bdoms:
                continue
            term = ""
            if x < width-1:
                term = f"{astrats[x][y]} * {p2_vars[x_index]}"
                x_index += 1
            else:
                if len(p2_vars) < 1:
                    term = f"{astrats[x][y]}"
                else:
                    term = f"{astrats[x][y]} * (1-({' + '.join([str(v) for v in p2_vars])}))"
            terms.append(term)
        p1_utilities.append(sp.sympify(" + ".join(terms)))

    p2_utilities = []
    for x in range(width):
        if x in bdoms:
            continue
        terms = []
        y_index = 0
        for y in range(height):
            if y in adoms:
                continue
            term = ""
            if y < height-1:
                term = f"{bstrats[x][y]} * {p1_vars[y_index]}"
                y_index += 1
            else:
                if len(p1_vars) < 1:
                    term = f"{bstrats[x][y]}"
                else:
                    term = f"{bstrats[x][y]} * (1-({' + '.join([str(v) for v in p1_vars])}))"
            terms.append(term)
        p2_utilities.append(sp.sympify(" + ".join(terms)))

    p1_equations = []
    for i in range(len(p1_utilities)-1):
        p1_equations.append(sp.Eq(p1_utilities[i], p1_utilities[i+1]))

    #Let's try using all equations and all vars to solve
    p2_equations = []
    for i in range(len(p2_utilities)-1):
        p2_equations.append(sp.Eq(p2_utilities[i], p2_utilities[i+1]))

    print(p1_equations)
    print(p2_equations)

    #Now let's extend the arrays with the new values
    #p1_equations.extend(p2_equations)
    #p1_vars.extend(p2_vars)
    p1_solutions = sp.solve(p1_equations, p2_vars)
    p2_solutions = sp.solve(p2_equations, p1_vars)
    solution_text = []
    solution_text.append("### Believs of Player1:")
    for variable in  p1_vars:
        value = "0 (unknown)"
        if variable in p2_solutions:
            value = p2_solutions[variable]
        solution_text.append(f"{variable} = {value}")
    solution_text.append("### Believs of Player2:")
    for variable in p2_vars:
        value = "0 (unknown)"
        if variable in p1_solutions:
            value = p1_solutions[variable]
        solution_text.append(f"{variable} = {value}")
    flask.session["mixed_strategies"] = solution_text

    
def get_dominations(payoffs, dom_strats, dom_strats_opponent, player, strict=True):
    """
    returns a list of tuples, each tuple contains the index of a dominated strategy and it's dominator
    """
    dominations = []
    
    if player == 1:
        payoffs = payoffs.T

    for y, strategy in enumerate(payoffs):
        if y in dom_strats:
            continue
        for y_, competing_strat in enumerate(payoffs):
            if y == y_ or y_ in dom_strats:
                continue

            dom = True
            for x, _ in enumerate(payoffs[y_]):
                if x in dom_strats_opponent:
                    continue
                
                if strict: #Hope this is right :0
                    if payoffs[y, x] >= payoffs[y_, x]:
                        dom = False
                else:
                    if payoffs[y, x] > payoffs[y_, x]:
                        dom = False

            if sum(strategy) == sum(competing_strat): #make shure that equal strategies don't dominate each other
                dom = False

            if dom:            
                dominations.append((y, y_)) # y gets dominated by y_

    return dominations


@app.route("/readMatrix", methods=["POST"])
def web_read_matrix():
    form = flask.request.form

    width = int(form["width"])
    height = int(form["height"])
    p1strats = np.zeros((width, height))
    p2strats = np.zeros((width, height))
    p1rationals = np.zeros((width, height), dtype=int)
    p2rationals = np.zeros((width, height), dtype=int)
    for key in form.keys():
        if key == "width" or key == "height":
            continue
        else:
            aname, x, y = key.split("_")
            x = int(x)
            y = int(y)
            val = None
            for value in form.getlist(key):
                val = value

            if val == None or val == '':
                val = 0
            val = int(val)
            
            if aname.find("p1") > -1:
                p1strats[x][y] = val
            else:
                p2strats[x][y] = val

    #Determine shit here // best responses
    for stratindex in range(width):
        compare_vals = p1strats[stratindex]
        best_val = max(compare_vals)
        for i in range(height):
            if p1strats[stratindex][i] == best_val:
                p1rationals[stratindex][i] = 1

    for stratindex in range(height):
        compare_vals = p2strats.T[stratindex]
        best_val = max(compare_vals)
        for i in range(width):
            if p2strats[i][stratindex] == best_val:
                p2rationals[i][stratindex] = 1

    #IEDS
    text_out = []
    p1_dominated = []
    p2_dominated = []

    p1_doms = get_dominations(p1strats, p1_dominated, p2_dominated, player=1)
    p2_doms = get_dominations(p2strats, p2_dominated, p1_dominated, player=2)
    strict_iteration = 0
    
    #text_out.append("==== Strictly Dominated Strategies of base game: ====")

    #for doms in p1_doms:
    #    dominated, dominator = doms
    #    text_out.append( f"P1: strategy {dominator+1} strictly dominates {dominated+1}" )
    #for doms in p2_doms:
    #    dominated, dominator = doms
    #    text_out.append( f"P2: strategy {dominator+1} strictly dominates {dominated+1}" )

    #text_out.append("==== Iterative elimination: ====")
    while(p1_doms != [] or p2_doms != []):

        if p1_doms != []:
            text_out.append(f"---- eliminating strategies of P1 strictly: (Iteration {strict_iteration})")
        for doms in p1_doms:
            dominated, dominator = doms
            text_out.append( f"P1: Strategy {dominator+1} strictly dominates strategy {dominated+1}")
            p1_dominated.append(dominated)


        if p2_doms != []:
            text_out.append(f"---- eliminating strategies of P2 strictly: (Iteration {strict_iteration})")
        for doms in p2_doms:
            dominated, dominator = doms
            text_out.append( f"P2:{dominator+1} strictly dominates {dominated+1}" )
            p2_dominated.append(dominated)
        p1_doms = get_dominations(p1strats, p1_dominated, p2_dominated, player=1)
        p2_doms = get_dominations(p2strats, p2_dominated, p1_dominated, player=2)
        strict_iteration += 1

    #IEWDS
    text_out_w = []
    p1_dominated_w = []
    p2_dominated_w = []

    p1_doms_w = get_dominations(p1strats, p1_dominated_w, p2_dominated_w, player=1, strict=False)
    p2_doms_w = get_dominations(p2strats, p2_dominated_w, p1_dominated_w, player=2, strict=False)

    weak_iteration = 0
    while(p1_doms_w != [] or p2_doms_w != []):
        if p1_doms_w != []:
            text_out_w.append(f"---- eliminating strategies of P1 weakly (Iteration {weak_iteration})")
        for doms in p1_doms_w:
            dominated, dominator = doms
            text_out_w.append( f"P1: Strategy {dominator+1} weakly dominates strategy {dominated+1}")
            p1_dominated_w.append(dominated)

        if p2_doms_w != []:
            text_out_w.append(f"---- eliminating strategies of P2: weakly (Iteration {weak_iteration})")
        for doms in p2_doms_w:
            dominated, dominator = doms
            text_out_w.append( f"P2:{dominator+1} weakly dominates {dominated+1}" )
            p2_dominated_w.append(dominated)

        p1_doms_w = get_dominations(p1strats, p1_dominated_w, p2_dominated_w, player=1, strict=False)
        p2_doms_w = get_dominations(p2strats, p2_dominated_w, p1_dominated_w, player=2, strict=False)
        weak_iteration += 1

    get_mixed_strategy_equilibria(p1strats, p2strats, p1_dominated_w, p2_dominated_w)
    
    #flask.session.clear()
    flask.session["p1strats"] = p1strats.tolist()
    flask.session["p2strats"] = p2strats.tolist()
    flask.session["p1rationals"] = p1rationals.tolist()
    flask.session["p2rationals"] = p2rationals.tolist()
    
    flask.session["ieds_text"] = text_out
    flask.session["iewds_text"] = text_out_w
    flask.session["p1_doms"] = p1_dominated_w
    flask.session["p2_doms"] = p2_dominated_w
    return flask.redirect("/showmatrix")

@app.route("/showmatrix")
def web_show_matrix():
    p1strats = flask.session["p1strats"]
    p2strats = flask.session["p2strats"]
    p1rationals = flask.session["p1rationals"]
    p2rationals = flask.session["p2rationals"]
    width = int(flask.session["width"])
    height = int(flask.session["height"])
    ieds_text = flask.session["ieds_text"]
    iewds_text = flask.session["iewds_text"]
    mixed_strats = flask.session["mixed_strategies"]
    p1doms = flask.session["p1_doms"]
    p2doms = flask.session["p2_doms"]
    return flask.render_template("matrixview.xml", p1strats=p1strats, p2strats=p2strats, width=width, height=height, p1rationals=p1rationals, p2rationals=p2rationals, ieds_text=ieds_text, iewds_text=iewds_text, mixed_strats=mixed_strats, p1doms=p1doms, p2doms=p2doms)

@app.route("/matrix/<a_strats>/<b_strats>")
def web_get_matrix(a_strats, b_strats):
    height, width = int(a_strats), int(b_strats)
    flask.session["width"] = width
    flask.session["height"] = height
    print(f"Generating form for Matrix of width: {width} and height: {height}")
    return flask.render_template("matrixform.xml", width=width, height=height)

app.run(debug=True)

