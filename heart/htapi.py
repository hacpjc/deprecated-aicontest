#!/usr/bin/env python
#
# Heart Poker Game
#

from deuces import Card
import sys, traceback
import random

# Heart API 
#
# suit num: Spade=1, Heart=2, Diamond=4, Club=8
# rank num: 2=0, Q=10, K=11, A=12, i.e. 0 ~ 12
#
class htapi():
    def __init__(self):
        pass

    # Debug tool - Print backtrace
    def bt(self):
        try:   
            raise Exception("Manually raise an exception.")
        except Exception:
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
    def strl2card(self, card_str_list, fixfmt = True):
        output = []
        for card_str in card_str_list:
            output.append(self.str2card(card_str, fixfmt))
        return output
    
    # Convert suit string into suit num: Input = Spade, Heart, Diamond, Club
    def str2suit(self, suit_str):
        c = suit_str[0]
        
        if c == 's' or c == 'S':
            return 1
        elif c == 'h' or c == 'H':
            return 2
        elif c == 'd' or c == 'D':
            return 4
        elif c == 'c' or c == 'C':
            return 8
        else:
            self.errmsg("Invalid input string: " + suit_str)
    
    # Convert rank string into rank num: Input = '2', '3', ...'K', 'A'
    def str2rank(self, card_str):
        c = card_str[0] + 'c'
        
        card = self.str2card(c, fixfmt=False)
        return self.get_card_rank(card)

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

    def card_arrange(self, card_list):
        # Sort by card suit and rank
        output = sorted(card_list, key=lambda v: (self.get_card_suit(v) * 20 + self.get_card_rank(v)))
        return output

# Heart Player 
class htplayer(htapi):
    ht = htapi()

    def nextgame(self):
        self.point_history.append(self.point)

        # Clean data
        self.point = 0
        self.used_card = []
        self.unused_card = []


    def __init__(self, name, ident, botai):
        self.name = name
        self.ident = ident
        self.used_card = []
        self.unused_card = []
        self.point = 0
        self.point_total = 0
        self.point_history = []
        self.botai = botai()

    def get_name(self):
        return self.name


    def get_ident(self):
        return self.ident


    def inc_point(self, point):
        self.point += point
        self.point_total += point
        
        return self.point
       
        
    def dec_point(self, point):
        if self.point >= point:
            self.point -= point
        else:
            self.point = 0
        
        return self.point


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


    def get_unused_card(self, card_suit_list = []):
        if len(card_suit_list) > 0:
            # Return unused card the same as input suit.
            output = []
            
            for card_suit in card_suit_list:
                for c in self.unused_card:
                    if self.ht.get_card_suit(c) == card_suit:
                        output.append(c)
            
            return output
        
        return self.unused_card


    def deal(self, card_list):
        self.unused_card = card_list
            
    def time2shoot(self, data):
        data['player_unused_card'] = self.unused_card

        data['player_point'] = self.point
        data['player_point_history'] = self.point_history
        
        pick = self.botai.time2shoot(data)
        
        if self.unused_card.count(pick) == 0:
            self.ht.errmsg("Invalid output card of user" + self.name)
            
        self.unused_card.remove(pick)
        self.used_card.append(pick)
        
        return pick

