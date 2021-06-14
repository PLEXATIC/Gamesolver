import flask
import json
import numpy as np

app = flask.Flask(__name__)
app.secret_key = "secret43"

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

            if sum(strategy) >= sum(competing_strat): #make shure that equal strategies don't dominate each other
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

    text_out.append("==== Dominated Strategies of base game: ====")
    for doms in p1_doms:
        dominated, dominator = doms
        text_out.append( f"P1: {dominated+1}. strategy gets dominated by the {dominator+1}. " )

    for doms in p2_doms:
        dominated, dominator = doms
        text_out.append( f"P2: {dominated+1}. strategy gets dominated by the {dominator+1}. " )

    text_out.append("==== Iterative elimination: ====")
    while(p1_doms != [] or p2_doms != []):

        if p1_doms != []:
            text_out.append(f"---- eliminating strategies of P1 strictly:")
        for doms in p1_doms:
            dominated, dominator = doms
            text_out.append( f"P1: Strategy {dominator+1} strictly dominates strategy {dominated+1}")
            p1_dominated.append(dominated)

        p2_doms = get_dominations(p2strats, p2_dominated, p1_dominated, player=2)

        if p2_doms != []:
            text_out.append(f"---- eliminating strategies of P2 strictly:")
        for doms in p2_doms:
            dominated, dominator = doms
            text_out.append( f"P2:{dominator+1} strictly dominates {dominated+1}" )
            p2_dominated.append(dominated)
        p1_doms = get_dominations(p1strats, p1_dominated, p2_dominated, player=1)

    #IEWDS
    text_out_w = []
    p1_dominated_w = []
    p2_dominated_w = []

    p1_doms_w = get_dominations(p1strats, p1_dominated_w, p2_dominated_w, player=1, strict=False)
    p2_doms_w = get_dominations(p2strats, p2_dominated_w, p1_dominated_w, player=2, strict=False)

    while(p1_doms_w != [] or p2_doms_w != []):

        if p1_doms_w != []:
            text_out_w.append(f"---- eliminating strategies of P1 weakly:")
        for doms in p1_doms_w:
            dominated, dominator = doms
            text_out_w.append( f"P1: Strategy {dominator+1} weakly dominates strategy {dominated+1}")
            p1_dominated_w.append(dominated)


        p2_doms_w = get_dominations(p2strats, p2_dominated_w, p1_dominated_w, player=2, strict=False)

        if p2_doms_w != []:
            text_out_w.append(f"---- eliminating strategies of P2: weakly")
        for doms in p2_doms_w:
            dominated, dominator = doms
            text_out_w.append( f"P2:{dominator+1} weakly dominates {dominated+1}" )
            p2_dominated_w.append(dominated)
        p1_doms_w = get_dominations(p1strats, p1_dominated_w, p2_dominated_w, player=1, strict=False)
    flask.session.clear()
    flask.session["p1strats"] = p1strats.tolist()
    flask.session["p2strats"] = p2strats.tolist()
    flask.session["p1rationals"] = p1rationals.tolist()
    flask.session["p2rationals"] = p2rationals.tolist()
    flask.session["width"] = width
    flask.session["height"] = height
    flask.session["ieds_text"] = text_out
    flask.session["iewds_text"] = text_out_w
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
    return flask.render_template("matrixview.xml", p1strats=p1strats, p2strats=p2strats, width=width, height=height, p1rationals=p1rationals, p2rationals=p2rationals, ieds_text=ieds_text, iewds_text=iewds_text)

@app.route("/matrix/<a_strats>/<b_strats>")
def web_get_matrix(a_strats, b_strats):
    height, width = int(a_strats), int(b_strats)
    print(f"Generating form for Matrix of width: {width} and height: {height}")
    return flask.render_template("matrixform.xml", width=width, height=height)

app.run(debug=True)

