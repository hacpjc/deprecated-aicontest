# coding=utf-8

#
# Heart Poker Game
#

from deuces import Card
import sys
import random

from htapi import htapi, htplayer, htgame

class hacbot(htapi):
    ht = htapi()
    
    def __init__(self):
        pass
    
    def deal(self, data):
        """
        You get the 13 cards.
        """
        my_unused_card = data['player_unused_card']
        
    def __select_card_to_pass(self, my_avail_card):
        """
        Always select 'Ks', 'As' first
        """
        card = self.ht.card_remove(my_avail_card, self.ht.str2card('Ks', fixfmt=False))
        if card != None:
            return card
        
        card = self.ht.card_remove(my_avail_card, self.ht.str2card('As', fixfmt=False))
        if card != None:
            return card
        
        # TODO: Also try to remove a suit
        suit_list = [self.ht.str2suit('Spade'), self.ht.str2suit('Heart'), self.ht.str2suit('Diamond'), self.ht.str2suit('Club')]
        pick_suit = suit_list[0]
        pick_suit_num = self.ht.calc_card_num_by_suit(pick_suit, my_avail_card) 
        for suit in suit_list:
            num = self.ht.calc_card_num_by_suit(suit, my_avail_card)
            print ("Have " + str(num) + " cards")
            
            if pick_suit_num == 0:
                pick_suit = suit
                pick_suit_num = num
            
            if num != 0 and num < pick_suit_num:
                pick_suit = suit
                pick_suit_num = num
                
        candidate_list = self.ht.card_select_by_suit(pick_suit, my_avail_card)        
        card = candidate_list.pop()
        my_avail_card.remove(card) # Remove to avoid selecting this card again.
        return card
    
    def time2pass(self, data):
        """
        Select 3 cards to pass. Cannot select '2c'
        """
        my_all_card = data['unused_card']
        my_avail_card = data['avail_card']
        
        output = []
        
        for i in range(3):
            c = self.__select_card_to_pass(my_avail_card)
            print ("Select card: " + self.ht.get_card_pretty(c))
            output.append(c)
    
        return output
    
    def __pick_small_card(self, card_list):
        small_card = card_list[0]
        small_card_rank = self.ht.get_card_rank(small_card)
        for c in card_list:
            if self.ht.get_card_rank(c) < small_card_rank:
                small_card = c
                small_card_rank = self.ht.get_card_rank(c)
            
        return small_card
    
    def __pick_smaller_card(self, card_list, card_list2cmp):
        candidate = []
        
        for c2cmp in card_list2cmp:
            for c in card_list:
                if self.ht.get_card_rank(c) < self.ht.get_card_rank(c2cmp):
                    candidate.append(c)
        
        if len(candidate) > 0:
            return candidate.pop() # This is the largest & smaller card
        else:
            return self.__pick_big_card(card_list)
    
    def __pick_big_card(self, card_list):
        big_card = card_list[0]
        big_card_rank = self.ht.get_card_rank(big_card)
        for c in card_list:
            if self.ht.get_card_rank(c) < big_card_rank:
                big_card = c
                big_card_rank = self.ht.get_card_rank(c)
            
        return big_card
    
    def __leadplay(self, data):
        """
        I am the round leader. Play the trick.
        """

        """
        Just pick a small card, so that i can win?
        
        TOOD: This is actually stupid... improve.
        """
        return self.__pick_small_card(self.my_avail_card)
    
    def __midplay(self, data):
        lead_card = self.all_board_card[0]
        my_lead_suit_num = self.ht.calc_card_num_by_suit(self.ht.get_card_suit(lead_card), self.my_avail_card)
        
        board_score = self.ht.cardl2htpoint(self.all_board_card)
        if my_lead_suit_num > 0:
            """
            Have the same suit. Choose a smaller card to avoid the trick.
            """
            return self.__pick_smaller_card(self.my_avail_card, self.all_board_card)
        else:
            """
            I don't have the same suit. Throw dangerous high point first. 
            """
            high_card = self.__pick_big_card(self.my_avail_card)
            if self.ht.get_card_rank(high_card) >= self.ht.str2rank('Q'):
                return high_card
            
            """
            I don't have the same suit. My chance to throw out point cards!
            """
            candidate_list = []
            candidate_list += self.ht.card_select_by_suit(self.ht.str2suit('Heart'), self.my_avail_card)
            candidate_list += self.ht.card_select_by_card_list([self.ht.str2card('Qs', fixfmt=False)], self.my_avail_card)
            
            if len(candidate_list) > 0:
                return candidate_list.pop()
             
            return high_card
    
    def __lastplay(self, data):
        lead_card = self.all_board_card[0]
        my_lead_suit_num = self.ht.calc_card_num_by_suit(self.ht.get_card_suit(lead_card), self.my_avail_card)
        
        board_score = self.ht.cardl2htpoint(self.all_board_card)
        if my_lead_suit_num > 0:
            """
            Have the same suit. If there's no point on board, shoot the biggest card.
            If there's a point, try to avoid.
            """   
            if board_score == 0:         
                return self.__pick_big_card(self.my_avail_card)
            else:
                return self.__pick_smaller_card(self.my_avail_card, self.all_board_card)
        else:
            """
            I don't have the same suit. Throw dangerous high point first. 
            """
            high_card = self.__pick_big_card(self.my_avail_card)
            if self.ht.get_card_rank(high_card) >= self.ht.str2rank('T'):
                return high_card
            
            """
            I don't have the same suit. My chance to throw out point cards!
            """
            return high_card
    
    def time2shoot(self, data):
        """
        Select a available card to shoot
        """
        self.all_used_card = data['used_card'][:]
        self.all_unused_card = data['unused_card'][:]
        self.all_board_card = data['board_card'][:]
        self.is_hb = data['is_hb']
        self.roundnum = data['roundnum']
        self.my_unused_card = data['player_unused_card'][:]
        self.my_avail_card = data['avail_card'][:]

        print ("unused card: " + self.ht.get_card_pretty_list(self.my_unused_card))
        print ("avail card: " + self.ht.get_card_pretty_list(self.my_avail_card))
                        
        if len(self.all_board_card) == 3:
            """
            Last play
            """
            card = self.__lastplay(data)
        elif len(self.all_board_card) > 0:
            """
            Middle play
            """
            card = self.__midplay(data)
        else:
            """
            Lead play
            """
            card = self.__leadplay(data)
        
        print (" -> shoot card: " + self.ht.get_card_pretty(card))
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

