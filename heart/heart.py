# coding=utf-8

#
# Heart Poker Game
#

from deuces import Card
import sys

from htapi import htapi, htplayer, htgame

class dummyai(htapi):
    ht = htapi()
    
    def __init__(self):
        pass
    
    def time2shoot(self, data):
        unused_card = data['avail_card']
        
        print ("...avail card: " + self.ht.get_card_pretty_list(unused_card))
        card = unused_card[0]
        print ("...shoot card: " + self.ht.get_card_pretty(card))
        return card

def test_htapi():
    myht = htapi()

    cards = myht.strl2card(["AD", "AH", "AS", "AC"], True)
    for c in cards:
        print (myht.get_card_rank(c), myht.get_card_suit(c))
        print (myht.get_card_pretty(c))
        sys.stdout.flush()

    print(myht.get_card_pretty_list(cards))

    allcard = myht.get_all_card()
    print (myht.get_card_pretty_list(allcard))
    for c in allcard:
        print (myht.get_card_rank(c), myht.get_card_suit(c))
        print (myht.get_card_pretty(c))
        sys.stdout.flush()
        
    print ("Card rank 'A': " + str(myht.str2rank('A')))
    print ("Card suit 'Spade': " + str(myht.str2suit('Spade')))
    

def test_htplayer():
    htp = htplayer("hac", "54088", dummyai)

    print (format(htp.get_stat_dict()))

def test_htgame():
    htl = []
    htl.append(htplayer("hac", "54088", dummyai))
    htl.append(htplayer("aaa", "11111", dummyai))
    htl.append(htplayer("bbb", "22222", dummyai))
    htl.append(htplayer("ccc", "33333", dummyai))

    game = htgame(htl)

    game.auto_deal()

    for roundnum in range(1, 14):
        game.auto_progress()
        

def unitest():
    test_htapi()
    test_htplayer()
    test_htgame()

if __name__ == '__main__':
    unitest()

#;
