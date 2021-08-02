from collections import namedtuple
import itertools as itr
from enum import IntEnum, auto
import random
from typing import List

DONATION_PTS = 1
TEMPLE_PTS = [10, 7, 4, 2]
MIN_DONATIONS = 1
MAX_DONATIONS = 3

SOUVENIR_PTS = [1, 3, 5, 7]
SOUVENIRS_OFFERED = 3
SOUVENIRS = [
    ("fan", 1, 6),
    ("food", 1, 3),
    ("food", 2, 3),
    ("shirt", 2, 6),
    ("statue", 2, 3),
    ("statue", 3, 3),
]

MEAL_PTS = 6
MEALS = [
    ("miso", 1, 3),
    ("nigiri", 1, 3),
    ("dango", 1, 3),
    ("soba", 2, 2),
    ("tofu", 2, 2),
    ("sushi", 2, 2),
    ("yakitori", 2, 2),
    ("tempura", 2, 2),
    ("sashimi", 3, 1),
    ("fugu", 3, 1),
    ("meshi", 3, 1),
    ("unagi", 3, 1),
    ("udon", 3, 1),
    ("donburi", 3, 1),
]

BATHS = [(2, 6), (3, 6)]

ENCOUNTERS = [
    ("coins", 2),
    ("souvenir", 2),
    ("field", 1),
    ("mountain", 2),
    ("lake", 3),
    ("donations", 2),
    ("points", 2),
]
ENCOUNTER_VALUE = {"coins": 3, "donations": 1, "points": 3}

FARM_PAYMENT = 3

SECTIONS = {"field": 3, "mountain": 4, "lake": 5}

ACHIEVEMENT_PTS = 3

STARTING_COINS = {
    "Chuubei": 4,
    "Hiroshige": 3,
    "Hirotoda": 8,
    "Kinko": 7,
    "Mitsukuni": 6,
    "Sasayakko": 5,
    "Satsuki": 2,
    "Umegae": 5,
    "Yoshiyasu": 9,
    "Zen_emon": 6,
}


class Traveler(IntEnum):
    Chuubei = auto()
    Hiroshige = auto()
    Hirotoda = auto()
    Kinko = auto()
    Mitsukuni = auto()
    Sasayakko = auto()
    Satsuki = auto()
    Umegae = auto()
    Yoshiyasu = auto()
    Zen_emon = auto()