# Heart Game
# 13 round of each game. 4 ppl.
class htgame(htplayer, htapi):
    ht = htapi()

    def nextround(self):
        self.roundnum += 1
        self.board_card = []

    def nextgame(self):
        for p in self.players:
            p.nextgame()

        self.used_card = []
        self.roundnum = 1
        self.is_hb = False
        
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
        self.roundnum = 1
        self.is_hb = False # Heart break in this round

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

    def __find_player(self, ident):
        for p in self.players:
            if p.get_ident() == ident:
                return p

        self.ht.errmsg("Cannot find player: ", str(ident))
        return None
    
    def __rotate_player_position(self, count):
        # Rotate the players, so the player to shoot first will also be at head.     
        for i in range(count):
            p = self.players.pop(0)
            self.players.append(p)
        

    def shoot(self, ident, card):
        p = self.__find_player(ident)
        if p == None:
            return False

        p.shoot(card)

        self.used_card.append(card)
        self.board_card.append(card)

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
            picked = self.ht.card_arrange(picked)
            p.deal(picked)
            sys.stdout.write(p.get_name() + ": ")
            print (self.ht.get_card_pretty_list(p.get_unused_card()))

        if len(unused_card) == 0:
            return True
        else:
            self.ht.errmsg("Can't shuffle all cards")
            return False

    def __calc_card_score(self, card_list):
        score = 0
        
        for c in card_list:
            suit = self.ht.get_card_suit(c)
            rank = self.ht.get_card_rank(c)
            if suit == self.ht.str2suit('Heart'):
                score += 1
            
            if suit == self.ht.str2suit('Spade'):
                if rank == self.ht.str2rank('Q'):
                    score += 13
        
        self.ht.msg("Score of this round: " + str(score))
        return score

    def __round_over(self):
        # Calc point!
        board_card = self.board_card
        players = self.players
        
        lead_card = board_card[0]
        lead_player = self.players[0]
        
        lead_card_suit = self.ht.get_card_suit(lead_card)
        lead_card_rank = self.ht.get_card_rank(lead_card)
        
        if len(board_card) != 4:
            self.ht.errmsg("Invalid board card size" + str(len(board_card)))
        
        idx = 0
        rotate = 0
        next_lead_player = lead_player
        highest_rank = lead_card_rank
        # Decide who can win this round, and the winner will lead next round
        for p in players:
            if idx == 0:
                # Skip the leader himself
                idx += 1
                continue
            
            shoot_card = board_card[idx]
            shoot_card_suit = self.ht.get_card_suit(shoot_card)
            shoot_card_rank = self.ht.get_card_rank(shoot_card)
            
            if shoot_card_suit == lead_card_suit:
                if shoot_card_rank > highest_rank:
                    next_lead_player = p
                    rotate = idx
                    highest_rank = shoot_card_rank

            idx += 1

        self.ht.msg("Next lead player: " + next_lead_player.get_name())
        if rotate > 0:
            self.__rotate_player_position(rotate)
        
        # Calculate the score for next leader
        score = self.__calc_card_score(board_card)
        self.ht.msg("Player: " + next_lead_player.get_name() + ", Score: " + str(next_lead_player.inc_point(score)))

    def __auto_pick_avail_1st_round(self, suit, player, is_lead):
        output = []
        
        if is_lead == True:
            # Only '2c' is available for 1st shoot.
            output = [self.ht.str2card('2c', fixfmt = False)]
            return output
        else:
            unused = player.get_unused_card([self.ht.str2suit('Club')])
            if len(unused) == 0:
                print ("Payer does not have suit Club")
                unused = player.get_unused_card(
                    [self.ht.str2suit('Spade'), self.ht.str2suit('Diamond')]
                    )
                if len(unused) == 0:
                    print ("Player does not have suit Spade/Diamond. Allow heart break!")
                    unused = player.get_unused_card([self.ht.str2suit('Heart')])
                    output = unused
                    return output
                else:
                    output = unused
                    return output
            else:
                output = unused
                return output
    
    def __auto_pick_avail_norm(self, suit, player, is_lead):
        if (is_lead):
            if self.is_hb == True:
                # Can use any card after heart-break
                unused = player.get_unused_card([
                    self.ht.str2suit('Spade'), self.ht.str2suit('Heart'), self.ht.str2suit('Diamond'), self.ht.str2suit('Club')
                    ])
                return unused
            else:
                # Cannot use heart before heart-break
                unused = player.get_unused_card([
                    self.ht.str2suit('Spade'), self.ht.str2suit('Diamond'), self.ht.str2suit('Club')
                    ])
                if len(unused) == 0:
                    unused = player.get_unused_card([
                        self.ht.str2suit('Spade'), self.ht.str2suit('Heart'), self.ht.str2suit('Diamond'), self.ht.str2suit('Club')
                        ]) 
                    return unused
                else:
                    return unused
        else:
            # Follow the suit
            unused = player.get_unused_card([suit])
            if len(unused) == 0:
                print ("Do not have the same suit" + str(suit))
                # Can use any card, can heart-break
                unused = player.get_unused_card([
                    self.ht.str2suit('Spade'), self.ht.str2suit('Heart'), self.ht.str2suit('Diamond'), self.ht.str2suit('Club')
                    ])
                return unused
            else:
                return unused
    
    def __auto_pick_avail(self, suit, player, is_lead):
        output = []
        
        if self.roundnum == 1:
            output = self.__auto_pick_avail_1st_round(suit, player, is_lead)
        else:
            output = self.__auto_pick_avail_norm(suit, player, is_lead)
        
        if len(output) == 0:
            self.ht.errmsg("Do not have available cards to use")
        
        return output
                

    def __auto_progress_round_1(self):
        self.ht.msg("Round num: " + str(self.roundnum))
        
        # Decide who must start! Find the guy who has '2c'
        club2 = self.ht.str2card('2c', False)
        
        # Find the guy having '2c'
        first_play = None
        rotate_cnt = 0
        for p in self.players:
            p_unused_card_list = p.get_unused_card([self.ht.str2suit('Club')])
            
            if p_unused_card_list.count(club2) > 0:
                first_play = p
                print ("...Start from player: " + first_play.get_name())
                break
            else:
                rotate_cnt += 1
            
        if first_play == None:
            self.ht.errmsg("Invalid start player")
        else:
            self.__rotate_player_position(rotate_cnt)
            pass
        
        # Get user card and add it
        is_lead = True
        lead_suit = self.ht.str2suit('Club')
        for p in self.players:        
            data = {
                'board_card': self.board_card, 'used_card': self.used_card,
                'unused_card': p.get_unused_card(),
                'roundnum': self.roundnum,
                'is_hb': self.is_hb, 'players': self.players}
            
            data['avail_card'] = self.__auto_pick_avail(lead_suit, p, is_lead)
            
            self.ht.msg("Turn: " + p.get_name())
            output = p.time2shoot(data)
            if output == None:
                self.ht.errmsg("Invalid card output")
        
            self.used_card.append(output)
            self.board_card.append(output)
            if is_lead == True:
                is_lead = False
                lead_suit = self.ht.get_card_suit(output)
            
        self.__round_over()
        self.nextround()
    
    def __auto_progress_round(self):
        self.ht.msg("Round num: " + str(self.roundnum))
        
        # Get user card and add it
        is_lead = True
        lead_suit = None
        for p in self.players:        
            data = {
                'board_card': self.board_card, 'used_card': self.used_card,
                'unused_card': p.get_unused_card(),
                'roundnum': self.roundnum,
                'is_hb': self.is_hb, 'players': self.players}
            
            data['avail_card'] = self.__auto_pick_avail(lead_suit, p, is_lead)
            
            self.ht.msg("Turn: " + p.get_name())
            output = p.time2shoot(data)
            if output == None:
                self.ht.errmsg("Invalid card output")
            
            if self.is_hb == False and self.ht.get_card_suit(output) == self.ht.str2suit('Heart'):
                self.msg("Heart break")
                self.is_hb = True
                
            self.used_card.append(output)
            self.board_card.append(output)
            if is_lead == True:
                is_lead = False
                lead_suit = self.ht.get_card_suit(output)
            
        self.__round_over()
        self.nextround()
    
    def __auto_progress_round_last(self):
        self.__auto_progress_round()
        
        self.ht.msg("Last round: " + str(self.roundnum))
        # FIXME
        
    # Automatically play game and ask a player to shoot a card
    def auto_progress(self):
        print("")
        
        if self.roundnum == 1:
            return self.__auto_progress_round_1()
        
        if self.roundnum == 13:
            return self.__auto_progress_round_last()
        
        return self.__auto_progress_round()
    

# ;