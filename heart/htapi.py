#
# Heart Poker Game
#

from deuces import Card
import sys, traceback
import random

#
# suit num: Spade=1, Heart=2, Diamond=4, Club=8
# rank num: 2=0, Q=10, K=11, A=12, i.e. 0 ~ 12
#
class htapi():
    def __init__(self):
        pass
    
    # Debug tool - Print backtrace
    def bt(self):
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
   
    # Debug tool - Print a list of string(s)
    def msg(self, *argv):
        sys.stdout.write("...")
        print("".join(list(argv)))
        sys.stdout.flush()
    
    def errmsg(self, *argv):
        sys.stderr.write(" *** ERROR: ")
        print("".join(list(argv)))
        sys.stderr.flush()
        self.bt()
    
    #
    # Convert string into deuces format
    #
    def __ht_fixfmt(self, card_str):
        card_str_list = list(card_str)
        
        card_str_list[0] = card_str[0]
        if card_str[1] == 'H':
            card_str_list[1] = 'h'
        elif card_str[1] == 'D':
            card_str_list[1] = 'd'
        elif card_str[1] == 'S':
            card_str_list[1] = 's'
        elif card_str[1] == 'C':
            card_str_list[1] = 'c'
        else:
            self.errmsg(self, "Invalid input", str(card_str))
            
        return "".join(card_str_list)

    # Convert 'AH' -> a Card.new() instance
    def str2card(self, card_str, fixfmt = True):
        if fixfmt == True:
            card_str = self.__ht_fixfmt(card_str)
            
        card = Card.new(card_str)
        return card
    
    # Convert a list ['AH', '2S'] -> a list of Card.new() instance
    def strl2card(self, fixfmt = True, *card_str_list):
        output = []
        for card_str in card_str_list:
            output.append(self.str2card(card_str, fixfmt))
        return output

    # Read suit num: Spade=1, Heart=2, Diamond=4, Club=8
    def get_card_suit(self, card):
        return Card.get_suit_int(card)
    
    # Read rank num: 2=0, Q=10, K=11, A=12, i.e. 0 ~ 12
    def get_card_rank(self, card):
        return Card.get_rank_int(card)
    
    def get_card_pretty(self, card):
        return Card.int_to_pretty_str(card)
    
    def get_card_pretty_list(self, card_list):
        output = ""
        for card in card_list:
            output += self.get_card_pretty(card)
            
        return output
    
    # Output: ['2s', '3s', '4s', '5s', '6s' ... 'Tc', 'Jc', 'Qc', 'Kc', 'Ac' ]
    def get_all_cardstr(self):
        tbl= []
        suit = ['s', 'h', 'd', 'c']
        rank = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        
        for s in suit:
            for r in rank:
                tbl.append("".join(r + s))
        return tbl
    
    # Get all poker cards
    def get_all_card(self):
        tbl = self.get_all_cardstr()
        output = []
        for card_str in tbl:
            output.append(self.str2card(card_str, False))
        return output
    
    # Calc heart game point of a card
    def card2htpoint(self, card):
        output = 0
        
        suit = self.get_card_suit(card)
        rank = self.get_card_rank(card)
        
        if suit == 1 and rank == 10:
            # 'Qs' is 13 point
            output = 13
        
        if suit == 2:
            output = 1
            
        return output

#;


class htplayer(htapi):
    ht = htapi()
    
    def nextgame(self):
        self.point_history.append(self.point)
        
        # Clean data
        self.point = 0
        self.used_card = []
        self.unused_card = []
    
    def __init__(self, name, ident):
        self.name = name
        self.ident = ident
        self.used_card = []
        self.unused_card = []
        self.point = 0
        self.point_total = 0
        self.point_history = []
        
        
    def get_name(self):
        return self.name
    
    def get_ident(self):
        return self.ident

    def inc_point(self, point):
        self.point += point
        self.point_total += point
        
    def get_point(self):
        return self.point
    
    def get_point_total(self):
        return self.point_total
    
    def get_stat_dict(self):
        output = {
                'name': str(self.name), 'ident': str(self.ident), 
                'point': self.point, 'point_total': self.point_total, 
                'point_history': self.point_history,
                'used_card': self.used_card,
                'unused_card': self.unused_card
                }
        return output

    def deal(self, card_list):
        self.unused_card = card_list
    
    def shoot(self, card):
        self.ht.msg(self.name, " -> ", self.ht.get_card_pretty(card), ", Point: ", str(self.get_point()))
        self.used_card.append(card)

class htgame(htplayer, htapi):   
    ht = htapi()
    
    def nextround(self):
        self.roundnum += 1
        self.board_card = []
    
    def nextgame(self):
        for p in self.players:
            p.nextgame()
        
        self.used_card = []
        self.roundnum = 0
        self.gamenum += 1

    def __init__(self, players):
        self.player_num = 0
        self.players = []
        for p in players:            
            self.players.append(p)
            self.player_num += 1
        
        self.used_card = []
        self.board_card = []
        
        self.gamenum = 0
        self.roundnum = 0       
    
    def get_stat_dict(self):        
        player_stat_dict = []
        
        for p in self.players:
            player_stat_dict.append(p.get_stat_dict())
        
        output = {
                'roundnum': self.roundnum,
                'used_card': self.used_card,
                'player_num': self.player_num,
                'players': player_stat_dict
                }
        return output
    
    def find_player(self, ident):
        for p in self.players:
            if p.get_ident() == ident:
                return p
        
        self.ht.errmsg("Cannot find player: ", str(ident))
        return None
    
    def shoot(self, ident, card):
        p = self.find_player(ident)
        if p == None:
            return False
        
        p.shoot(card)

        self.used_card.append(card)

    # Automatically deal cards to all players
    def auto_deal(self):
        unused_card = self.ht.get_all_card()
        random.shuffle(unused_card)

        if len(self.players) != 4:
            self.ht.errmsg("Unexpected player num: ", len(self.players))

        for p in self.players:
            picked = []
            for i in range(13):
                picked.append(unused_card.pop())
            p.deal(picked)

        if len(unused_card) == 0:
            return True
        else:
            self.ht.errmsg("Can't shuffle all cards")
            return False

#;
