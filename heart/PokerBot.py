# coding=UTF-8

import os, sys, json, logging, random

class Log(object):
    def bt(self):
        try:   
            raise Exception("Manually raise an exception.")
        except Exception:
            import traceback
            traceback.print_stack(file=sys.stderr)
            sys.stderr.flush()
            
    def __init__(self, is_debug=False):
        self.is_debug = is_debug
        self.msg = None
        self.logger = logging.getLogger('hearts_logs')
        hdlr = logging.FileHandler('hearts_logs.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

    def show_message(self, msg):
        if self.is_debug == True:
            print (msg)
        pass
        
    def save_logs(self, msg):
        if self.is_debug == True:
            self.logger.info(msg)
        pass

#
# If you use Log class, control the message here.
#
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
    
    def new_game(self, data):
        err_msg = self.__build_err_msg("new_game")
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

class Htapi():
    
    game_score_cards = [Card("QS"), Card("TC"),
        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
        Card("QH"), Card("KH"), Card("AH")]
    
    game_penalty_cards = [Card("QS"),
                        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
                        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
                        Card("QH"), Card("KH"), Card("AH")]
        
    def __init__(self, is_debug=False):
        from uptime import uptime
        random.seed(int(uptime()))
        
        if is_debug == True:
            self.is_debug = True
        else:
            self.is_debug = False
            
        self.game_heart_cards = self.get_cards_by_suit(self.get52cards(), 'H')
        
        all52cards = self.get52cards()
        self.game_no_penalty_cards = self.filter_out_cards(all52cards, self.game_penalty_cards)
        
        all52cards = self.get52cards()
        self.game_no_score_cards = self.filter_out_cards(all52cards, self.game_score_cards)

    def logdict(self, dict):
        """
        Output log to stdout by a python dict input
        TODO: Write to a file, maybe?
        """
        print(format(dict))
        sys.stdout.flush()

    # Debug tool - Print a list of string(s)
    def msg(self, *argv):
        sys.stdout.write("".join(list(argv)) + "\n")
        sys.stdout.flush()
        
    def dbg(self, *argv):
        if self.is_debug == True:
            sys.stdout.write("...")
            sys.stdout.write("".join(list(argv)) + "\n")
            sys.stdout.flush()

    def errmsg(self, *argv):
        sys.stderr.write(" *** ERROR: ")
        sys.stderr.write("".join(list(argv)) + "\n")
        sys.stderr.flush()
        self.bt()
        sys.exit(255)
        
    def get52cards(self):
        """
        Output: ['2S', '3S', ..., 'AS', '2H', ... 'AC' ]
        """
        suits = ['S', 'H', 'D', 'C']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        
        allcard = []
        for suit in range(0, 4):
            for rank in range(0, 13):
                card = Card(str(ranks[rank]) + str(suits[suit]))
                allcard.append(card)
        
        return allcard
    
    def calc_card_num_by_suit(self, cards_in, suit = 'C'):
        return len(self.get_cards_by_suit(cards_in, suit))
    
    def get_cards_by_suit(self, cards_in, suit = 'C'):
        cards = []
        for c in cards_in:
            if c.get_suit() == suit:
                cards.append(c)
                
        return cards
    
    def get_cards_by_suits(self, cards_in, suits):
        cards = []
        for suit in suits:
            cards += self.get_cards_by_suit(cards_in, suit)
            
        return cards
    
    def find_card(self, cards_in, card2find):
        """
        Find a single card.
        
        Output: None | Card('XX')
        """
        for c in cards_in:
            if c == card2find:
                return c
            
        return None
    
    def find_cards(self, cards_in, cards2find):
        """
        Find mutiple cards.
        
        Output: [ Card('XX), Card('OO') ]
        Output: []
        """
        found = []
        for c2find in cards2find:
            for c in cards_in:
                if c2find == c:
                    found.append(c)
        
        return found
    
    def find_score_cards(self, cards_in):
        """
        NOTE: TC is also a score card
        """
        return self.find_cards(cards_in, self.game_score_cards)
    
    def find_no_score_cards(self, cards_in):
        """
        NOTE: TC is also a score card
        """
        return self.find_cards(cards_in, self.game_no_score_cards)
    
    def find_penalty_cards(self, cards_in):
        """
        NOTE: TC is not a penalty card.
        """
        return self.find_cards(cards_in, self.game_penalty_cards)

    def find_no_penalty_cards(self, cards_in):
        """
        NOTE: TC is also no penalty card
        """
        return self.find_cards(cards_in, self.game_no_penalty_cards)
    
    def filter_out_cards(self, cards_in, filter_cards):
        """
        Return the cards not in the tgt
        """
        output = []
        for c in cards_in:
            if filter_cards.count(c) == 0:
                output.append(c)
                
        return output

    def remove_card(self, cards_in, card2rm):
        """
        Remove a single card!
        """
        c = None
        if cards_in.count(card2rm) > 0:
            c_idx = cards_in.index(card2rm)
            c = cards_in.pop(c_idx)
            
        return c
        
    def remove_cards(self, cards_in, cards2rm):
        """
        Remove cards if there's any.
        
        Output: Removed cards
        """
        remove = []
        
        for c in cards2rm:
            rm = self.remove_card(cards_in, c)
            remove.append(rm)
        
        return remove
    
    def arrange_cards(self, card_list):
        # Sort by card suit and rank
        output = sorted(card_list, key=lambda v: (v.get_suit_num() * 20 + v.get_rank_num()))
        return output
    
    def arrange_cards_by_rank(self, card_list):
        output = sorted(card_list, key=lambda v: v.get_rank_num())
        return output
    
    def shuffle_cards(self, card_list):
        random.shuffle(card_list)
        return card_list
    
    def clone_cards(self, cards):
        output = cards[:]
        return output
    
    def calc_score(self, cards, is_expose_ah=False):
        """
        Calculate the score/penalty of the cards
        """
        score = 0
        picked_cards = cards
 
        my_score_cards = self.find_cards(picked_cards, self.game_score_cards)
        my_heart_cards = self.find_cards(picked_cards, self.game_heart_cards)
        my_penalty_cards = self.find_cards(picked_cards, self.game_penalty_cards)
        
        if is_expose_ah == True:
            score = len(my_heart_cards) * 2 * (-1)
        else:
            score = len(my_heart_cards) * (-1)
        
        if self.find_card(my_score_cards, Card('QS')) != None:
            score += -13
            
        if self.find_card(my_score_cards, Card('TC')) != None:
            score *= 2
            
        if len(self.find_cards(my_score_cards, my_penalty_cards)) == len(self.game_penalty_cards):
            # Shoot the moon. Score becomes postive! Score x 4! 
            score *= -1
            score *= 4
        
        return score
    
    def pick_small_card(self, card_list):
        """
        Pick the smallest card in list 
        """
        small_card = card_list[0]
        small_card_rank_num = small_card.get_rank_num()
        for c in card_list:
            if c.get_rank_num() < small_card_rank_num:
                small_card = c
                small_card_rank_num = c.get_rank_num(c)
            
        return small_card
    
    def pick_bigger_card(self, card_list, card_list2cmp):
        """
        Pick a bigger card (but not biggest)
        """
        candidate = []
        
        for c2cmp in card_list2cmp:
            for c in card_list:
                if c.get_rank_num > c2cmp.get_rank_num():
                    candidate.append(c)
        
        if len(candidate) > 0:
            candidate = self.arrange_cards(candidate)
            return candidate.pop(0)
        else:
            return None
    
    def pick_smaller_card(self, card_list, card_list2cmp, auto_choose_big=False):
        """
        Pick a smaller card (but not smallest)
        """
        candidate = []
        
        for c2cmp in card_list2cmp:
            for c in card_list:
                if c.get_rank_num() < c2cmp.get_rank_num():
                    candidate.append(c)
        
        if len(candidate) > 0:
            candidate = self.arrange_cards(candidate)
            return candidate.pop()
        else:
            if auto_choose_big == True:
                # Select the biggest one if there's no smaller card.
                return self.pick_big_card(card_list)
            else:
                return None
        
        return None
    
    def pick_big_card(self, card_list):
        big_card = card_list[0]
        big_card_rank = big_card.get_rank_num()
        for c in card_list:
            if c.get_rank_num() > big_card_rank:
                big_card = c
                big_card_rank = c.get_rank_num()
        
        return big_card
    