#!/usr/bin/env python
#
# Heart Poker Game
#

from deuces import Card
import sys, traceback
import random

from uptime import uptime

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

        if card == self.str2card('Qs', fixfmt=False):
            # 'Qs' is 13 point
            output = 13
        elif suit == 2:
            output = 1

        return output
    
    def cardl2htpoint(self, card_list):
        output = 0
        
        for c in card_list:
            output += self.card2htpoint(c)
            
        return output

    def card_arrange(self, card_list):
        # Sort by card suit and rank
        output = sorted(card_list, key=lambda v: (self.get_card_suit(v) * 20 + self.get_card_rank(v)))
        return output
    
    def card_remove(self, list2remove, card):
        if list2remove.count(card) > 0:
            list2remove.remove(card)
            return card
        
        return None
    
    def card_remove_list(self, list2remove, card_list):
        output = []
        
        for c in card_list:
            removed_card = self.card_remove(list2remove, c)
            output.append(removed_card)
        
        return output
    
    def card_select_by_suit(self, suit, card_list):
        """
        Get cards with the same suit
        """
        output = []
        for c in card_list:
            if self.get_card_suit(c) == suit:
                output.append(c)
        return output
    
    def card_select_by_card_list(self, card2take_list, card_list):
        """
        Pick up card by order
        Output: A list of cards which are also in input list, too
        """
        output = []
        for c2take in card2take_list:
            if card_list.count(c2take) > 0:
                output.append(c2take)
        
        return output
        
        
    def calc_card_num_by_suit(self, suit, card_list):
        """
        Calculate the number of card in target suit, e.g. if you want to know how many hearts in card list...
        """
        same_suit_list = self.card_select_by_suit(suit, card_list)
        return len(same_suit_list) 


# Heart Player 
class htplayer(htapi):
    ht = htapi()

    def nextround(self, data2p = None):
        self.botai.nextround(data2p)

    def nextgame(self, data2p = None):
        self.botai.nextgame(data2p)
        
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
        self.shoot_moon_cnt = 0

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

    def arrange_card(self):
        self.unused_card = self.ht.card_arrange(self.unused_card)

    def remove_card(self, card_list):
        if len(card_list) > len(self.unused_card):
            self.ht.errmsg("Cannot remove card num: " + str(len(card_list)))
        
        for c in card_list:
            self.unused_card.remove(c)
            
    def add_card(self, card_list):
        for c in card_list:
            self.unused_card.append(c)
            
        self.arrange_card()

    def deal(self, card_list):
        self.unused_card = card_list
        
        data2p = {}
        data2p['player_unused_card'] = card_list
        self.botai.deal(data2p)
    
    def time2pass(self, data2p):
        return self.botai.time2pass(data2p)
        
    def time2shoot(self, data2p):
        data2p['player_unused_card'] = self.unused_card

        data2p['player_point'] = self.point
        data2p['player_point_history'] = self.point_history
        
        pick = self.botai.time2shoot(data2p)
        
        if self.unused_card.count(pick) == 0:
            self.ht.errmsg("Invalid output card of user" + self.name)
            
        self.unused_card.remove(pick)
        self.used_card.append(pick)
        
        return pick

    def shoot_moon(self):
        self.shoot_moon_cnt += 1

