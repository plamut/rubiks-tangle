# -*- coding: utf-8 -*-
from __future__ import print_function

import cStringIO
from collections import namedtuple


TermColors = dict(
    BOLD='\033[1m',
    INV='\033[7m',  # inverted background and foreground
    RESET='\033[0m',
)
TermColors = namedtuple('TermColors', TermColors.keys())(*TermColors.values())


class Card(object):
    """A card which can be placed onto the game panel.

    It can be placed either with its front or back side up and with its main
    edge facing one of the four possible directions (north, east, south, west)
    resulting in 8 different possible placements.
    """
    # F - front side up, B - back side up
    # N, E, S, W - orientation of the card's reference (main) edge
    Orientation = namedtuple(
        'Orientation', ['FN', 'FE', 'FS', 'FW', 'BN', 'BE', 'BS', 'BW'])
    Orientation = Orientation(*xrange(8))

    Color = namedtuple('Color', ['UNKNOWN', 'BLUE', 'GREEN', 'RED', 'YELLOW'])
    Color = Color(*xrange(-1, 4))

    def __init__(self, card_id, edges, orientation=Orientation.FN):
        """Create a new card instance.

        :param card_id: card's identifier (must be unique!)
        :param edges: list of descriptions of card edges' colors with each
            description being a two-tuple (color1, color2). The following
            edge order is assumed: FN, FE, FS, FW, BN, BE, BS, BW
            (clockwise starting with NORTH, FRONT side first)
        :param orientation: card's orientation
        """
        self.card_id = card_id
        self.edges = edges
        self.orientation = orientation

    def __eq__(self, other):
        return (other is not None) and self.card_id == other.card_id

    def __ne__(self, other):
        return (other is None) or self.card_id != other.card_id

    def __getitem__(self, item_idx):
        """Return card's color at item_idx on the side currently facing up
        (taking the current card orientation into account).

        item_idx:
           0 1
          7   2
          6   3
           5 4
        """
        # adjust index for card's rotation
        idx = (item_idx - 2 * (self.orientation % 4)) % 8

        if self.orientation < 4:  # front side up
            return (self.edges[idx // 2])[idx % 2]
        else:
            return (self.edges[idx // 2 + 4])[idx % 2]

    def __setitem__(self, item_idx, item):
        """Prevent any subsequent modifications of the card's edge colors."""
        raise TypeError("Modifying card colors not allowed.")


class GamePanel(object):
    """Representation of the game panel with 9 slots for cards.

    A note on the card placement: if the card is placed with its back side up,
    it is not "physically turned around". Instead the back side "bubbles up"
    to the surface so that the front side is now behind (under) it.
    This way the card's edge indexes are not mirrored, simplyfying some
    calculations.

    Indexes of panel's slots (where the cards can be placed):
    0 1 2
    3 4 5
    6 7 8
    """
    # a mapping of Card.Color to the colors in the output to the terminal
    COLOR_STR = {
        Card.Color.UNKNOWN: ' ',
        Card.Color.BLUE: '\033[34mB\033[0m',
        Card.Color.GREEN: '\033[32mG\033[0m',
        Card.Color.RED: '\033[31mR\033[0m',
        Card.Color.YELLOW: '\033[33mY\033[0m',
    }

    # indexes of slots adjacent to a particular slot
    NeighborIdx = namedtuple('NeighborIdx', ['north', 'east', 'south', 'west'])
    SLOT_NEIGHBORS = (
        #(NORTH, EAST, SOUTH, WEST)
        NeighborIdx(None, 1, 3, None),
        NeighborIdx(None, 2, 4, 0),
        NeighborIdx(None, None, 5, 1),
        NeighborIdx(0, 4, 6, None),
        NeighborIdx(1, 5, 7, 3),
        NeighborIdx(2, None, 8, 4),
        NeighborIdx(3, 7, None, None),
        NeighborIdx(4, 8, None, 6),
        NeighborIdx(5, None, None, 7),
    )

    def __init__(self):
        self.slots = [None] * 9
        # current empty slot where new card will be placed
        # defaults to 0 (upper-left corner)
        self.curr_slot = 0

    def __str__(self):
        Color = Card.Color

        output = cStringIO.StringIO()
        output.write(''.join(['+', '-----+' * 3, '\n']))

        for row in range(3):
            # each card is displayed in 5 text lines, 3 cards per each
            # game panel row
            cards_in_row = self.slots[row * 3: row * 3 + 3]
            # 1st line
            for card in cards_in_row:
                # highlight card's edge if oriented to north
                TermColors.INV
                rev = TermColors.INV if card.orientation in (0, 4) else ''

                color1, color2 = (card[0], card[1]) if card \
                    else (Color.UNKNOWN, Color.UNKNOWN)
                output.write('| {rev}{0}{reset} {rev}{1}{reset} '.format(
                    self.COLOR_STR[color1], self.COLOR_STR[color2],
                    rev=rev, reset=TermColors.RESET)
                )
            output.write('|\n')

            # 2nd line
            for card in cards_in_row:
                # highlight western edge if the card is oriented to the west
                rev_w = TermColors.INV if card.orientation in (3, 7) else ''

                # highlight eastern edge if the card oriented to the east
                rev_e = TermColors.INV if card.orientation in (1, 5) else ''

                color1, color2 = (card[7], card[2]) if card \
                    else (Color.UNKNOWN, Color.UNKNOWN)
                output.write('|{rev_w}{}{reset}   {rev_e}{}{reset}'.format(
                    self.COLOR_STR[color1], self.COLOR_STR[color2],
                    rev_w=rev_w, rev_e=rev_e, reset=TermColors.RESET)
                )
            output.write('|\n')

            # 3rd line
            for card in cards_in_row:
                # highlight western edge if the card is oriented to the west
                rev_w = TermColors.INV if card.orientation in (3, 7) else ''

                # highlight eastern edge if the card oriented to the east
                rev_e = TermColors.INV if card.orientation in (1, 5) else ''

                color1, color2 = (card[6], card[3]) if card \
                    else (Color.UNKNOWN, Color.UNKNOWN)
                output.write('|{rev_w}{}{reset}   {rev_e}{}{reset}'.format(
                    self.COLOR_STR[color1], self.COLOR_STR[color2],
                    rev_w=rev_w, rev_e=rev_e, reset=TermColors.RESET)
                )
            output.write('|\n')

            # 4th line
            for card in cards_in_row:
                # highlight card's edge if oriented to south
                rev = TermColors.INV if card.orientation in (2, 6) else ''

                color1, color2 = (card[5], card[4]) if card else \
                    (Color.UNKNOWN, Color.UNKNOWN)
                output.write('| {rev}{}{reset} {rev}{}{reset} '.format(
                    self.COLOR_STR[color1], self.COLOR_STR[color2],
                    rev=rev, reset=TermColors.RESET)
                )
            output.write('|\n')

            # 5th line
            output.write(''.join(['+', '-----+' * 3, '\n']))

        placement = []
        for i, c in enumerate(self.slots):
            if i % 3 == 0:
                placement.append('\n')
            if c is not None:
                # facing = "down" if c.orientation // 4 else "up"
                placement.append('{bold}{}{reset}({bold}{}{reset})'.format(
                    c.card_id, c.Orientation._fields[c.orientation],
                    bold=TermColors.BOLD, reset=TermColors.RESET)
                )

        output.write("CARD PLACEMENT: {0}".format(' '.join(placement)))

        contents = output.getvalue()
        output.close()
        return contents

    def can_place(self, card):
        """Can we place a card into the currently first empty slot?

        We must check all cards in adjacent slots to verify that all edge
        colors match.
        """
        # northern neighbor
        idx = GamePanel.SLOT_NEIGHBORS[self.curr_slot].north
        neighbor_card = self.slots[idx] if (idx is not None) else None
        if neighbor_card is not None:
            if (card[0] != neighbor_card[5]) or (card[1] != neighbor_card[4]):
                return False

        # eastern neighbor
        idx = GamePanel.SLOT_NEIGHBORS[self.curr_slot].east
        neighbor_card = self.slots[idx] if (idx is not None) else None
        if neighbor_card is not None:
            if (card[2] != neighbor_card[7]) or (card[3] != neighbor_card[6]):
                return False

        # southern neighbor
        idx = GamePanel.SLOT_NEIGHBORS[self.curr_slot].south
        neighbor_card = self.slots[idx] if (idx is not None) else None
        if neighbor_card is not None:
            if (card[5] != neighbor_card[0]) or (card[4] != neighbor_card[1]):
                return False

        # western neighbor
        idx = GamePanel.SLOT_NEIGHBORS[self.curr_slot].west
        neighbor_card = self.slots[idx] if (idx is not None) else None
        if neighbor_card is not None:
            if (card[7] != neighbor_card[2]) or (card[6] != neighbor_card[3]):
                return False

        return True

    def place(self, card):
        self.slots[self.curr_slot] = card
        self.curr_slot += 1
        # XXX: automatically update list of cards available for placing?

    def remove_last(self):
        assert self.curr_slot > 0, "No cards to remove"
        self.curr_slot -= 1
        assert self.slots[self.curr_slot] is not None, \
            "Can't remove card that isn't there"
        self.slots[self.curr_slot] = None
        # XXX: automatically update list of cards available for placing?


def generate_cards():
    """Generate and return a list of all cards in the game."""
    Color = Card.Color  # just to save some typing ...
    card_edges = [
        [(Color.GREEN, Color.BLUE), (Color.RED, Color.GREEN),
         (Color.BLUE, Color.YELLOW), (Color.RED, Color.YELLOW),
         (Color.YELLOW, Color.BLUE), (Color.RED, Color.YELLOW),
         (Color.BLUE, Color.GREEN), (Color.RED, Color.GREEN)
         ],

        [(Color.GREEN, Color.YELLOW), (Color.BLUE, Color.RED),
         (Color.GREEN, Color.BLUE), (Color.RED, Color.YELLOW),
         (Color.YELLOW, Color.GREEN), (Color.RED, Color.BLUE),
         (Color.YELLOW, Color.BLUE), (Color.GREEN, Color.RED)
         ],

        [(Color.GREEN, Color.RED), (Color.YELLOW, Color.BLUE),
         (Color.GREEN, Color.YELLOW), (Color.BLUE, Color.RED),
         (Color.YELLOW, Color.RED), (Color.BLUE, Color.GREEN),
         (Color.YELLOW, Color.GREEN), (Color.RED, Color.BLUE)
         ],

        [(Color.BLUE, Color.YELLOW), (Color.RED, Color.GREEN),
         (Color.BLUE, Color.GREEN), (Color.YELLOW, Color.RED),
         (Color.GREEN, Color.BLUE), (Color.YELLOW, Color.RED),
         (Color.GREEN, Color.YELLOW),
         (Color.RED, Color.BLUE)
         ],

        [(Color.YELLOW, Color.RED), (Color.GREEN, Color.BLUE),
         (Color.YELLOW, Color.BLUE), (Color.RED, Color.GREEN),
         (Color.BLUE, Color.RED), (Color.YELLOW, Color.GREEN),
         (Color.BLUE, Color.YELLOW), (Color.GREEN, Color.RED)
         ],

        [(Color.BLUE, Color.RED), (Color.GREEN, Color.YELLOW),
         (Color.BLUE, Color.YELLOW), (Color.RED, Color.GREEN),
         (Color.RED, Color.BLUE), (Color.YELLOW, Color.GREEN),
         (Color.RED, Color.YELLOW), (Color.GREEN, Color.BLUE)
         ],

        [(Color.YELLOW, Color.GREEN), (Color.BLUE, Color.RED),
         (Color.YELLOW, Color.RED), (Color.GREEN, Color.BLUE),
         (Color.GREEN, Color.YELLOW), (Color.RED, Color.BLUE),
         (Color.GREEN, Color.RED), (Color.BLUE, Color.YELLOW)
         ],

        [(Color.RED, Color.YELLOW), (Color.BLUE, Color.YELLOW),
         (Color.GREEN, Color.RED), (Color.BLUE, Color.GREEN),
         (Color.RED, Color.GREEN), (Color.YELLOW, Color.GREEN),
         (Color.BLUE, Color.RED), (Color.YELLOW, Color.BLUE)
         ],

        [(Color.GREEN, Color.RED), (Color.YELLOW, Color.RED),
         (Color.BLUE, Color.GREEN), (Color.YELLOW, Color.BLUE),
         (Color.GREEN, Color.YELLOW), (Color.RED, Color.YELLOW),
         (Color.BLUE, Color.GREEN), (Color.RED, Color.BLUE)
         ],
    ]

    cards = []
    for index, edges in enumerate(card_edges):
        cards.append(Card(index+1, edges))

    return cards


def solve_problem(panel, avail_cards):
    global COMBOS

    if not avail_cards:
        yield panel   # all cards have been placed, we have a solution
    else:
        for card in avail_cards:
            for orientation in Card.Orientation:
                COMBOS += 1
                # copy needed? just remove it form the list/set!
                # XXX: profile!
                new_card = Card(card.card_id, card.edges, orientation)

                if not panel.can_place(new_card):
                    continue
                else:
                    panel.place(new_card)

                    # XXX: not efficient this copying back and forth?
                    new_cards_avail = \
                        [x for x in avail_cards if x != new_card]

                    for solved_panel in solve_problem(panel, new_cards_avail):
                        yield solved_panel

                    # after examining all sub-placings, remove last placed card
                    # and try with another card/orientation in the next
                    # iteration
                    panel.remove_last()


if __name__ == "__main__":
    COMBOS = 0
    n_solutions = 0

    cards = generate_cards()
    panel = GamePanel()

    for solved_panel in solve_problem(panel, cards):
        n_solutions += 1
        print(solved_panel, "\n")
        # break  # uncomment if you don't want ALL solutions

    print("*** SOLUTIONS FOUND: ",
          TermColors.BOLD, n_solutions, TermColors.RESET, sep='')
    print("*** COMBINATIONS CHECKED: ",
          TermColors.BOLD, COMBOS, TermColors.RESET, sep='')
