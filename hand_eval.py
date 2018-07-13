# -*- coding: utf-8 -*-
"""
Created on Thu Jul 12 14:17:35 2018

@author: pingjhih_chen
"""

import random
from deuces import Card
from deuces import Evaluator

#def getCard(card):
#    card_type = card[1]
#    cardnume_code = card[0]
#    card_num = 0
#    card_num_type = 0
#    if card_type == 'S':
#        card_num_type = 1
#    elif card_type == 'H':
#        card_num_type = 2
#    elif card_type == 'D':
#        card_num_type = 3
#    else:
#        card_num_type = 4
#
#    if cardnume_code == 'T':
#        card_num = 10
#    elif cardnume_code == 'J':
#        card_num = 11
#    elif cardnume_code == 'Q':
#        card_num = 12
#    elif cardnume_code == 'K':
#        card_num = 13
#    elif cardnume_code == 'A':
#        card_num = 14
#    else:
#        card_num = int(cardnume_code)
#
#    return Card(card_num,card_num_type)


hole = [Card.new('9s'), Card.new('Ks')]
board = [Card.new('Ts'), Card.new('Js'), Card.new('Qs'), Card.new('Ah')]

evaluator = Evaluator()

score = evaluator.evaluate(board, hole)

Card.print_pretty_cards (hole)
Card.print_pretty_cards (board)

print ('score=', score)


#;