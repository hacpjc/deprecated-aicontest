# coding=UTF-8

import os, sys, json, logging

import unicodedata

class Log(object):
    def bt(self):
        try:   
            raise Exception("Manually raise an exception.")
        except Exception:
            import traceback
            traceback.print_stack(file=sys.stderr)
            sys.stderr.flush()
            
    def __init__(self, is_debug=True):
        self.is_debug = is_debug
        self.msg = None
        self.logger = logging.getLogger('hearts_logs')
        hdlr = logging.FileHandler('hearts_logs.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

    def show_message(self, msg):
        print (msg)
        pass
        
    def save_logs(self, msg):
        if self.is_debug:
            self.logger.info(msg)

_IS_DEBUG = False
system_log = Log(_IS_DEBUG)

class Card:

    # Takes in strings of the format: "AS", "TC", "6D"
    def __init__(self, card_string):
        self.suit_value_dict = {"T": 10, "J": 11, "Q": 12, "K": 13, "A": 14, 
                                "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9}
        self.suit_index_dict = {"S": 0, "H": 1, "D": 2, "C": 3}
        self.val_string = "AKQJT98765432"
        value, self.suit = card_string[0], card_string[1]
        self.value = self.suit_value_dict[value]
        self.suit_index = self.suit_index_dict[self.suit]
        
    def __str__(self):
        return self.val_string[14 - self.value] + self.suit

    def toString(self):
        return self.val_string[14 - self.value] + self.suit

    def __repr__(self):
        return self.val_string[14 - self.value] + self.suit

    def __eq__(self, other):
        if self is None:
            return other is None
        elif other is None:
            return False
        return self.value == other.value and self.suit == other.suit

    def __hash__(self):
        return hash(self.value.__hash__() + self.suit.__hash__())
    
    def get_suit(self):
        return str(self.suit)
    
    def get_suit_num(self):
        return self.suit_index
    
    def get_rank_num(self):
        return self.value
    
    def get_rank(self):
        return str(self.value)

class PokerBot(object):

    def __init__(self, player_name):
        self.round_cards_history = []
        self.pick_his = {}
        self.round_cards = {}
        self.score_cards = {}
        self.player_name = player_name
        self.players_current_picked_cards = []
        self.game_score_cards = {Card("QS"), Card("TC"), Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"),
                           Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), Card("QH"), Card("KH"),
                           Card("AH")}

    def get_name(self):
        return self.player_name

    # @abstractmethod
    def receive_cards(self, data):
        err_msg = self.__build_err_msg("receive_cards")
        raise NotImplementedError(err_msg)

    def pass_cards(self, data):
        err_msg = self.__build_err_msg("pass_cards")
        raise NotImplementedError(err_msg)

    def pick_card(self, data):
        """
        event: your_turn
        """
        err_msg = self.__build_err_msg("pick_card")
        raise NotImplementedError(err_msg)

    def expose_my_cards(self, yourcards):
        err_msg = self.__build_err_msg("expose_my_cards")
        raise NotImplementedError(err_msg)

    def expose_cards_end(self, data):
        err_msg = self.__build_err_msg("expose_cards_announcement")
        raise NotImplementedError(err_msg)

    def receive_opponent_cards(self, data):
        err_msg = self.__build_err_msg("receive_opponent_cards")
        raise NotImplementedError(err_msg)

    def round_end(self, data):
        err_msg = self.__build_err_msg("round_end")
        raise NotImplementedError(err_msg)

    def deal_end(self, data):
        err_msg = self.__build_err_msg("deal_end")
        raise NotImplementedError(err_msg)

    def game_over(self, data):
        err_msg = self.__build_err_msg("game_over")
        raise NotImplementedError(err_msg)

    def pick_history(self, data, is_timeout, pick_his):
        err_msg = self.__build_err_msg("pick_history")
        raise NotImplementedError(err_msg)

    def reset_card_his(self):
        """
        Reset history. Usually called at end of a deal.
        """
        self.round_cards_history = []
        self.pick_his = {}

    def get_card_history(self):
        return self.round_cards_history

    def turn_end(self, data):
        turnCard = data['turnCard']
        turnPlayer = data['turnPlayer']
        players = data['players']
        is_timeout = data['serverRandom']
        
        for player in players:
            player_name = player['playerName']
            if player_name == self.player_name:
                current_cards = player['cards']
                for card in current_cards:
                    self.players_current_picked_cards.append(Card(card))
                    
        self.round_cards[turnPlayer] = Card(turnCard)
        opp_pick = {}
        opp_pick[turnPlayer] = Card(turnCard)
        
        if (self.pick_his.get(turnPlayer)) != None:
            pick_card_list = self.pick_his.get(turnPlayer)
            pick_card_list.append(Card(turnCard))
            self.pick_his[turnPlayer] = pick_card_list
        else:
            pick_card_list = []
            pick_card_list.append(Card(turnCard))
            self.pick_his[turnPlayer] = pick_card_list
            
        self.round_cards_history.append(Card(turnCard))
        self.pick_history(data, is_timeout, opp_pick)

    def get_cards(self, data):
        try:
            receive_cards = []
            players = data['players']
            
            for player in players:
                if player['playerName'] == self.player_name:
                    cards = player['cards']
                    for card in cards:
                        receive_cards.append(Card(card))
                    break
                
            return receive_cards
        except Exception, e:
            system_log.show_message(e.message)
            return None

    def get_round_scores(self, is_expose_card=False, data=None):
        
        if data != None:
            players = data['roundPlayers']
            picked_user = players[0]
            round_card = self.round_cards.get(picked_user)
            score_cards = []
            
            for i in range(len(players)):
                card = self.round_cards.get(players[i])
                if card in self.game_score_cards:
                    score_cards.append(card)
                if round_card.suit_index == card.suit_index:
                    if round_card.value < card.value:
                        picked_user = players[i]
                        round_card = card
                        
            if (self.score_cards.get(picked_user) != None):
                current_score_cards = self.score_cards.get(picked_user)
                score_cards += current_score_cards
                
            self.score_cards[picked_user] = score_cards
            self.round_cards = {}

        receive_cards = {}
        for key in self.pick_his.keys():
            picked_score_cards = self.score_cards.get(key)
            round_score = 0
            round_heart_score = 0
            is_double = False
            
            if picked_score_cards != None:
                for card in picked_score_cards:
                    if card in self.game_score_cards:
                        if card == Card("QS"):
                            round_score += -13
                        elif card == Card("TC"):
                            is_double = True
                        else:
                            round_heart_score += -1
                            
                if is_expose_card:
                    round_heart_score *= 2
                    
                round_score += round_heart_score
                
                if is_double:
                    round_score *= 2
                    
            receive_cards[key] = round_score
            
        return receive_cards

    def get_deal_scores(self, data):
        try:
            self.score_cards = {}
            final_scores = {}
            initial_cards = {}
            receive_cards = {}
            picked_cards = {}
            players = data['players']
            
            for player in players:
                player_name = player['playerName']
                palyer_score = player['dealScore']
                player_initial = player['initialCards']
                player_receive = player['receivedCards']
                player_picked = player['pickedCards']

                final_scores[player_name] = palyer_score
                initial_cards[player_name] = player_initial
                receive_cards[player_name] = player_receive
                picked_cards[player_name] = player_picked
                
            return final_scores, initial_cards, receive_cards, picked_cards
        except Exception, e:
            system_log.show_message(e.message)
            return None

    def get_game_scores(self, data):
        try:
            receive_cards = {}
            players = data['players']
            
            for player in players:
                player_name = player['playerName']
                palyer_score = player['gameScore']
                receive_cards[player_name] = palyer_score
                
            return receive_cards
        except Exception, e:
            system_log.show_message(e.message)
            return None

class SampleBot(PokerBot):

    def __init__(self, name):
        super(SampleBot, self).__init__(name)
        self.my_hand_cards = []
        self.expose_card = False
        self.my_pass_card = []

    def receive_cards(self, data):
        self.my_hand_cards = self.get_cards(data)

    def pass_cards(self, data):
        cards = data['self']['cards']
        self.my_hand_cards = []
        for card_str in cards:
            card = Card(card_str)
            self.my_hand_cards.append(card)
            
        pass_cards = [self.my_hand_cards[0], self.my_hand_cards[1], self.my_hand_cards[2]]
#         count = 0
#         for i in range(len(self.my_hand_cards)):
#             card = self.my_hand_cards[len(self.my_hand_cards) - (i + 1)]
#             if card == Card("QS"):
#                 pass_cards.append(card)
#                 count += 1
#             elif card == Card("TC"):
#                 pass_cards.append(card)
#                 count += 1
#         for i in range(len(self.my_hand_cards)):
#             card = self.my_hand_cards[len(self.my_hand_cards) - (i + 1)]
#             if card.suit_index == 2:
#                 pass_cards.append(card)
#                 count += 1
#                 if count == 3:
#                     break
#         if count < 3:
#             for i in range(len(self.my_hand_cards)):
#                 card = self.my_hand_cards[len(self.my_hand_cards) - (i + 1)]
#                 if card not in self.game_score_cards:
#                     pass_cards.append(card)
#                     count += 1
#                     if count == 3:
#                         break
        return_values = []
        for card in pass_cards:
            return_values.append(card.toString())
        message = "Pass Cards:{}".format(return_values)
        system_log.show_message(message)
        system_log.save_logs(message)
        self.my_pass_card = return_values
        return return_values

    def pick_card(self, data):
        """
        event: your_turn
        """
        cadidate_cards = data['self']['candidateCards']
        cards = data['self']['cards']
        self.my_hand_cards = []
        for card_str in cards:
            card = Card(card_str)
            self.my_hand_cards.append(card)
        message = "My Cards:{}".format(self.my_hand_cards)
        system_log.show_message(message)
        card_index = 0
        message = "Pick Card Event Content:{}".format(data)
        system_log.show_message(message)
        message = "Candidate Cards:{}".format(cadidate_cards)
        system_log.show_message(message)
        system_log.save_logs(message)
        message = "Pick Card:{}".format(cadidate_cards[card_index])
        system_log.show_message(message)
        system_log.save_logs(message)
        return cadidate_cards[card_index]

    def expose_my_cards(self, yourcards):
        expose_card = []
        for card in self.my_hand_cards:
            if card == Card("AH"):
                expose_card.append(card.toString())
        message = "Expose Cards:{}".format(expose_card)
        system_log.show_message(message)
        system_log.save_logs(message)
        return expose_card

    def expose_cards_end(self, data):
        players = data['players']
        expose_player = None
        expose_card = None
        for player in players:
            try:
                if player['exposedCards'] != [] and len(player['exposedCards']) > 0 and player['exposedCards'] != None:
                    expose_player = player['playerName']
                    expose_card = player['exposedCards']
            except Exception, e:
                system_log.show_message(e.message)
                system_log.save_logs(e.message)
        if expose_player != None and expose_card != None:
            message = "Player:{}, Expose card:{}".format(expose_player, expose_card)
            system_log.show_message(message)
            system_log.save_logs(message)
            self.expose_card = True
        else:
            message = "No player expose card!"
            system_log.show_message(message)
            system_log.save_logs(message)
            self.expose_card = False

    def receive_opponent_cards(self, data):
        self.my_hand_cards = self.get_cards(data)
        players = data['players']
        for player in players:
            player_name = player['playerName']
            if player_name == self.player_name:
                picked_cards = player['pickedCards']
                receive_cards = player['receivedCards']
                message = "User Name:{}, Picked Cards:{}, Receive Cards:{}".format(player_name, picked_cards, receive_cards)
                system_log.show_message(message)
                system_log.save_logs(message)

    def round_end(self, data):
        try:
            round_scores = self.get_round_scores(self.expose_card, data)
            for key in round_scores.keys():
                message = "Player name:{}, Round score:{}".format(key, round_scores.get(key))
                system_log.show_message(message)
                system_log.save_logs(message)
        except Exception, e:
            system_log.show_message(e.message)

    def deal_end(self, data):
        self.my_hand_cards = []
        self.expose_card = False
        deal_scores, initial_cards, receive_cards, picked_cards = self.get_deal_scores(data)
        message = "Player name:{}, Pass Cards:{}".format(self.player_name, self.my_pass_card)
        system_log.show_message(message)
        system_log.save_logs(message)
        for key in deal_scores.keys():
            message = "Player name:{}, Deal score:{}".format(key, deal_scores.get(key))
            system_log.show_message(message)
            system_log.save_logs(message)
        for key in initial_cards.keys():
            message = "Player name:{}, Initial cards:{}, Receive cards:{}, Picked cards:{}".format(key, initial_cards.get(key), receive_cards.get(key), picked_cards.get(key))
            system_log.show_message(message)
            system_log.save_logs(message)

    def game_over(self, data):
        game_scores = self.get_game_scores(data)
        for key in game_scores.keys():
            message = "Player name:{}, Game score:{}".format(key, game_scores.get(key))
            system_log.show_message(message)
            system_log.save_logs(message)

    def pick_history(self, data, is_timeout, pick_his):
        for key in pick_his.keys():
            message = "Player name:{}, Pick card:{}, Is timeout:{}".format(key, pick_his.get(key), is_timeout)
            system_log.show_message(message)
            system_log.save_logs(message)
