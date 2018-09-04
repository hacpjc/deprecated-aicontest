
from PokerBot import PokerBot, system_log, Card, Htapi

class HacBot(PokerBot, Htapi):
    """
    Hac's policy-based bot.
    """
    def __init__(self, name, is_debug=False):
        super(HacBot, self).__init__(name)

        self.htapi = Htapi(is_debug=is_debug)
                       
        self.players = {}
        self.stat = {}
        
        self.big_rank_cards = [
            Card('AS'), Card('KS'), Card('JS'), Card('TS'),
            Card('AH'), Card('KH'), Card('QH'), Card('JH'), Card('TH'),
            Card('AD'), Card('KD'), Card('QD'), Card('JD'), Card('TD'),
            Card('AC'), Card('KC'), Card('QC'), Card('JC'), Card('TC'), 
            ]
        
        self.score_cards = [Card("QS"), Card("TC"),
                        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
                        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
                        Card("QH"), Card("KH"), Card("AH")]
        
        self.plz_rebuild_players = True
        
    def _rebuild_players(self, data):
        """
        Configure player table by input data.
        """
        
        self.htapi.msg("Rebuild players: ", format(data))
        
        data_players = data['players']
        
        if len(data_players) != 4:
            self.errmsg("Invalid player number " + str(len(data_players)) + " in server msg")
        
        self.players = {}
        
        for dp in data_players:
            self.players[dp['playerName']] = {
                'playerName': dp['playerName'],
                'score_accl': 0,
                'score': 0,
                'shoot': [],
                'shoot_moon': 0,
                'expose': False,
                }
    
    def new_game(self, data):
        """
        Event: The start of a new game.
        """
        if self.plz_rebuild_players == True:
            self._rebuild_players(data)
            self.plz_rebuild_players = False
    
    def receive_cards(self, data):
        """
        Event: Receive my 13 cards.
        """
        self.stat['hand'] = self.get_cards(data)
        
    def _select_card2pass(self, my_hand_cards):
        
        card = self.htapi.remove_card(my_hand_cards, Card('KS'))
        if card != None:
            return card
        
        card = self.htapi.remove_card(my_hand_cards, Card('AS'))
        if card != None:
            return card
        
        # Found the suit in shortage
        suit_list = ['S', 'H', 'D', 'C']
        pick_suit = None
        pick_suit_num = 0
        for suit in suit_list:
            this_suit_num = self.htapi.calc_card_num_by_suit(my_hand_cards, suit)
            
            if this_suit_num == 0:
                continue
            
            if pick_suit_num == 0:
                pick_suit_num = this_suit_num
                pick_suit = suit
            elif this_suit_num < pick_suit_num:
                pick_suit_num = this_suit_num
                pick_suit = suit

        # Remove the most large card in the target suit        
        candidate_list = self.htapi.get_cards_by_suit(my_hand_cards, pick_suit)
        self.htapi.arrange_cards(candidate_list)
        card = candidate_list.pop()
        
        return self.htapi.remove_card(my_hand_cards, card)
    
    def pass_cards(self, data):
        """
        Event: Pick 3 cards to pass to others
        """
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        
        output = []
        for i in range(3):
            card = self._select_card2pass(my_hand_cards)
            if card == None:
                self.htapi.errmsg("Cannot pick a card to pass")
            output.append(card.toString())
            
        self.htapi.dbg(self.get_name() + " Pass 3 cards: " + format(output))
        return output

    def receive_opponent_cards(self, data):
        """
        Event: Recv 3 cards from one opponent
        """
        pass

    def expose_my_cards(self, data):
        """
        Event: The server asks me to expose AH...
        """
        my_hand_cards = self.stat['hand']
        
        output = []
        candidates = data['cards']
        if candidates == None or len(candidates) == 0:
            return output

        candidates = [Card(x) for x in candidates]
        
        if self.htapi.find_card(candidates, Card('AH')) == None:
            return output
        
        if my_hand_cards == None or len(my_hand_cards) == 0:
            return output
                
        # Calculate the rate that I will get penalty...
        # The simplest calculation is to check if I have too many big-rank cards
        big_card_num = self.htapi.find_cards(my_hand_cards, self.big_rank_cards)
        if big_card_num > (len(self.big_rank_cards) / 3):
            # Too many big-rank cards...Give up expose.
            return output
            
        output = ['AH']
        
        return output

    def expose_cards_end(self, data):
        """
        Event: Check if somebody expose AH. Damn. 
        """
        data_players = data['players']
        
        for dp in data_players:
            local_player = self.players[dp['playerName']]
            
            if len(dp['exposedCards']) > 0:
                # This guy exposed AH. 
                local_player['expose'] = True
            else:
                local_player['expose'] = False
    
    def __pick_small_card(self, card_list):
        """
        Pick the smallest card in list 
        """
        small_card = card_list[0]
        small_card_rank = small_card.get_rank_num()
        for c in card_list:
            if c.get_rank() < small_card_rank:
                small_card = c
                small_card_rank = c.get_rank_num(c)
            
        return small_card
    
    def __pick_smaller_card(self, card_list, card_list2cmp):
        """
        Pick a smaller card (but not smallest)
        """
        candidate = []
        
        for c2cmp in card_list2cmp:
            for c in card_list:
                if c.get_rank_num() < c2cmp.get_rank_num():
                    candidate.append(c)
        
        if len(candidate) > 0:
            return candidate.pop()
        else:
            # Don't have any smaller card. Give up and pick the biggest one instead.
            return self.__pick_big_card(card_list)
    
    def __pick_big_card(self, card_list):
        big_card = card_list[0]
        big_card_rank = big_card.get_rank_num()
        for c in card_list:
            if c.get_rank_num() > big_card_rank:
                big_card = c
                big_card_rank = c.get_rank_num()
        
        return big_card
    
    def __leadplay(self, data):
        """
        I am the round leader. Play the trick.
        """

        """
        Just pick a small card, so that i can win?
        
        TODO: This is actually stupid... improve.
        """
        
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        
        return self.__pick_small_card(my_hand_cards)
    
    def __midplay(self, data):
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        round_cards = [Card(x) for x in data['self']['roundCard']]
        my_hand_cards = self.stat['hand']
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]
        
        lead_card = round_cards[0]
        my_lead_suit_num = self.htapi.calc_card_num_by_suit(my_hand_cards, lead_card.get_suit())
        
        if my_lead_suit_num > 0:
            """
            Have the same suit. Choose a smaller card to avoid the trick.
            """
            return self.__pick_smaller_card(my_avail_cards, round_cards)
        else:
            """
            I don't have the same suit. Git rid of 'QS'. 
            """
            qs = self.htapi.find_card(my_avail_cards, Card('QS')) 
            if qs != None:
                return qs
            
            """
            I don't have the same suit. Throw dangerous high rank cards. 
            """
            high_card = self.__pick_big_card(my_avail_cards)
            if high_card.get_rank_num() >= Card('QS').get_rank_num():
                return high_card
            
            """
            I don't have the same suit. My chance to throw out point cards!
            """
            candidate_list = []
            
            candidate_list += self.htapi.find_cards(my_avail_cards, [Card('TC')])
            candidate_list += self.htapi.get_cards_by_suit(my_avail_cards, 'H')
            
            if len(candidate_list) > 0:
                return candidate_list.pop(0)
            
            """
            Otherwise, pick the highest rank card. 
            """
            return high_card
    
    def __lastplay(self, data):
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        round_cards = [Card(x) for x in data['self']['roundCard']]
        my_hand_cards = self.stat['hand']
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]
        
        lead_card = round_cards[0]
        my_lead_suit_num = self.htapi.calc_card_num_by_suit(my_hand_cards, lead_card.get_suit())
        
        score_card_num = self.htapi.find_cards(round_cards, self.score_cards)

        if my_lead_suit_num > 0:
            """
            Have the same suit. If there's no point on board, shoot the biggest card.
            If there's a point, try to avoid.
            """
            if score_card_num == 0:
                return self.__pick_big_card(my_avail_cards)
            else:
                return self.__pick_smaller_card(my_avail_cards, round_cards)
        else:
            """
            Don't have the same suit. Play the trick.
            """
            return self.__midplay(data)
        
    def pick_card(self, data):
        """
        Event: My turn to shoot a card.
        """
        # roundPlayers is in the correct order of shooting cards.
        round_players = data['roundPlayers']
        
        for idx in range(0, len(round_players)):
            if self.get_name() == round_players[idx]:
                break

        if idx == 0:
            card = self.__leadplay(data)            
        elif idx == 3:
            card = self.__lastplay(data)
        else:
            card = self.__midplay(data)
            
        self.htapi.dbg(self.get_name() + " shoot card: " + format(card) + " from: " + format(data['self']['cards']))
        return card.toString()
    
    def turn_end(self, data):
        """
        Event: turn end
        """
        data_turn_player = data['turnPlayer']
        
        data_turn_card = data['turnCard']
        data_turn_card = Card(data_turn_card)
        
        if data_turn_player != self.get_name():
            self.htapi.dbg(data_turn_player + " shoot card: " + format(data_turn_card))
            
        this_player = self.players[data_turn_player]
        this_player['shoot'].append(data_turn_card)
        
    def pick_history(self, data, is_timeout, pick_his):
        """
        Event: turn end
        """
        self.turn_end(data)
    
    def round_end(self, data):
        """
        Event: round end
        """
        pass
    
    def deal_end(self, data):
        """
        Event: deal end
        """
        data_players = data['players']
        
        print ("...deal end")
        print (data)
        
        for player in data_players:
            local_player = self.players[player['playerName']]
            local_player['score_accl'] = player['gameScore']
            if player['shootingTheMoon'] == True:
                local_player['shoot_moon'] += 1

        for key in self.players.keys():
            p = self.players[key]
            # Reset deal-specific data.
            p['score'] = 0
            p['shoot'] = []
            p['expose'] = False
    
    def game_over(self, data):
        """
        Event: game end
        """
        pass


