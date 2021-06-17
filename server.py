import os
import random
import math

import cherrypy
"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""

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


def get_cautious_moves(curr_head, data):
  head_x = curr_head["x"]
  head_y = curr_head["y"]
  moves = []
  if not is_blocked(head_x - 1, head_y, data) and not is_blocked(
          head_x - 2, head_y, data):
      moves.append("left")
  if not is_blocked(head_x + 1, head_y, data) and not is_blocked(
          head_x + 2, head_y, data):
      moves.append("right")
  if not is_blocked(head_x, head_y - 1, data) and not is_blocked(
          head_x, head_y - 2, data):
      moves.append("down")
  if not is_blocked(head_x, head_y + 1, data) and not is_blocked(
          head_x, head_y + 2, data):
      moves.append("up")

  return moves


def get_normal_moves(curr_head, data):
  head_x = curr_head["x"]
  head_y = curr_head["y"]
  moves = []
  if not is_blocked(head_x - 1, head_y, data):
      moves.append("left")
  if not is_blocked(head_x + 1, head_y, data):
      moves.append("right")
  if not is_blocked(head_x, head_y - 1, data):
      moves.append("down")
  if not is_blocked(head_x, head_y + 1, data):
      moves.append("up")

  return moves


def point_distance(p1, p2):
    print(f"getting dist between {p1} and {p2}")
    return math.sqrt((p1["x"] - p2["x"])**2 + (p1["y"] - p2["y"])**2)


# score fn: distance to closest food
def dist_to_closest_food(head, board):
    default = 10000
    closest_dist = default  # larger than anything realistic
    for food in board["food"]:
        closest_dist = min(closest_dist, point_distance(food, head))
    return 0 if closest_dist == default else closest_dist * -1


def centrality(head, board):
    center_x = board["width"] / 2
    center_y = board["height"] / 2
    return (abs(head["x"] - center_x) + abs(head["y"] - center_y)) * -1


def move_value(move_str, curr_head, data):
    move = move_map[move_str]
    next_head = {
        key: (curr_head[key] + value)
        for (key, value) in move.items()
    }
    # use any value fns available. This should amount to something like a linear expression
    board = data["board"]
    missing_health = 100 - data["you"]["health"]
    value = (0.1 * missing_health * dist_to_closest_food(
        next_head, board)) + centrality(next_head, board)
    print(f"value of move '{move_str}': {value}")

    return value


def choose_move(data):
    curr_head = data["you"]["head"]

    # filter out dangerous moves
    moves = get_cautious_moves(curr_head, data)
    if not moves:
        moves = get_normal_moves(curr_head, data)

    # Choose the best direction to move in
    return max(moves, key=lambda move: move_value(move, curr_head, data))


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

        print(f"MOVE: {move}")
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
