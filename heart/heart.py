#
# Heart Poker Game
#

from deuces import Card
import sys

from htapi import htapi, htplayer, htgame

def test_htapi():
    myht = htapi()
    
    cards = myht.strl2card(True, "AD", "AH", "AS", "AC")
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
    
def test_htplayer():
    htp = htplayer("hac", "54088")
    
    print (format(htp.get_stat_dict()))

def test_htgame():
    htl = []
    
    htp = htplayer("hac", "54088")
    htl.append(htp)
    
    htp = htplayer("xxx", "11111")
    htl.append(htp)
    
    game = htgame(htl)

    print ("")    
    print (format(game.get_stat_dict()))
    
    game.do_shoot('54088', Card.new('Qs'))
    
    print ("")
    print (format(game.get_stat_dict()))
    
    game.do_shoot('11111', Card.new('As'))
    
    print ("")
    print (format(game.get_stat_dict()))
    
    game.nextround()


def unitest():
    test_htapi()
    test_htplayer()
    test_htgame()

if __name__ == '__main__':
    unitest()
    
#;