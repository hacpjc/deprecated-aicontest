
from PokerBot import PokerBot, system_log, Card, Htapi

class HacBot(PokerBot, Htapi):
    """
    Hac's policy-based bot.
    """
    
    def __init__(self, name):
        super(HacBot, self).__init__(name)

        self.htapi = Htapi()
                       
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
                'expose': False,
                }
    
    def new_game(self, data):
        self._rebuild_players(data)
    
    def receive_cards(self, data):
        """
        Receive my 13 cards.
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
        Pick 3 cards to pass to others
        """
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        
        output = []
        for i in range(3):
            card = self._select_card2pass(my_hand_cards)
            if card == None:
                self.htapi.errmsg("Cannot pick a card to pass")
            output.append(card.toString())
        
        return output

    def receive_opponent_cards(self, data):
        """
        Recv 3 cards from one opponent
        """
        pass

    def expose_my_cards(self, data):
        """
        The server asks me to expose AH...
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
        Check if somebody expose AH. Damn. 
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
        My turn to shoot a card.
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
            
        return card.toString()
    
    def pick_history(self, data, is_timeout, pick_his):
        """
        turn end
        """
        pass
    
    def round_end(self, data):
        pass
    
    def deal_end(self, data):
        pass
    
    def game_over(self, data):
        pass


# class HacBot(PokerBot):
# 
# 
#     def expose_my_cards(self, yourcards):
#         """
#         TODO: Expose AH? WHY?
#         """
#         expose_card = []
#         for card in self.my_hand_cards:
#             if card == Card("AH"):
#                 expose_card.append(card.toString())
#                 
#         message = "Expose Cards:{}".format(expose_card)
#         
#         system_log.show_message(message)
#         system_log.save_logs(message)
#         
#         return expose_card
# 
#     def expose_cards_end(self, data):
#         players = data['players']
#         expose_player = None
#         expose_card = None
#         
#         for player in players:
#             try:
#                 if player['exposedCards'] != [] and len(player['exposedCards']) > 0 and player['exposedCards'] != None:
#                     expose_player = player['playerName']
#                     expose_card = player['exposedCards']
#             except Exception, e:
#                 system_log.show_message(e.message)
#                 system_log.save_logs(e.message)
#                 
#         if expose_player != None and expose_card != None:
#             message = "Player:{}, Expose card:{}".format(expose_player, expose_card)
#             system_log.show_message(message)
#             system_log.save_logs(message)
#             self.expose_card = True
#         else:
#             message = "No player expose card!"
#             system_log.show_message(message)
#             system_log.save_logs(message)
#             self.expose_card = False
# 
#     def receive_opponent_cards(self, data):
#         self.my_hand_cards = self.get_cards(data)
#         players = data['players']
#         for player in players:
#             player_name = player['playerName']
#             if player_name == self.player_name:
#                 picked_cards = player['pickedCards']
#                 receive_cards = player['receivedCards']
#                 message = "User Name:{}, Picked Cards:{}, Receive Cards:{}".format(player_name, picked_cards, receive_cards)
#                 system_log.show_message(message)
#                 system_log.save_logs(message)
# 
#     def round_end(self, data):
#         try:
#             round_scores = self.get_round_scores(self.expose_card, data)
#             for key in round_scores.keys():
#                 message = "Player name:{}, Round score:{}".format(key, round_scores.get(key))
#                 system_log.show_message(message)
#                 system_log.save_logs(message)
#         except Exception, e:
#             system_log.show_message(e.message)
# 
#     def deal_end(self, data):
#         self.my_hand_cards = []
#         self.expose_card = False
#         deal_scores, initial_cards, receive_cards, picked_cards = self.get_deal_scores(data)
#         message = "Player name:{}, Pass Cards:{}".format(self.player_name, self.my_pass_card)
#         system_log.show_message(message)
#         system_log.save_logs(message)
#         
#         for key in deal_scores.keys():
#             message = "Player name:{}, Deal score:{}".format(key, deal_scores.get(key))
#             system_log.show_message(message)
#             system_log.save_logs(message)
#             
#         for key in initial_cards.keys():
#             message = "Player name:{}, Initial cards:{}, Receive cards:{}, Picked cards:{}".format(key, initial_cards.get(key), receive_cards.get(key), picked_cards.get(key))
#             system_log.show_message(message)
#             system_log.save_logs(message)
# 
#     def game_over(self, data):
#         game_scores = self.get_game_scores(data)
#         for key in game_scores.keys():
#             message = "Player name:{}, Game score:{}".format(key, game_scores.get(key))
#             system_log.show_message(message)
#             system_log.save_logs(message)
# 
#     def pick_history(self, data, is_timeout, pick_his):
#         for key in pick_his.keys():
#             message = "Player name:{}, Pick card:{}, Is timeout:{}".format(key, pick_his.get(key), is_timeout)
#             system_log.show_message(message)
#             system_log.save_logs(message)
