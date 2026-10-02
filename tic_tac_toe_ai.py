import os
import random
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)

# Use a fixed secret key on Render
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


# --------------------------------------------------
# CREATE NEW GAME
# --------------------------------------------------

def new_game():
    return {
        "places": [
            ["_", "_", "_"],
            ["_", "_", "_"],
            ["_", "_", "_"]
        ],

        "user": [
            [False, False, False],
            [False, False, False],
            [False, False, False]
        ],

        "pc": [
            [False, False, False],
            [False, False, False],
            [False, False, False]
        ],

        "last": -1,
        "placed": None,
        "lis": list(range(1, 10)),
        "name": ""
    }


# --------------------------------------------------
# HOME / GAME ROUTE
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def place():

    # Create a separate game for each user's session
    if "game" not in session:
        session["game"] = new_game()

    game = session["game"]

    # ----------------------------------------------
    # FIRST VISIT
    # ----------------------------------------------

    if not session.get("visited"):

        if request.method == "POST" and "name" in request.form:

            game["name"] = request.form["name"].title()

            session["game"] = game
            session["visited"] = True

            return render_template(
                "interface.html",
                places=game["places"],
                lis=game["lis"],
                place=[
                    1,
                    f"{game['name']} Lets start the game !!"
                ],
                placed=None,
                name=game["name"]
            )

        return render_template("intro.html")

    # ----------------------------------------------
    # GAME
    # ----------------------------------------------

    if len(game["lis"]) != 9:
        current_place = [
            1,
            f"{game['name']} , Lets start the game !!"
        ]
    else:
        current_place = ""

    if request.method == "POST" and "place" in request.form:

        p = int(request.form["place"])

        # Player's move
        player_turn(game, p - 1)

        # Check if player won
        result = check_win(game)

        if result[0]:
            session["game"] = game

            return render_template(
                "Win.html",
                who=result[1],
                places=game["places"],
                lis=game["lis"],
                name=game["name"]
            )

        # If player's move was valid, computer plays
        if game["placed"]:

            computer_move = system(game)

            if computer_move is not None:

                current_place = list(computer_move)

                current_place[1] = (
                    game["name"] + " , " + current_place[1]
                )

                # Remove both positions from available list
                game["lis"][p - 1] = " "
                game["lis"][computer_move[0] - 1] = " "

        # Check if computer won
        result = check_win(game)

        if result[0]:
            session["game"] = game

            return render_template(
                "Win.html",
                who=result[1],
                places=game["places"],
                lis=game["lis"],
                name=game["name"]
            )

        # Save updated game
        session["game"] = game

        return render_template(
            "interface.html",
            places=game["places"],
            placed=game["placed"],
            lis=game["lis"],
            place=current_place,
            name=game["name"]
        )

    # GET request
    return render_template(
        "interface.html",
        places=game["places"],
        lis=game["lis"],
        place=current_place,
        placed=None,
        name=game["name"]
    )


# --------------------------------------------------
# RESET GAME
# --------------------------------------------------

@app.route("/reset", methods=["POST", "GET"])
def reset():

    # Reset only this user's game
    session["game"] = new_game()

    # Keep the user on the game page
    session["visited"] = True

    return redirect("/")


# --------------------------------------------------
# PLAYER TURN
# --------------------------------------------------

def player_turn(game, n):

    places = game["places"]
    user = game["user"]

    n = int(n)

    row = n // 3
    col = n % 3

    # Check whether position is empty
    if places[row][col] == "_":

        places[row][col] = "✘"
        user[row][col] = True

        game["last"] = (row, col)
        game["placed"] = True

    else:

        game["placed"] = False


# --------------------------------------------------
# COMPUTER MOVE
# --------------------------------------------------

