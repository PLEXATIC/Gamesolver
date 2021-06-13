import flask
import json
import numpy as np

app = flask.Flask(__name__)
app.secret_key = "secret43"

def get_dominations(payoffs, player):
    """
    returns a list of tuples, each tuple contains the index of a dominated strategy and it's dominator
    """
    dominations = []
    
    if player == 1:
        payoffs = payoffs.T
    
    for i1, strategy in enumerate(payoffs):

        for i2, competing_strat in enumerate(payoffs):
            if i1 == i2:
                continue
            if (strategy <= competing_strat).all() :
                print(strategy, competing_strat)
                dominations.append((i1, i2)) # i1 gets dominated by i2

    return dominations


@app.route("/readMatrix", methods=["POST"])
def web_read_matrix():
    form = flask.request.form

    width = int(form["width"])
    height = int(form["height"])
    p1strats = np.zeros((height, width))
    p2strats = np.zeros((height, width))
    p1rationals = np.zeros((height, width), dtype=int)
    p2rationals = np.zeros((height, width), dtype=int)
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
    p1_ieds = p1strats.copy() #copy strategy arrays, so the originals don't change, when deleting strategies
    p2_ieds = p2strats.copy()
    p1_doms = get_dominations(p1_ieds, player=1)
    p2_doms = get_dominations(p2_ieds, player=2)

    while(p1_doms != [] or p2_doms != []):

        for doms in p1_doms:
            dominated, dominator = doms
            text_out.append( f"P1: {dominated+1}. strategy gets dominated by the {dominator+1}. " )
            p1_ieds = np.delete(p1_ieds, dominated, 1) #delete the dominated strategy in both arrays
            p2_ieds = np.delete(p2_ieds, dominated, 1)

        for doms in p2_doms:
            dominated, dominator = doms
            text_out.append( f"P2: {dominated+1}. strategy gets dominated by the {dominator+1}. " )
            p1_ieds = np.delete(p1_ieds, dominated, 0) #delete the dominated strategy in both arrays
            p2_ieds = np.delete(p2_ieds, dominated, 0) 
            

        text_out.append(f"---- eliminate dominated strategies! ----")
        p1_doms = get_dominations(p1_ieds, player=1)
        p2_doms = get_dominations(p2_ieds, player=2)


    flask.session.clear()
    flask.session["p1strats"] = p1strats.tolist()
    flask.session["p2strats"] = p2strats.tolist()
    flask.session["p1rationals"] = p1rationals.tolist()
    flask.session["p2rationals"] = p2rationals.tolist()
    flask.session["width"] = width
    flask.session["height"] = height
    flask.session["ieds_text"] = text_out
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
    return flask.render_template("matrixview.xml", p1strats=p1strats, p2strats=p2strats, width=width, height=height, p1rationals=p1rationals, p2rationals=p2rationals, ieds_text=ieds_text)

@app.route("/findstrictlydominated")
def web_find_strictly_dominated():
    p1strats = flask.session["p1strats"]
    p2strats = flask.session["p2strats"]
    p1sd = np.zeros_like(p1strats)
    p2sd = np.zeros_like(p2strats) 
    width = flask.session["width"]
    height = flask.session["height"]
    #Find strictly dominated strats for p1
    #Iterate over rows
    print(p1strats)
    
    for y in range(height):
        for y_ in range(height):
            if y == y_:
                continue
            dom = True
            for x in range(width):
                if p1strats[x][y] >= p1strats[x][y_]:
                    dom = False
            if dom:
                for x in range(width):
                    p1sd[x][y] = 1


    return str(p1sd)


@app.route("/matrix/<a_strats>/<b_strats>")
def web_get_matrix(a_strats, b_strats):
    height, width = int(a_strats), int(b_strats)
    print(f"Generating form for Matrix of width: {width} and height: {height}")
    return flask.render_template("matrixform.xml", width=width, height=height)

app.run(debug=True)