class randomai(htapi):
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
        
        self.ht.msg("My card before exchange: " + self.ht.get_card_pretty_list(my_unused_card))
    
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
        self.all_used_card = data['used_card'][:]
        self.all_unused_card = data['unused_card'][:]
        self.all_board_card = data['board_card'][:]
        self.is_hb = data['is_hb']
        self.roundnum = data['roundnum']
        self.my_unused_card = data['player_unused_card'][:]
        self.my_avail_card = data['avail_card'][:]

        print ("unused card: " + self.ht.get_card_pretty_list(self.my_unused_card))
        print ("avail card: " + self.ht.get_card_pretty_list(self.my_avail_card))
        
        card = random.choice(self.my_avail_card)
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
    htp = htplayer("hac", "54088", randomai)

    print (format(htp.get_stat_dict()))

def test_htgame():
    htl = []
    htl.append(htplayer("hac", "54088", hacbot))
    htl.append(htplayer("selmon", "54099", randomai))
    htl.append(htplayer("spoka", "52252", randomai))
    htl.append(htplayer("franklin", "59467", randomai))

    game = htgame(htl)

    for gamenum in range(2000):
        game.auto_deal()    
        for roundnum in range(1, 14):
            game.auto_progress()
        game.display_game_result()
        game.nextgame()
        

def unitest():
#     test_htapi()
#     test_htplayer()
    test_htgame()

if __name__ == '__main__':
    unitest()

#;