def system(game):

    places = game["places"]
    user = game["user"]
    pc = game["pc"]

    # ----------------------------------------------
    # USER ROWS
    # ----------------------------------------------

    r1 = [user[0][0], user[0][1], user[0][2]]
    r2 = [user[1][0], user[1][1], user[1][2]]
    r3 = [user[2][0], user[2][1], user[2][2]]

    # ----------------------------------------------
    # USER COLUMNS
    # ----------------------------------------------

    c1 = [user[0][0], user[1][0], user[2][0]]
    c2 = [user[0][1], user[1][1], user[2][1]]
    c3 = [user[0][2], user[1][2], user[2][2]]

    # ----------------------------------------------
    # USER DIAGONALS
    # ----------------------------------------------

    d1 = [user[0][0], user[1][1], user[2][2]]
    d2 = [user[0][2], user[1][1], user[2][0]]

    # ----------------------------------------------
    # COMPUTER ROWS
    # ----------------------------------------------

    pr1 = [pc[0][0], pc[0][1], pc[0][2]]
    pr2 = [pc[1][0], pc[1][1], pc[1][2]]
    pr3 = [pc[2][0], pc[2][1], pc[2][2]]

    # ----------------------------------------------
    # COMPUTER COLUMNS
    # ----------------------------------------------

    pc1 = [pc[0][0], pc[1][0], pc[2][0]]
    pc2 = [pc[0][1], pc[1][1], pc[2][1]]
    pc3 = [pc[0][2], pc[1][2], pc[2][2]]

    # ----------------------------------------------
    # COMPUTER DIAGONALS
    # ----------------------------------------------

    pd1 = [pc[0][0], pc[1][1], pc[2][2]]
    pd2 = [pc[0][2], pc[1][1], pc[2][0]]

    # Number of player's moves
    su = sum(user[0]) + sum(user[1]) + sum(user[2])

    # ----------------------------------------------
    # FIRST MOVE
    # ----------------------------------------------

    if su == 1:

        # Choose a random empty position
        while True:

            t = random.randint(0, 8)

            if not user[t // 3][t % 3] and not pc[t // 3][t % 3]:
                break

        places[t // 3][t % 3] = "O"
        pc[t // 3][t % 3] = True

        return (
            t + 1,
            f"I placed at {t + 1} position"
        )

    # ==================================================
    # ATTACK - COMPUTER CAN WIN
    # ==================================================

    # Rows
    elif (
        (sum(pr1) == 2 and sum(r1) != 1)
        or
        (sum(pr2) == 2 and sum(r2) != 1)
        or
        (sum(pr3) == 2 and sum(r3) != 1)
    ):

        if sum(pr1) == 2 and sum(r1) != 1:
            return plarow(game, 0)

        elif sum(pr2) == 2 and sum(r2) != 1:
            return plarow(game, 1)

        elif sum(pr3) == 2 and sum(r3) != 1:
            return plarow(game, 2)

    # Columns
    elif (
        (sum(pc1) == 2 and sum(c1) != 1)
        or
        (sum(pc2) == 2 and sum(c2) != 1)
        or
        (sum(pc3) == 2 and sum(c3) != 1)
    ):

        if sum(pc1) == 2 and sum(c1) != 1:
            return placol(game, 0)

        elif sum(pc2) == 2 and sum(c2) != 1:
            return placol(game, 1)

        elif sum(pc3) == 2 and sum(c3) != 1:
            return placol(game, 2)

    # Diagonals
    elif (
        (sum(pd1) == 2 and sum(d1) != 1)
        or
        (sum(pd2) == 2 and sum(d2) != 1)
    ):

        if sum(pd1) == 2 and sum(d1) != 1:

            for i in range(3):

                if not user[i][i] and not pc[i][i]:

                    pc[i][i] = True
                    places[i][i] = "O"

                    position = i * 3 + i + 1

                    return (
                        position,
                        f"I placed at {position} position"
                    )

        elif sum(pd2) == 2 and sum(d2) != 1:

            if not user[0][2] and not pc[0][2]:

                pc[0][2] = True
                places[0][2] = "O"

                return (3, "I placed at 3rd position")

            elif not user[1][1] and not pc[1][1]:

                pc[1][1] = True
                places[1][1] = "O"

                return (5, "I placed at 5th position")

            elif not user[2][0] and not pc[2][0]:

                pc[2][0] = True
                places[2][0] = "O"

                return (7, "I placed at 7th position")

    # ==================================================
    # DEFENCE - BLOCK PLAYER
    # ==================================================

    # Rows
    elif (
        (sum(r1) == 2 and sum(pr1) != 1)
        or
        (sum(r2) == 2 and sum(pr2) != 1)
        or
        (sum(r3) == 2 and sum(pr3) != 1)
    ):

        if sum(r1) == 2 and sum(pr1) != 1:
            return plarow(game, 0)

        elif sum(r2) == 2 and sum(pr2) != 1:
            return plarow(game, 1)

        elif sum(r3) == 2 and sum(pr3) != 1:
            return plarow(game, 2)

    # Columns
    elif (
        (sum(c1) == 2 and sum(pc1) != 1)
        or
        (sum(c2) == 2 and sum(pc2) != 1)
        or
        (sum(c3) == 2 and sum(pc3) != 1)
    ):

        if sum(c1) == 2 and sum(pc1) != 1:
            return placol(game, 0)

        elif sum(c2) == 2 and sum(pc2) != 1:
            return placol(game, 1)

        elif sum(c3) == 2 and sum(pc3) != 1:
            return placol(game, 2)

    # Diagonals
    elif (
        (sum(d1) == 2 and sum(pd1) != 1)
        or
        (sum(d2) == 2 and sum(pd2) != 1)
    ):

        if sum(d1) == 2 and sum(pd1) != 1:

            for i in range(3):

                if not user[i][i] and not pc[i][i]:

                    pc[i][i] = True
                    places[i][i] = "O"

                    position = i * 3 + i + 1

                    return (
                        position,
                        f"I placed at {position} position"
                    )

        elif sum(d2) == 2 and sum(pd2) != 1:

            if not user[0][2] and not pc[0][2]:

                pc[0][2] = True
                places[0][2] = "O"

                return (3, "I placed at 3rd position")

            elif not user[1][1] and not pc[1][1]:

                pc[1][1] = True
                places[1][1] = "O"

                return (5, "I placed at 5th position")

            elif not user[2][0] and not pc[2][0]:

                pc[2][0] = True
                places[2][0] = "O"

                return (7, "I placed at 7th position")

    # ==================================================
    # NORMAL MOVE
    # ==================================================

    else:

        for i in range(3):

            for j in range(3):

                if not pc[i][j] and not user[i][j]:

                    pc[i][j] = True
                    places[i][j] = "O"

                    position = i * 3 + j + 1

                    return (
                        position,
                        f"I placed at {position} position"
                    )

    return None


# --------------------------------------------------
# PLACE COMPUTER MOVE IN A ROW
# --------------------------------------------------

def plarow(game, row):

    places = game["places"]
    user = game["user"]
    pc = game["pc"]

    for i in range(3):

        if not user[row][i] and not pc[row][i]:

            pc[row][i] = True
            places[row][i] = "O"

            position = row * 3 + i + 1

            return (
                position,
                f"I placed at {position} position"
            )

    return None


# --------------------------------------------------
# PLACE COMPUTER MOVE IN A COLUMN
# --------------------------------------------------

def placol(game, col):

    places = game["places"]
    user = game["user"]
    pc = game["pc"]

    for i in range(3):

        if not user[i][col] and not pc[i][col]:

            pc[i][col] = True
            places[i][col] = "O"

            position = i * 3 + col + 1

            return (
                position,
                f"I placed at {position} position"
            )

    return None


# --------------------------------------------------
# CHECK WIN
# --------------------------------------------------

def check_win(game):

    places = game["places"]
    user = game["user"]
    pc = game["pc"]

    # ----------------------------------------------
    # PLAYER ROWS
    # ----------------------------------------------

    r1 = (
        places[0][0] ==
        places[0][1] ==
        places[0][2] ==
        "✘"
    )

    r2 = (
        places[1][0] ==
        places[1][1] ==
        places[1][2] ==
        "✘"
    )

    r3 = (
        places[2][0] ==
        places[2][1] ==
        places[2][2] ==
        "✘"
    )

    # ----------------------------------------------
    # PLAYER COLUMNS
    # ----------------------------------------------

    c1 = (
        places[0][0] ==
        places[1][0] ==
        places[2][0] ==
        "✘"
    )

    c2 = (
        places[0][1] ==
        places[1][1] ==
        places[2][1] ==
        "✘"
    )

    c3 = (
        places[0][2] ==
        places[1][2] ==
        places[2][2] ==
        "✘"
    )

    # ----------------------------------------------
    # PLAYER DIAGONALS
    # ----------------------------------------------

    d1 = (
        places[0][0] ==
        places[1][1] ==
        places[2][2] ==
        "✘"
    )

    d2 = (
        places[0][2] ==
        places[1][1] ==
        places[2][0] ==
        "✘"
    )

    # ----------------------------------------------
    # COMPUTER ROWS
    # ----------------------------------------------

    pr1 = (
        places[0][0] ==
        places[0][1] ==
        places[0][2] ==
        "O"
    )

    pr2 = (
        places[1][0] ==
        places[1][1] ==
        places[1][2] ==
        "O"
    )

    pr3 = (
        places[2][0] ==
        places[2][1] ==
        places[2][2] ==
        "O"
    )

    # ----------------------------------------------
    # COMPUTER COLUMNS
    # ----------------------------------------------

    pc1 = (
        places[0][0] ==
        places[1][0] ==
        places[2][0] ==
        "O"
    )

    pc2 = (
        places[0][1] ==
        places[1][1] ==
        places[2][1] ==
        "O"
    )

    pc3 = (
        places[0][2] ==
        places[1][2] ==
        places[2][2] ==
        "O"
    )

    # ----------------------------------------------
    # COMPUTER DIAGONALS
    # ----------------------------------------------

    pd1 = (
        places[0][0] ==
        places[1][1] ==
        places[2][2] ==
        "O"
    )

    pd2 = (
        places[0][2] ==
        places[1][1] ==
        places[2][0] ==
        "O"
    )

    # ----------------------------------------------
    # CHECK PLAYER WIN
    # ----------------------------------------------

    if r1 or r2 or r3 or c1 or c2 or c3 or d1 or d2:

        return True, "✘"

    # ----------------------------------------------
    # CHECK COMPUTER WIN
    # ----------------------------------------------

    elif pr1 or pr2 or pr3 or pc1 or pc2 or pc3 or pd1 or pd2:

        return True, "O"

    # ----------------------------------------------
    # CHECK DRAW
    # ----------------------------------------------

    su = sum(user[0]) + sum(user[1]) + sum(user[2])
    sp = sum(pc[0]) + sum(pc[1]) + sum(pc[2])

    if su + sp == 9:

        return True, "Draw"

    return False, "DOe"


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