# Heart Game
# 13 round of each game. 4 ppl.
class htgame(htplayer, htapi):
    ht = htapi()

    def nextround(self):
        data2p = None
        # FIXME: Add data2p for player botai
        for p in self.players:
            p.nextround(data2p)
        
        self.roundnum += 1
        self.board_card = []

    def nextgame(self):
        data2p = None # FIXME: Add data2p for player botai
        for p in self.players:
            p.nextgame(data2p)

        self.used_card = []
        self.roundnum = 1
        self.is_hb = False
        self.is_shoot_moon = False
        
        self.gamenum += 1

    def __init__(self, players):
        self.player_num = 0
        self.players = []
        for p in players:
            self.players.append(p)
            self.player_num += 1

        self.used_card = []
        self.board_card = []

        self.gamenum = 1
        self.roundnum = 1
        self.is_hb = False # Heart break in this round
        self.is_shoot_moon = False
        
        random.seed(int(uptime()))

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

        if len(unused_card) == 0:
            return True
        else:
            self.ht.errmsg("Can't shuffle all cards")
            return False

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
        score = self.ht.cardl2htpoint(board_card)
        self.ht.msg("Player: " + next_lead_player.get_name() + 
                    ", Score: " + str(next_lead_player.get_point()) +  " -> " + str(next_lead_player.inc_point(score)))

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
        
        # Ask players to pass 3 card by correct order
        # NOTE: Cannot pass '2c'
        self.auto_pass()
        
        # Get user card and add it
        is_lead = True
        lead_suit = self.ht.str2suit('Club')
        for p in self.players:        
            data2p = {
                'board_card': self.board_card, 'used_card': self.used_card,
                'unused_card': p.get_unused_card(),
                'roundnum': self.roundnum,
                'is_hb': self.is_hb, 'players': self.players}
            
            data2p['avail_card'] = self.__auto_pick_avail(lead_suit, p, is_lead)
            
            self.ht.msg("Turn: " + p.get_name())
            output = p.time2shoot(data2p)
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
            data2p = {
                'board_card': self.board_card, 'used_card': self.used_card,
                'unused_card': p.get_unused_card(),
                'roundnum': self.roundnum,
                'is_hb': self.is_hb, 'players': self.players}
            
            data2p['avail_card'] = self.__auto_pick_avail(lead_suit, p, is_lead)
            
            self.ht.msg("Turn: " + p.get_name())
            output = p.time2shoot(data2p)
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
        
        """
        Re-calculate scores if somebody shoot the moon
        """
        shoot_moon_player = None
        for p in self.players:
            score = p.get_point()
            if score == 26:
                shoot_moon_player = p
            elif score > 26:
                self.ht.errmsg("Invalid score: " + str(score) + " of player: " + p.get_name())
        
        if shoot_moon_player != None:
            self.msg("Player: " + shoot_moon_player.get_name() + " shoot moon")
            
            self.is_shoot_moon = True
            
            # Add 26 points at other players, dec 26 points at shoot moon player
            for p in self.players:
                if p.get_ident() == shoot_moon_player.get_ident():
                    p.dec_point(26)
                else:
                    p.inc_point(26)
                    
            # Inform the user the shoot moon event
            shoot_moon_player.shoot_moon()
        
        
    # Automatically play game and ask a player to shoot a card
    def auto_progress(self):
        print("")
        
        if self.roundnum == 1:
            return self.__auto_progress_round_1()
        
        if self.roundnum == 13:
            return self.__auto_progress_round_last()
        
        return self.__auto_progress_round()
    
    def auto_pass(self):
        
        exchange_list = []
        for p in self.players:
            # Get user's hand card, but skip '2c'
            unused_card = p.get_unused_card()
            avail_card = []
            for c in unused_card:
                if c != self.ht.str2card("2c", fixfmt=False):
                    avail_card.append(c)
            
            data2p = {}
            data2p['unused_card'] = unused_card[:]
            data2p['avail_card'] = avail_card[:]
            
            exchange = []
            exchange = p.time2pass(data2p)
            
            if len(exchange) != 3:
                self.ht.errmsg("Invalid exchange output of user: " + p.get_name())
                
            for c in exchange:
                if c == self.ht.str2card("2c", fixfmt=False):
                    self.ht.errmsg("Invalid exchange output '2c' of user: " + p.get_name())
                    
            exchange_list.append(exchange)

        idx = 0
        for p in self.players:
            card2remove = exchange_list[idx]
            card2add = exchange_list[idx - 1]
            
            # Remove the player's card
            self.ht.msg("Player: " + p.get_name() + ", Remove: " + self.ht.get_card_pretty_list(card2remove) + 
                   ", Add: " + self.ht.get_card_pretty_list(card2add))
            p.remove_card(card2remove)
            p.add_card(card2add)
                      
            idx += 1
    
    def get_game_result(self):
        output = {}
        for p in self.players:
            output[p.get_ident()] = {
                "name": p.get_name(),
                "score": p.get_point(), 
                "total": p.get_point_total()
                      }
        return output

    def display_game_result(self):
        self.ht.msg("Game Result: ")
        """
        Score board
        """
        output = self.get_game_result()
        self.ht.msg(format(output))
    
# ;