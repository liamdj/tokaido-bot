from math import nan
from tokaido_game import TokaidoGame, Traveler
from mcts import Mcts
import itertools as itr
import cProfile

def run_game(travelers, trials):
    game = TokaidoGame(travelers)
    while not game.is_over():
        tree = Mcts(game)
        for _ in range(trials):
            tree.do_round()
        game.take_action(tree.best_move())

    for plyr in game.players:
        print(
            "{0} scored {1} ({2})".format(
                plyr.traveler.name, plyr.points, plyr.achievements
            )
        )
    return [game.players_beaten(i) for i in range(len(travelers))]


if __name__ == "__main__":
    names = [tvlr.name for tvlr in Traveler]
    scores_by_tvlr = {s: 0 for s in names}
    games_by_tvlr = {s: 0 for s in names}
    scores_by_order = {i: 0 for i in range(4)}
    games = 0
    for perm in itr.permutations(names, 4):
        # cProfile.run('run_game(perm, 1000)')
        scores = run_game(perm, 1000)
        for i in range(4):
            scores_by_order[i] += scores[i]
            scores_by_tvlr[perm[i]] += scores[i]
            games_by_tvlr[perm[i]] += 1
        games += 1
        break

    print([s / games for s in scores_by_order.values()])
    for n in names:
        print(n, scores_by_tvlr[n] / games_by_tvlr[n] if games_by_tvlr[n] != 0 else nan)

