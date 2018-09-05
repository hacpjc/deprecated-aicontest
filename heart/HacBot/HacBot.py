
from PokerBot import PokerBot, system_log, Card, Htapi

class HacBot(PokerBot, Htapi):
    """
    Hac's policy-based bot.
    
    This is the most stupid version which cannot shoot moon, but this is smart enough to avoid taking tricks.
    The grades of 50 games:
    ...Player: hac, score: -4, score_accl: -3835, shoot_moon_accl: 1
    ...Player: bota, score: 0, score_accl: -12501, shoot_moon_accl: 2
    ...Player: botb, score: -33, score_accl: -11415, shoot_moon_accl: 2
    ...Player: botc, score: -2, score_accl: -11538, shoot_moon_accl: 3
    """
    def __init__(self, name, is_debug=False):
        super(HacBot, self).__init__(name)

        self.htapi = Htapi(is_debug=is_debug)
                       
        self.players = {}
        self.stat = {}
        self.stat['roundCard'] = [] 
        self.stat['usedCard'] = []
        self.stat['nextPlayers'] = []
        
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
                'shoot_moon': 0,
                'expose': False,
                                
                'shoot': [],
                'suit_leak': [],
                'pick': [],
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
        
        card = self.htapi.remove_card(my_hand_cards, Card('AC'))
        if card != None:
            return card
        
        card = self.htapi.remove_card(my_hand_cards, Card('KC'))
        if card != None:
            return card        

        card = self.htapi.remove_card(my_hand_cards, Card('QC'))
        if card != None:
            return card 
        
        card = self.htapi.remove_card(my_hand_cards, Card('JC'))
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

    def _monte_carlo_predict(self, card2shoot, opponent_cards, round_cards=[]):
        """
        Will I take the trick if I select the card2shoot!?
        """

        # TODO: Improve prediction by the players!
