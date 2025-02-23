import os
import random
import math

import cherrypy
"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""

lookahead = 5
coeff_hunger = 0.7
coeff_centrality = -100
coeff_avoidance = 0.5
coeff_hunt = -4

move_map = {
    "up": {
        "x": 0,
        "y": 1
    },
    "down": {
        "x": 0,
        "y": -1
    },
    "left": {
        "x": -1,
        "y": 0
    },
    "right": {
        "x": 1,
        "y": 0
    }
}

possible_moves = ["up", "down", "left", "right"]


def is_blocked(x, y, data):
    board = data["board"]
    if (x < 0 or y < 0):
        return True
    if (x >= board["width"] or y >= board["height"]):
        return True
    for snake in board["snakes"]:
        for part in snake["body"]:
            if part["x"] == x and part["y"] == y:
                return True
    return False


def head_to_head_liability(x, y, data):
    point = {"x": x, "y": y}
    you = data["you"]
    for snake in data["board"]["snakes"]:
        if (snake["id"] != you["id"]) and (point_distance(
                point, snake["head"]) == 1) and len(snake["body"]) >= len(
                    you["body"]):
            return True
    return False


def is_safe(x, y, data):
    return not is_blocked(x, y, data) and not head_to_head_liability(
        x, y, data)


def get_safe_moves(curr_head, data):
    head_x = curr_head["x"]
    head_y = curr_head["y"]
    moves = []
    if is_safe(head_x - 1, head_y, data):
        moves.append("left")
    if is_safe(head_x + 1, head_y, data):
        moves.append("right")
    if is_safe(head_x, head_y - 1, data):
        moves.append("down")
    if is_safe(head_x, head_y + 1, data):
        moves.append("up")

    return moves


def point_distance(p1, p2):
    return abs(p1["x"] - p2["x"]) + abs(p1["y"] - p2["y"])


# score fn: distance to closest food
def dist_to_closest_food(head, board):
    default = 10000
    closest_dist = default  # larger than anything realistic
    for food in board["food"]:
        closest_dist = min(closest_dist, point_distance(food, head))
    return 0 if closest_dist == default else closest_dist * -1


# score fn: distance to closest larger snake head
def dist_to_closest_pred(head, data):
    default = 10000
    closest_dist = default  # larger than anything realistic
    you = data["you"]
    for snake in data["board"]["snakes"]:
        if (snake["id"] != you["id"]) and len(snake["body"]) >= len(
                you["body"]):
            closest_dist = min(closest_dist,
                               point_distance(snake["head"], head))
    return 0 if closest_dist == default else closest_dist


# score fn: distance to closest smaller snake head
def dist_to_closest_prey(head, data):
    default = 10000
    closest_dist = default  # larger than anything realistic
    you = data["you"]
    for snake in data["board"]["snakes"]:
        if (snake["id"] != you["id"]) and len(snake["body"]) > len(
                you["body"]):
            closest_dist = min(closest_dist,
                               point_distance(snake["head"], head))
    return 0 if closest_dist == default else closest_dist


def centrality(head, board):
    center_x = board["width"] / 2
    center_y = board["height"] / 2
    return point_distance(head, {"x": center_x, "y": center_y})


def board_value(curr_head, data):
  # use any value fns available. This should amount to something like a linear expression
  board = data["board"]

  # weighted features
  missing_health = 100 - data["you"]["health"]
  get_food = (coeff_hunger * missing_health *
              dist_to_closest_food(curr_head, board))
  # print(f"get food: {get_food}")
  stay_center = coeff_centrality * centrality(curr_head, board)
  # print(f"stay centered: {stay_center}")
  avoid_pred = coeff_avoidance * dist_to_closest_pred(
      curr_head, data)
  # print(f"avoid predators: {avoid_pred}")
  hunt_prey = coeff_hunt * dist_to_closest_prey(curr_head, data)
  # print(f"hunt prey: {hunt_prey}")

  value = get_food + stay_center + avoid_pred + hunt_prey
  return value


def apply_move(move_str, curr_head):
    move = move_map[move_str]
    next_head = {
        key: (curr_head[key] + value)
        for (key, value) in move.items()
    }
    return next_head


def board_value_lookahead(curr_head, data, lookahead=0):
    if lookahead == 0:
        return board_value(curr_head, data)

    moves = get_safe_moves(curr_head, data)
    return -10000 if not moves else max({
        board_value_lookahead(apply_move(move, curr_head), data, lookahead - 1)
        for move in moves
    })


def choose_move(data):
    curr_head = data["you"]["head"]
    moves = get_safe_moves(curr_head, data)
    return "up" if not moves else max(
        moves,
        key=lambda move: board_value_lookahead(apply_move(move, curr_head),
                                               data, lookahead))


class Battlesnake(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        # This function is called when you register your Battlesnake on play.battlesnake.com
        # It controls your Battlesnake appearance and author permissions.
        # TIP: If you open your Battlesnake URL in browser you should see this data
        return {
            "apiversion": "1",
            "author": "cognalog",  # TODO: Your Battlesnake Username
            "color": "#6b0c78",  # TODO: Personalize
            "head": "safe",  # TODO: Personalize
            "tail": "freckled",  # TODO: Personalize
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def start(self):
        # This function is called everytime your snake is entered into a game.
        # cherrypy.request.json contains information about the game that's about to be played.
        data = cherrypy.request.json

        print("START")
        return "ok"

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def move(self):
        # This function is called on every turn of a game. It's how your snake decides where to move.
        # Valid moves are "up", "down", "left", or "right".
        # TODO: Use the information in cherrypy.request.json to decide your next move.
        data = cherrypy.request.json

        # Choose the best direction to move in
        move = choose_move(data)

        # print(f"MOVE: {move}")
        return {"move": move}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def end(self):
        # This function is called when a game your snake was in ends.
        # It's purely for informational purposes, you don't have to make any decisions here.
        data = cherrypy.request.json

        print("END")
        return "ok"


if __name__ == "__main__":
    server = Battlesnake()
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update({
        "server.socket_port":
        int(os.environ.get("PORT", "8080")),
    })
    print("Starting Battlesnake Server...")
    cherrypy.quickstart(server)
