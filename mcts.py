import math
from copy import deepcopy


class Node:
    C = 2

    def __init__(self, player: int):
        # index of player who made the previous move
        self.player = player
        # times node has been visited
        self.trials = 0
        # sum of values when node has been visited
        self.cum_value = 0
        # map of actions to resulting nodes
        self.children = {}

    def idealness(self, parent_trials: int) -> float:
        if self.trials == 0:
            return 3
        else:
            return self.cum_value / self.trials + math.sqrt(
                Node.C * math.log(parent_trials) / self.trials
            )

    def best_action(self, game_state):
        if not self.children:
            return

        top_ideal = 0
        for action in game_state.available_actions():
            ideal = self.children[action].idealness(self.trials)
            if ideal > top_ideal:
                top_ideal = ideal
                top_action = action
        return top_action

    def create_children(self, game_state):
        for action in game_state.available_actions():
            if action not in self.children:
                self.children[action] = Node(game_state.whose_turn)


class Mcts:
    def __init__(self, game_state):
        self.current_state = game_state
        self.root = Node(game_state.whose_turn)

    # return the action that has been the most explored
    def best_move(self):
        most_trials = max([node.trials for node in self.root.children.values()])
        for action, child in self.root.children.items():
            if child.trials == most_trials:
                return action

    # update node values for an iteration
    def do_round(self):
        nodes, state = self.construct_path()
        state.random_playout()
        values = [state.players_beaten(i) for i in range(len(state.players))]
        for nd in nodes:
            nd.trials += 1
            nd.cum_value += values[nd.player]

    # find the path to a leaf using idealness while expanding nodes
    def construct_path(self):
        nodes = [self.root]
        state = deepcopy(self.current_state)
        current_node = self.root
        while current_node.trials > 0 and not state.is_over():
            current_node.create_children(state)
            action = current_node.best_action(state)
            state.take_action(action)
            current_node = current_node.children[action]
            nodes.append(current_node)
        return nodes, state