class HacBotII(PokerBot, Htapi):
    """
    Hac's policy-based bot.
    Ideas:
    - Have different running policy: shoot-moon mode, look-look mode, and anti-trick mode (if failed to shoot moon).
    - In look-look mode, if it's my turn and I can take the trick -> Ask myself, should I switch to shoot-moon mode?
    - So, need to calculate the chance of shoot-moon at every round (turn?). How?
    - Once I cannot shoot the moon, stop the mode right away!!! Holy cow.
    - If I am in shoot-moon mode, let's take all tricks! 
    - If I have many heart big cards and I have QS. Try shoot moon mode from the 1st step. But the risk is quite high.
    """
    LOOK_MODE = "look-look-mode"
    ANTI_TRICK_MODE = "anti-trick-mode"
    SHOOT_MOON_MODE = "shoot-moon-mode"
    
    def __init__(self, name, is_debug=False):
        super(HacBotII, self).__init__(name)

        self.htapi = Htapi(is_debug=is_debug)
                       
        self.players = {}
        self.stat = {}
        
        self.big_rank_cards = [
            Card('AS'), Card('KS'), Card('JS'), Card('TS'),
            Card('AH'), Card('KH'), Card('QH'), Card('JH'), Card('TH'),
            Card('AD'), Card('KD'), Card('QD'), Card('JD'), Card('TD'),
            Card('AC'), Card('KC'), Card('QC'), Card('JC'), Card('TC'), 
            ]
        
        self.score_cards = [Card("QS"), Card("TC"),
                        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
                        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
                        Card("QH"), Card("KH"), Card("AH")]
        
        self.plz_rebuild_players = True
        self.mode = self.LOOK_MODE
        
    def _rebuild_players(self, data):
        """
        Configure player table by input data.
        """
        self.htapi.dbg("Rebuild players: ", format(data))
        
        data_players = data['players']
        
        if len(data_players) != 4:
            self.errmsg("Invalid player number " + str(len(data_players)) + " in server msg")
        
        self.players = {}
        
        for dp in data_players:
            self.players[dp['playerName']] = {
                'playerName': dp['playerName'],
                'score_accl': 0,
                'score': 0,
                'shoot': [],
                'shoot_moon': 0,
                'expose': False,
                }
            
    def new_game(self, data):
        """
        Event: The start of a new game.
        """
        if self.plz_rebuild_players == True:
            self._rebuild_players(data)
            self.plz_rebuild_players = False
    
    def _calc_sm_while_recv13(self):
        """
        Calculate the possibility to shoot the moon while get 13 cards.
        
        If I should enter shoot-moon mode, avoid passing big-rank cards to opponent.
        """
        my_hand_cards = self.stat['hand']
        
        high_rank_score_cards = [Card('AH'), Card('KH'), Card('QH'), Card('JH'), Card('TH')]
        high_rank_score_num = len(self.htapi.find_cards(my_hand_cards, high_rank_score_cards))
               
        high_rank_spade_cards = [Card('AS'), Card('KS'), Card('QS')]
        high_rank_spade_num = len(self.htapi.find_cards(my_hand_cards, high_rank_spade_cards))
        
        # By having these cards, I have higher chance to shoot the moon.
        
        return 100 * ((high_rank_score_num + high_rank_spade_num) / 8.0)
    
    def receive_cards(self, data):
        """
        Event: Receive my 13 cards.
        """
        self.stat['hand'] = self.get_cards(data)
        self.htapi.dbg("Recv cards: " + format(self.stat['hand']))
        
        percentage = self._calc_sm_while_recv13()
        print ("percentage = " + str(percentage))
        if percentage >= 75:
            self.htapi.dbg("shoot moon mode")
            self.mode = self.SHOOT_MOON_MODE
        
    def _select_card2pass(self, my_hand_cards):
        
        card = self.htapi.remove_card(my_hand_cards, Card('KS'))
        if card != None:
            return card
        
        card = self.htapi.remove_card(my_hand_cards, Card('AS'))
        if card != None:
            return card
        
        # Found the suit in shortage
        suit_list = ['S', 'H', 'D', 'C']
        pick_suit = None
        pick_suit_num = 0
        for suit in suit_list:
            this_suit_num = self.htapi.calc_card_num_by_suit(my_hand_cards, suit)
            
            if this_suit_num == 0:
                continue
            
            if pick_suit_num == 0:
                pick_suit_num = this_suit_num
                pick_suit = suit
            elif this_suit_num < pick_suit_num:
                pick_suit_num = this_suit_num
                pick_suit = suit

        # Remove the most large card in the target suit        
        candidate_list = self.htapi.get_cards_by_suit(my_hand_cards, pick_suit)
        self.htapi.arrange_cards(candidate_list)
        card = candidate_list.pop()
        
        return self.htapi.remove_card(my_hand_cards, card)
    
    def pass_cards(self, data):
        """
        Event: Pick 3 cards to pass to others
        """
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        
        output = []
        for i in range(3):
            card = self._select_card2pass(my_hand_cards)
            if card == None:
                self.htapi.errmsg("Cannot pick a card to pass")
            output.append(card.toString())
            
        self.htapi.dbg(self.get_name() + " Pass 3 cards: " + format(output))
        return output

    def receive_opponent_cards(self, data):
        """
        Event: Recv 3 cards from one opponent
        """
        pass

    def expose_my_cards(self, data):
        """
        Event: The server asks me to expose AH...
        """
        my_hand_cards = self.stat['hand']
        
        output = []
        candidates = data['cards']
        if candidates == None or len(candidates) == 0:
            return output

        candidates = [Card(x) for x in candidates]
        
        if self.htapi.find_card(candidates, Card('AH')) == None:
            return output
        
        if my_hand_cards == None or len(my_hand_cards) == 0:
            return output
                
        # Calculate the rate that I will get penalty...
        # The simplest calculation is to check if I have too many big-rank cards
        big_card_num = self.htapi.find_cards(my_hand_cards, self.big_rank_cards)
        if big_card_num > (len(self.big_rank_cards) / 3):
            # Too many big-rank cards...Give up expose.
            return output
            
        output = ['AH']
        
        return output

    def expose_cards_end(self, data):
        """
        Event: Check if somebody expose AH. Damn. 
        """
        data_players = data['players']
        
        for dp in data_players:
            local_player = self.players[dp['playerName']]
            
            if len(dp['exposedCards']) > 0:
                # This guy exposed AH. 
                local_player['expose'] = True
            else:
                local_player['expose'] = False
    
    def __pick_small_card(self, card_list):
        """
        Pick the smallest card in list 
        """
        small_card = card_list[0]
        small_card_rank = small_card.get_rank_num()
        for c in card_list:
            if c.get_rank() < small_card_rank:
                small_card = c
                small_card_rank = c.get_rank_num(c)
            
        return small_card
    
    def __pick_smaller_card(self, card_list, card_list2cmp):
        """
        Pick a smaller card (but not smallest)
        """
        candidate = []
        
        for c2cmp in card_list2cmp:
            for c in card_list:
                if c.get_rank_num() < c2cmp.get_rank_num():
                    candidate.append(c)
        
        if len(candidate) > 0:
            return candidate.pop()
        else:
            # Don't have any smaller card. Give up and pick the biggest one instead.
            return self.__pick_big_card(card_list)
    
    def __pick_big_card(self, card_list):
        big_card = card_list[0]
        big_card_rank = big_card.get_rank_num()
        for c in card_list:
            if c.get_rank_num() > big_card_rank:
                big_card = c
                big_card_rank = c.get_rank_num()
        
        return big_card
    
    def __leadplay(self, data):
        """
        I am the round leader. Play the trick.
        """

        """
        Just pick a small card, so that i can win?
        
        TODO: This is actually stupid... improve.
        """
        
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        
        return self.__pick_small_card(my_hand_cards)
    
    def __midplay(self, data):
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        round_cards = [Card(x) for x in data['self']['roundCard']]
        my_hand_cards = self.stat['hand']
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]
        
        lead_card = round_cards[0]
        my_lead_suit_num = self.htapi.calc_card_num_by_suit(my_hand_cards, lead_card.get_suit())
        
        if my_lead_suit_num > 0:
            """
            Have the same suit. Choose a smaller card to avoid the trick.
            """
            return self.__pick_smaller_card(my_avail_cards, round_cards)
        else:
            """
            I don't have the same suit. Git rid of 'QS'. 
            """
            qs = self.htapi.find_card(my_avail_cards, Card('QS')) 
            if qs != None:
                return qs
            
            """
            I don't have the same suit. Throw dangerous high rank cards. 
            """
            high_card = self.__pick_big_card(my_avail_cards)
            if high_card.get_rank_num() >= Card('QS').get_rank_num():
                return high_card
            
            """
            I don't have the same suit. My chance to throw out point cards!
            """
            candidate_list = []
            
            candidate_list += self.htapi.find_cards(my_avail_cards, [Card('TC')])
            candidate_list += self.htapi.get_cards_by_suit(my_avail_cards, 'H')
            
            if len(candidate_list) > 0:
                return candidate_list.pop(0)
            
            """
            Otherwise, pick the highest rank card. 
            """
            return high_card
    
    def __lastplay(self, data):
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        round_cards = [Card(x) for x in data['self']['roundCard']]
        my_hand_cards = self.stat['hand']
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]
        
        lead_card = round_cards[0]
        my_lead_suit_num = self.htapi.calc_card_num_by_suit(my_hand_cards, lead_card.get_suit())
        
        score_card_num = self.htapi.find_cards(round_cards, self.score_cards)

        if my_lead_suit_num > 0:
            """
            Have the same suit. If there's no point on board, shoot the biggest card.
            If there's a point, try to avoid.
            """
            if score_card_num == 0:
                return self.__pick_big_card(my_avail_cards)
            else:
                return self.__pick_smaller_card(my_avail_cards, round_cards)
        else:
            """
            Don't have the same suit. Play the trick.
            """
            return self.__midplay(data)
        
    def pick_card(self, data):
        """
        Event: My turn to shoot a card.
        """
        # roundPlayers is in the correct order of shooting cards.
        round_players = data['roundPlayers']
        
        for idx in range(0, len(round_players)):
            if self.get_name() == round_players[idx]:
                break

        if idx == 0:
            card = self.__leadplay(data)            
        elif idx == 3:
            card = self.__lastplay(data)
        else:
            card = self.__midplay(data)
            
        self.htapi.dbg(self.get_name() + " shoot card: " + format(card) + " from: " + format(data['self']['cards']))
        return card.toString()
    
    def turn_end(self, data):
        """
        Event: turn end
        """
        data_turn_player = data['turnPlayer']
        
        data_turn_card = data['turnCard']
        data_turn_card = Card(data_turn_card)
        
        if data_turn_player != self.get_name():
            self.htapi.dbg(data_turn_player + " shoot card: " + format(data_turn_card))
            
        this_player = self.players[data_turn_player]
        this_player['shoot'].append(data_turn_card)
        
    def pick_history(self, data, is_timeout, pick_his):
        """
        Event: turn end
        """
        self.turn_end(data)
    
    def round_end(self, data):
        """
        Event: round end
        """
        pass
    
    def deal_end(self, data):
        """
        Event: deal end
        """
        data_players = data['players']
        
        print ("...deal end")
        print (data)
        
        for player in data_players:
            local_player = self.players[player['playerName']]
            local_player['score_accl'] = player['gameScore']
            if player['shootingTheMoon'] == True:
                local_player['shoot_moon'] += 1

        for key in self.players.keys():
            p = self.players[key]
            # Reset deal-specific data.
            p['score'] = 0
            p['shoot'] = []
            p['expose'] = False
    
    def game_over(self, data):
        """
        Event: game end
        """
        pass