class TokaidoGame:

    Item = namedtuple("Item", ["type", "cost"])

    board = []

    class Player:
        def __init__(self, traveler):
            self.traveler = Traveler[traveler]
            self.points = 0
            self.coins = STARTING_COINS[traveler]
            self.meals = []
            self.panoramas = {"field": 0, "mountain": 0, "lake": 0}
            self.encounters = 0
            self.baths = 0
            self.donations = 0
            self.souvenirs = {"fan": 0, "food": 0, "shirt": 0, "statue": 0}
            self.achievements = 0

    class Space(IntEnum):
        INN = auto()
        SHOP = auto()
        FARM = auto()
        TEMPLE = auto()
        ENCOUNTER = auto()
        FIELD = auto()
        MOUNTAIN = auto()
        LAKE = auto()
        HOT_SPRING = auto()

    class Action(IntEnum):
        MOVE = auto()
        EAT = auto()
        BUY = auto()
        DONATE = auto()
        CHOOSE_ENCOUNTER = auto()
        CHOOSE_PANORAMA = auto()
        FINISHED = auto()

    def __init__(self, travelers):

        assert len(travelers) == 4

        if not self.board:
            with open("tokaido4p.txt") as f:
                for s in f.read().split("\n"):
                    self.board.append(getattr(self.Space, s))

        self.cards = {
            "encounters": [typ for typ, num in ENCOUNTERS for _ in range(num)],
            "meals": [
                self.Item(typ, cost) for typ, cost, num in MEALS for _ in range(num)
            ],
            "souvenirs": [
                self.Item(typ, cost) for typ, cost, num in SOUVENIRS for _ in range(num)
            ],
            "baths": [pts for pts, num in BATHS for _ in range(num)],
        }

        self.players = [self.Player(tvlr) for tvlr in travelers]
        self.positions = list(range(len(travelers)))
        self.turn = self.Action.MOVE
        self.whose_turn = 0
        self.waiting_to_eat = False
        self.gastro = 1

        self.pano_achievments = {"field": True, "mountain": True, "lake": True}

    def next_player_turn(self):
        if self.turn == self.Action.EAT:
            behind = self.positions[self.whose_turn] - 1
            if behind in self.positions:
                self.whose_turn = self.positions.index(behind)
            elif self.positions[self.whose_turn] == len(self.board) - len(self.players):
                self.end_of_game()
            else:
                self.turn = self.Action.MOVE
        else:
            back = min(self.positions)
            if (
                self.board[back] == self.Space.INN
                and self.board[back - 1] != self.Space.INN
            ):
                self.available_meals = self.draw_cards(
                    "meals", len(self.players) + 1 - self.gastro
                )
                self.whose_turn = self.positions.index(max(self.positions))
                self.turn = self.Action.EAT
            else:
                self.whose_turn = self.positions.index(min(self.positions))
                self.turn = self.Action.MOVE

    def on_road(self, position):
        return (
            position == len(self.board) - 1
            or self.board[position] != self.board[position + 1]
        )

    def roadToInn(self, start):
        spaces = set()
        for pos in range(start, len(self.board)):
            if self.onRoad(pos):
                spaces.add(pos)
                if self.board[pos] == self.Space.INN:
                    return spaces
        return spaces

    def end_of_game(self):

        spent = [sum([m.cost for m in p.meals]) for p in self.players]
        baths = [p.baths for p in self.players]
        encounters = [p.encounters for p in self.players]
        souvenirs = [sum(p.souvenirs.values()) for p in self.players]
        for category in [spent, baths, encounters, souvenirs]:
            most = max(category)
            for i, val in enumerate(category):
                if val == most:
                    self.collect_achievement(self.players[i])

        donations = [p.donations for p in self.players]
        values = sorted(list(set(donations)), reverse=True)
        for i, val in enumerate(donations):
            if val > 0:
                self.players[i].points += TEMPLE_PTS[values.index(val)]

        self.turn = self.Action.FINISHED

    def players_beaten(self, player_index):
        player = self.players[player_index]
        num = 0
        for i, opponent in enumerate(self.players):
            if i != player_index:
                if player.points > opponent.points:
                    num += 1
                elif player.points == opponent.points:
                    if player.achievements > opponent.achievements:
                        num += 1
                    elif player.achievements == opponent.achievements:
                        num += 0.5
        return num

    def is_over(self):
        return self.turn == self.turn.FINISHED

    def move_choices(self) -> List[int]:
        player = self.players[self.whose_turn]
        choices = []
        for pos in range(self.positions[self.whose_turn] + 1, len(self.board)):
            if (
                pos in self.positions
                or (not self.on_road(pos) and pos + 1 not in self.positions)
                or (
                    (
                        self.board[pos] == self.Space.SHOP
                        or self.board[pos] == self.Space.TEMPLE
                    )
                    and player.coins < 1
                )
                or (
                    self.board[pos] == self.Space.FIELD
                    and player.panoramas["field"] >= SECTIONS["field"]
                )
                or (
                    self.board[pos] == self.Space.MOUNTAIN
                    and player.panoramas["mountain"] >= SECTIONS["mountain"]
                )
                or (
                    self.board[pos] == self.Space.LAKE
                    and player.panoramas["lake"] >= SECTIONS["lake"]
                )
            ):
                continue

            choices.append(pos)

            if self.board[pos] == self.Space.INN:
                return choices

    def purchase_choices(self) -> List[List[Item]]:
        player = self.players[self.whose_turn]
        powerset = itr.chain.from_iterable(
            itr.combinations(self.available_souvenirs, r)
            for r in range(len(self.available_souvenirs) + 1)
        )
        return (
            [
                comb
                for comb in powerset
                if sum([souvenir.cost for souvenir in comb])
                - max([souvenir.cost for souvenir in comb], default=1)
                + 1
                <= player.coins
            ]
            if player.traveler == Traveler.Zen_emon
            else [
                comb
                for comb in powerset
                if sum([souvenir.cost for souvenir in comb]) <= player.coins
            ]
        )

    def pano_choices(self) -> List[str]:
        player = self.players[self.whose_turn]
        return [
            pano for pano, num in player.panoramas.items() if num < SECTIONS[pano]
        ] + [None]

    def meal_choices(self) -> List[Item]:
        player = self.players[self.whose_turn]
        reduction = 1 if player.traveler == Traveler.Kinko else 0
        choices = [
            meal
            for meal in self.available_meals
            if player.coins >= meal.cost - reduction and meal not in player.meals
        ] + [None]
        if (
            player.traveler == Traveler.Satsuki
            and self.satsuki_meal_draw not in player.meals
        ):
            choices.append(self.Item(self.satsuki_meal_draw.type, 0))
        return choices

    def available_actions(self) -> List:
        # returns list of legal actions for the current player

        if self.turn == self.Action.FINISHED:
            return []
        elif self.turn == self.Action.MOVE:
            return self.move_choices()
        elif self.turn == self.Action.BUY:
            return self.purchase_choices()
        elif self.turn == self.Action.DONATE:
            return list(
                range(
                    MIN_DONATIONS,
                    min(MAX_DONATIONS, self.players[self.whose_turn].coins) + 1,
                )
            )
        elif self.turn == self.Action.CHOOSE_ENCOUNTER:
            return self.encounter_choices + [None]
        elif self.turn == self.Action.CHOOSE_PANORAMA:
            return self.pano_choices()
        elif self.turn == self.Action.EAT:
            return self.meal_choices()

    def collect_achievement(self, player: Player):
        player.achievements += 1
        player.points += ACHIEVEMENT_PTS
        if player.traveler == Traveler.Mitsukuni:
            player.points += 1

    def collect_encounter(self, player: Player, typ):
        # returns true if the player may choose a panorama

        player.encounters += 1
        if player.traveler == Traveler.Umegae:
            player.points += 1
            player.coins += 1

        if typ == "souvenir":
            item = self.draw_cards("souvenirs", 1)[0]
            self.collect_souvenir(player, item.type)
        elif typ == "coins":
            player.coins += ENCOUNTER_VALUE["coins"]
        elif typ == "points":
            player.points += ENCOUNTER_VALUE["points"]
        elif typ == "donations":
            player.donations += ENCOUNTER_VALUE["donations"]
            player.points += ENCOUNTER_VALUE["donations"] * DONATION_PTS
        elif player.panoramas[typ] < SECTIONS[typ]:
            self.collect_panorama(player, typ)
        else:
            return True
        return False

    def collect_souvenir(self, player: Player, typ):
        souvenirs = player.souvenirs
        assert (
            typ in souvenirs
        ), "Attempted to collect {}, which is not a souvenir".format(typ)
        pos = sum([n > souvenirs[typ] for n in souvenirs.values()])
        souvenirs[typ] += 1
        player.points += SOUVENIR_PTS[pos]

    def collect_panorama(self, player: Player, pano):
        assert (
            player.panoramas[pano] < SECTIONS[pano]
        ), "Attempted to collect a {}, but that panorama is already complete".format(
            pano
        )
        player.panoramas[pano] += 1
        player.points += player.panoramas[pano]
        if player.panoramas[pano] == SECTIONS[pano] and self.pano_achievments[pano]:
            self.pano_achievments[pano] = False
            self.collect_achievement(player)

    def draw_cards(self, typ, num) -> list:
        cards = []
        pile = self.cards[typ]
        while len(cards) < num and len(pile) > 0:
            cards.append(pile.pop(random.randrange(len(pile))))
        return cards

    def take_action(self, action) -> str:
        # transitions to next state
        assert (
            self.turn != self.Action.FINISHED
        ), "Attempted to take a turn when the game is finished"

        player = self.players[self.whose_turn]

        if self.turn == self.Action.MOVE:
            assert action in self.move_choices(), "Attempted an illegal move"

            self.positions[self.whose_turn] = action
            space = self.board[action]

            if space == self.Space.INN:
                if player.traveler == Traveler.Satsuki:
                    self.satsuki_meal_draw = self.draw_cards("meals", 1)[0]

                    return "Satsuki arrives at the next inn is offered {} for free".format(
                        self.satsuki_meal_draw.type
                    )

                if action < len(self.board) - 5 and player.traveler == Traveler.Chuubei:
                    encounter = self.draw_cards("encounters", 1)[0]
                    if self.collect_encounter(player, encounter):
                        self.turn = self.Action.CHOOSE_PANORAMA
                    else:
                        self.next_player_turn()

                    return "Chuubei arrives at the next inn and receives {} from an encounter".format(
                        encounter
                    )

                if (
                    action < len(self.board) - 5
                    and player.traveler == Traveler.Hiroshige
                ):
                    self.turn = self.Action.CHOOSE_PANORAMA
                else:
                    self.next_player_turn()

                return "{} arrives at the next inn".format(player.traveler.name)

            elif space == self.Space.SHOP:
                self.available_souvenirs = self.draw_cards(
                    "souvenirs", SOUVENIRS_OFFERED
                )
                self.turn = self.Action.BUY

                return "{0} goes to a shop and is offered {1}".format(
                    player.traveler.name, self.available_souvenirs
                )

            elif space == self.Space.TEMPLE:
                self.turn = self.Action.DONATE

                return "{} visits a temple".format(player.traveler.name)

            elif space == self.Space.ENCOUNTER:
                if player.traveler == Traveler.Yoshiyasu:
                    self.encounter_choices = self.draw_cards("encounters", 2)
                    self.turn = self.Action.CHOOSE_ENCOUNTER

                    return "Yoshiyasu has a choice between {0} and {1} encounters".format(
                        self.encounter_choices[0], self.encounter_choices[1]
                    )

                else:
                    encounter = self.draw_cards("encounters", 1)[0]
                    if self.collect_encounter(player, encounter):
                        self.turn = self.Action.CHOOSE_PANORAMA
                    else:
                        self.next_player_turn()

                    return "{0} receives {1} from an encounter".format(
                        player.traveler.name, encounter
                    )

            elif space == self.Space.FARM:
                player.coins += FARM_PAYMENT
                self.next_player_turn()

                return "{0} works at a farm".format(player.traveler.name)

            elif space == self.Space.HOT_SPRING:
                bath = self.draw_cards("baths", 1)[0]
                player.points += bath
                player.baths += 1
                if player.traveler == "Mitsukuni":
                    player.pts += 1
                self.next_player_turn()

                return "{0} takes a bath for {1} points".format(
                    player.traveler.name, bath
                )

            else:
                self.collect_panorama(player, space.name.lower())
                self.next_player_turn()

                return "{0} visits a {1}".format(
                    player.traveler.name, space.name.lower()
                )

        elif self.turn == self.Action.BUY:
            assert (
                len(
                    [
                        souvenir
                        for souvenir in action
                        if souvenir not in self.available_souvenirs
                    ]
                )
                == 0
            ), "Attempted to buy a souvenir that is not for sale"

            coins_needed = sum([souvenir.cost for souvenir in action])
            if player.traveler == Traveler.Zen_emon:
                coins_needed -= (
                    max([souvenir.cost for souvenir in action], default=1) - 1
                )
            assert (
                coins_needed <= player.coins
            ), "Attempted to spend coins you do not have at a shop"

            for souvenir in action:
                player.coins -= souvenir.cost
                self.collect_souvenir(player, souvenir.type)
                self.available_souvenirs.remove(souvenir)

            self.cards["souvenirs"].extend(self.available_souvenirs)

            if player.traveler == Traveler.Zen_emon:
                player.coins += (
                    max([souvenir.cost for souvenir in action], default=1) - 1
                )
            if player.traveler == Traveler.Sasayakko and len(action) >= 2:
                player.coins += min([souvenir.cost for souvenir in action])

            self.next_player_turn()

            return "{0} purchases {1}".format(player.traveler.name, action)

        elif self.turn == self.Action.DONATE:
            assert (
                action >= MIN_DONATIONS
            ), "Attempted to donate too few coins to a temple"
            assert (
                action <= MAX_DONATIONS
            ), "Attempted to donate too many coins to a temple"
            assert (
                action <= player.coins
            ), "Attempted to spend coins you do not have at a temple"
            player.coins -= action
            if player.traveler == "Hirotoda":
                action += 1
            player.points += action * DONATION_PTS
            player.donations += action

            self.next_player_turn()

            return "{0} donates {1} coins".format(player.traveler.name, action)

        elif self.turn == self.Action.CHOOSE_ENCOUNTER:
            if action != None:
                assert (
                    action in self.encounter_choices
                ), "Attempted to choose {}, which is not an available encounter".format(
                    action
                )
                self.encounter_choices.remove(action)
            self.cards["encounters"].extend(self.encounter_choices)
            if action != None and self.collect_encounter(player, action):
                self.turn = self.Action.CHOOSE_PANORAMA
            else:
                self.next_player_turn()

            return "{0} chooses a {1} encounter".format(player.traveler.name, action)

        elif self.turn == self.Action.CHOOSE_PANORAMA:
            assert (
                action in self.pano_choices()
            ), "Attempted to choose a {}, which is an illegal panorama".format(action)
            if action != None:
                self.collect_panorama(player, action)
            self.next_player_turn()

            return "{0} chooses a {1} panorama".format(player.traveler.name, action)

        elif self.turn == self.Action.EAT:
            if action != None:
                reduction = 1 if player.traveler == Traveler.Kinko else 0
                free_meal = player.traveler == Traveler.Satsuki and action.cost == 0
                meal = self.satsuki_meal_draw if free_meal else action
                assert (
                    action in self.available_meals or free_meal
                ), "Attempted to buy a {}, which is not an available meal".format(
                    action.type
                )
                assert (
                    meal not in player.meals
                ), "Attempted to buy a {}, which you have already eaten".format(
                    action.type
                )
                assert (
                    action.cost - reduction <= player.coins
                ), "Attempted to spend coins you do not have at an inn"
                player.points += MEAL_PTS
                player.coins -= action.cost - reduction
                player.meals.append(meal)
                if not free_meal:
                    self.available_meals.remove(action)

            self.next_player_turn()

            return (
                "{} skips a meal".format(player.traveler.name)
                if action == None
                else "{0} buys {1} for {2} coins".format(
                    player.traveler.name, action.type, action.cost
                )
            )

    def random_playout(self):
        while self.turn != self.Action.FINISHED:
            options = self.available_actions()
            if self.turn == self.Action.MOVE:
                weights = list(itr.accumulate([0.5] * len(options), lambda x, y: x * y))
                action = random.choices(options, weights)[0]
            else:
                action = random.choice(options)
            self.take_action(action)
