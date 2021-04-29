import time
from functools import lru_cache

cards = []
# r-g r-g b-g b-r r-b b-b g-b b-r g-r g-r r-g r-g b-g b-r r-b b-b g-b b-r g-r g-r r-g r-g b-g b-r r-b b-b g-b b-r g-r g-r r-g r-g b-g b-r r-b b-b g-b b-r g-r g-r r-g r-g b-g b-r r-b b-b g-b b-r g-r g-r
# get input
for _ in range(int(input())):
    num_cards = int(input().strip())
    raw_cards = input().strip().split()
    # for each card, find cards that can go on top
    @lru_cache(None)
    def num_more_cards(stack, last_tops):
        max_num = 0
        # for each card that can go on top, find the number that can go on top
        for card_index in last_tops:
            # make sure it hasn't been used up already
            if cards[card_index][2] - stack[card_index] <= 0: continue
            # update stack
            new_stack = list(stack); new_stack[card_index] += 1; new_stack = tuple(new_stack)
            # amount that can go on top, plus one for the card considered in the loop
            max_num = max(max_num, num_more_cards(new_stack, cards[card_index][1]) + 1)
        return max_num
    start = time.process_time()
    # sides, can go on top, num
    cards = []
    found_cards = set()
    # process input into list of cards
    for raw_card in raw_cards:
        # seperate top and bottom sides
        card_sides = tuple(raw_card.split('-'))
        # add to cards
        if not card_sides in found_cards: found_cards.add(card_sides); cards.append([card_sides, (), 1])
        else: 
            for card in cards:
                if card[0] == card_sides: card[2] += 1; break
    # find all cards that can go on top of every card
    for i, card in enumerate(cards):
        for j, potential_top in enumerate(cards):
            if card[0][1] == potential_top[0][0]:
                card[1] += (j,)
    max_length = 0
    print("time before search:", time.process_time()-start); start = time.process_time()
    # for each card, find number that can go on top
    for i, card in enumerate(cards):
        stack = [0 for _ in cards]; stack[i] += 1; stack = tuple(stack)
        max_length = max(max_length, num_more_cards(stack, card[1]) + 1)
    print(max_length)
    print("time to search:", time.process_time()-start)