#         next_players = self.stat['nextPlayers'] 
#         next_player_num = len(next_players)

        # Calculate the number of cards will... make me eat the trick.
        opponent_same_suit_cards = self.htapi.get_cards_by_suit(opponent_cards, card2shoot.get_suit())
        if len(opponent_same_suit_cards) == 0:
            return 100.0
        
        danger_level = 0
        for ocard in opponent_same_suit_cards:
            if ocard.get_rank_num() < card2shoot.get_rank_num():
                # Oops...
                danger_level += 1
        
        max = float(len(opponent_same_suit_cards))
        percentage = danger_level / max
        return percentage
            
    def __leadplay(self, data):
        """
        I am the round leader. I want to avoid tacking the trick, so choose the best!
        """
        
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]    
        
        opponent_cards = self._get_unused_cards_by_suits(my_hand_cards)
        
        selected = []
        peak_percentage = 0
        for c in my_avail_cards:
            # If I pick this card, will I take the trick?            
            percentage = self._monte_carlo_predict(c, opponent_cards, round_cards=[])
            
            if len(selected) == 0:
                peak_percentage = percentage
                selected = [c]
            elif percentage < peak_percentage:
                peak_percentage = percentage
                selected = [c]
            elif percentage == peak_percentage:
                selected.append(c)
                
        # Prefer a lower number suit
        all_suit = []
        for c in selected:
            card_suit = c.get_suit()
            if all_suit.count(card_suit) == 0:
                all_suit.append(card_suit)

        self.htapi.dbg("Selected candidates: " + format(selected) + ", the suits: " + format(all_suit) + ", all cards: " + format(my_hand_cards))
        
        prefer_suit = None
        min_suit_num = 0
        for suit in all_suit:
            same_suit_num = self.htapi.get_cards_by_suit(my_hand_cards, suit)
            
            if prefer_suit == None:
                prefer_suit = suit
                min_suit_num = same_suit_num
            elif same_suit_num < min_suit_num:
                prefer_suit = suit
                min_suit_num = same_suit_num
        
        prefer_cards = self.htapi.arrange_cards(self.htapi.get_cards_by_suit(selected, prefer_suit))
        self.htapi.dbg("Selected candidates: " + format(prefer_cards))
        card2shoot = prefer_cards.pop()
        self.htapi.dbg("Select card" + format(card2shoot))
        
        return card2shoot
    
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
            filtered_round_cards = self.htapi.get_cards_by_suit(round_cards, lead_card.get_suit())
            return self.htapi.pick_smaller_card(my_avail_cards, filtered_round_cards, auto_choose_big=True)
        else:
            """
            I don't have the same suit. Git rid of 'QS'. 
            """
            cardqs = self.htapi.find_card(my_avail_cards, Card('QS')) 
            if cardqs != None:
                return cardqs
            
            """
            I don't have the same suit. Throw dangerous high rank cards. 
            """
            high_card = self.htapi.pick_big_card(my_avail_cards)
            if high_card.get_rank_num() >= Card('JS').get_rank_num():
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
                return self.htapi.pick_big_card(my_avail_cards)
            else:
                return self.htapi.pick_smaller_card(my_avail_cards, round_cards, auto_choose_big=True)
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
        
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())

        # Get players in next turn.
        self.stat['nextPlayers'] = data['roundPlayers'][my_pos:]
            
        if my_pos == 0:
            card = self.__leadplay(data)            
        elif my_pos == 3:
            card = self.__lastplay(data)
        else:
            card = self.__midplay(data)
            
        self.htapi.dbg(self.get_name() + " shoot card: " + format(card) + ", from: " + format(data['self']['cards']) + ", next players: " + format(self.stat['nextPlayers']))
        return card.toString()

    def _detect_card_shortage(self, local_player, turn_card):
        #
        # If the player is not lead player and he shoots a card not the same as lead card,
        # mark the player as card shortage.
        #
        # If I know the shortage status of players, can have advantage to predict.
        #
        
        round_cards = self.stat['roundCard']
        
        if len(round_cards) <= 1:
            # The turn player is leader. Ignore.
            return False
        
        lead_card = round_cards[0]
        
        if lead_card.get_suit_num() != turn_card.get_suit_num():
            if local_player['suit_leak'].count(lead_card.get_suit()):
                local_player['suit_leak'].append(lead_card.get_suit())
                self.htapi.dbg("Player: " + local_player['playerName'] + " card leakage: " + lead_card.get_suit())
    
    def _get_unused_cards_by_suits(self, my_cards, suits=[]):
        """
        Get unused cards of other opponents so that I can know how many cards are left..
        """
        
        all52cards = self.htapi.get52cards()
        output = all52cards

        self.htapi.remove_cards(output, self.stat['usedCard'])
        self.htapi.remove_cards(output, my_cards)

        if len(suits) == 0:
            # Do not need to pick a specific suit
            pass
        else:
            # Pick unused cards of target suits
            output = self.htapi.get_cards_by_suits(output, suits)

        return output
        
    def turn_end(self, data):
        """
        Event: turn end
        """
        data_turn_player = data['turnPlayer']
        
        data_turn_card = data['turnCard']
        data_turn_card = Card(data_turn_card)
        
        if data_turn_player != self.get_name():
            self.htapi.dbg(data_turn_player + " shoot card: " + format(data_turn_card))
            
        local_player = self.players[data_turn_player]
        local_player['shoot'].append(data_turn_card)
        
        self.stat['roundCard'].append(data_turn_card)
        self.stat['usedCard'].append(data_turn_card)
        
        self._detect_card_shortage(local_player, data_turn_card)
                
    def pick_history(self, data, is_timeout, pick_his):
        """
        Event: turn end
        """
        self.turn_end(data)
    
    def round_end(self, data):
        """
        Event: round end
        """
        round_player_name = data['roundPlayer']
        round_cards = self.stat['roundCard']
        
        local_player = self.players[round_player_name]
        local_player['pick'] += round_cards
        
        self.htapi.dbg("Player: " + round_player_name + " picked 4 cards: " + format(round_cards), " overall pick: " + format(local_player['pick']))
        
        #
        # Reset round data
        #
        self.stat['roundCard'] = []
    
    def deal_end(self, data):
        """
        Event: deal end
        """
        data_players = data['players']
        
        self.htapi.dbg(format(data))
        
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
            p['pick'] = []
        
        self.stat['usedCard'] = []
    
    def game_over(self, data):
        """
        Event: game end
        """
        self.htapi.dbg(format(data))
