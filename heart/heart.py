# coding=utf-8

#
# Heart Poker Game
#

from deuces import Card
import sys
import random

from htapi import htapi, htplayer, htgame

class dummyai(htapi):
    """
    This is a random play bot. Use this as template and create your smart bot!
    """
    ht = htapi()
    
    def __init__(self):
        pass
    
    def deal(self, data):
        """
        You get the 13 cards.
        """
        my_unused_card = data['player_unused_card']
        
        self.ht.msg("My card: " + self.ht.get_card_pretty_list(my_unused_card))
    
    def time2pass(self, data):
        """
        Select 3 cards to pass. Cannot select '2c'
        """
        my_all_card = data['unused_card']
        my_avail_card = data['avail_card']
        
        output = []
        output = random.sample(my_avail_card, 3)
    
        return output
    
    def time2shoot(self, data):
        """
        Select a available card to shoot
        """
        unused_card = data['unused_card']
        avail_card = data['avail_card']
        
        print ("...unused card: " + self.ht.get_card_pretty_list(unused_card))
        print ("...avail card: " + self.ht.get_card_pretty_list(avail_card))
        card = random.choice(avail_card)
        print ("...shoot card: " + self.ht.get_card_pretty(card))
        return card
    
    
    def nextround(self, data):
        """
        next round event
        """
        pass
    
    def nextgame(self, data):
        """
        next game event
        """
        pass


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

    for gamenum in range(20):
        game.auto_deal()    
        for roundnum in range(1, 14):
            game.auto_progress()
        game.display_game_result()
        game.nextgame()
        

def unitest():
    test_htapi()
    test_htplayer()
    test_htgame()

if __name__ == '__main__':
    unitest()

#;
