
from PokerBot import PokerBot, system_log, Card, Htapi

class HacBotV(PokerBot, Htapi):
    """
    Random bot. Life is luck. Life is random. Life is life.
    """
    SM_THOLD_PASS3 = 9.0
    ANTISCORE_THOLD_PASS3 = 8.0
    
    def __init__(self, name, is_debug=False):
        super(HacBotV, self).__init__(name)

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
        
        self.stat['expose_ah_mode'] = False
        self.stat['shoot_moon_mode'] = True
        
        self.stat['pass3_antiscore_ability'] = 0
        self.stat['pass3_antiscore_ability_history'] = []
        self.stat['pass3_sm_ability'] = 0
        self.stat['pass3_sm_ability_history'] = []
        
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
        
    def _calc_hand_cards_num(self, my_hand_cards, reverse=False):
        card_num_stat = {'S': 0, 'H': 0, 'D': 0, 'C': 0}        
        for c in my_hand_cards:
            card_num_stat[c.get_suit()] += 1
             
        card_num_stat_sorted = sorted(card_num_stat.iteritems(), key=lambda (k, v): (v, k), reverse=reverse)
        return card_num_stat_sorted

    def _select_card2pass_shoot_moon_mode(self, my_hand_cards):
        """
        Pop out 1 card to pass
        
        Reserve cards in long suit.
        Remove small cards in shortage suit.
        """
        card_num_stat_sorted = self._calc_hand_cards_num(my_hand_cards)
        
        # Remove small cards in shortage suit.
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            if suit == 'H':
                continue
            
            same_suit_cards = self.htapi.get_cards_by_suit(my_hand_cards, suit)
            smaller_card = self.htapi.pick_smaller_card(same_suit_cards, [Card('9S')], auto_choose_big=False)
            
            if smaller_card != None:
                return self.htapi.remove_card(my_hand_cards, smaller_card)
            
        # Remove suit
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            if suit == 'H':
                continue
            
            same_suit_cards = self.htapi.get_cards_by_suit(my_hand_cards, suit)
            small_card = self.htapi.pick_small_card(same_suit_cards)
            
            return self.htapi.remove_card(my_hand_cards, small_card)
        
        # Remove suit, in case I have 13 hearts... A.A
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            same_suit_cards = self.htapi.get_cards_by_suit(my_hand_cards, suit)
            small_card = self.htapi.pick_small_card(same_suit_cards)
            
            return self.htapi.remove_card(my_hand_cards, small_card)
        
        self.htapi.errmsg("BUG")
        
    def _select_card2pass(self, my_hand_cards):
        """
        Pop out 1 card to pass. Anti-score mode.
        
        - Remove big rank card from shortage suit
        - Remove big rank card in long suit
        """
        
        card_num_stat_sorted = self._calc_hand_cards_num(my_hand_cards)
        card_num_stat_sorted_dict = dict(card_num_stat_sorted)
        
        if card_num_stat_sorted_dict['S'] <= 1:
            # Spade in shortage. KS and AS will be dangerous.
            card = self.htapi.remove_card(my_hand_cards, Card('KS'))
            if card != None:
                return card
            
            card = self.htapi.remove_card(my_hand_cards, Card('AS'))
            if card != None:
                return card
            
            card = self.htapi.remove_card(my_hand_cards, Card('QS'))
            if card != None:
                return card
        
        # Remove big rank card from shortage suit
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            same_suit_cards = self.htapi.get_cards_by_suit(my_hand_cards, suit)
            big_card = self.htapi.pick_big_card(same_suit_cards)
            
            if big_card.get_rank_num() > Card('8S').get_rank_num():
                return self.htapi.remove_card(my_hand_cards, big_card)
        
        # Remove suit
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            same_suit_cards = self.htapi.get_cards_by_suit(my_hand_cards, suit)
            big_card = self.htapi.pick_big_card(same_suit_cards)
            
            return self.htapi.remove_card(my_hand_cards, big_card)
        
        self.htapi.errmsg("BUG")
           
    def _get_unused_cards_by_suits(self, my_hand_cards, suits=[]):
        """
        Get unused cards of other opponents so that I can know how many cards are left..
        """
        
        all52cards = self.htapi.get52cards()
        output = all52cards

        self.htapi.remove_cards(output, self.stat['usedCard'])
        self.htapi.remove_cards(output, my_hand_cards)

        if len(suits) == 0:
            # Do not need to pick a specific suit
            pass
        else:
            # Pick unused cards of target suits
            output = self.htapi.get_cards_by_suits(output, suits)

        return output
    
    def _get_unused_cards(self, my_hand_cards):
        return self._get_unused_cards_by_suits(my_hand_cards, suits=[])
    
    def _calc_antiscore_point(self, card, oppo_unused_cards):
        """
        Calculate the power of this card to avoid taking grades.
        
        Output: 1.0 - This card won't take the trick. (Won't be next leader)
        Output: 0.0 - This card will take the trick. Possibly a big card.
        """
        
        oppo_unused_same_suit_cards = self.htapi.get_cards_by_suit(oppo_unused_cards, card.get_suit())
        if len(oppo_unused_same_suit_cards) == 0:
            # Opponent does not have same suit...
#             oppo_no_score_cards = self.htapi.find_no_score_cards(oppo_unused_cards)
#             return len(oppo_no_score_cards) / float(len(oppo_unused_cards))
            return 0.0
        
        lose_cnt = 0
        for c in oppo_unused_same_suit_cards:
            if card.get_rank_num() < c.get_rank_num():
                lose_cnt += 1
        
        return lose_cnt / float(len(oppo_unused_same_suit_cards)) 

    def _calc_sm_point(self, card, oppo_unused_cards):
        """
        Calculate the power of this card to win others.
        """
        oppo_unused_same_suit_cards = self.htapi.get_cards_by_suit(oppo_unused_cards, card.get_suit())
        if len(oppo_unused_same_suit_cards) == 0:
            # No same suit at opponent.
            return 1.0
        
        win_cnt = 0
        for c in oppo_unused_same_suit_cards:
            if card.get_rank_num() > c.get_rank_num():
                win_cnt += 1
        
        return win_cnt / float(len(oppo_unused_same_suit_cards))
    
    def _pass_cards_calc_shoot_moon_ability(self, data=None):
        """
        Detect if I can shoot the moon.
        """
        my_hand_cards = self.stat['hand']
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
        
        if len(oppo_unused_cards) != (52 - 13) or len(my_hand_cards) != 13:
            self.htapi.errmsg("BUG")
            
        return self._pick_card_calc_shoot_moon_ability(data=None)
    
    def _pass_cards_calc_antiscore_ability(self, data):
        """
        Detect if I can shoot the moon.
        """
        my_hand_cards = self.stat['hand']
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
         
        my_antiscore_point = 0.0
        for c in my_hand_cards:
            this_antiscore_point = self._calc_antiscore_point(c, oppo_unused_cards)
            if this_antiscore_point >= 1.0:
                my_antiscore_point += this_antiscore_point * 2
            else:    
                my_antiscore_point += this_antiscore_point       
            
        return my_antiscore_point 
    
    def _pass_cards_shoot_moon_mode(self, data):
        """
        Pick 3 cards which can help myself to shoot moon.
        """
        my_hand_cards = self.stat['hand']

        output = []
        for i in range(3):
            card = self._select_card2pass_shoot_moon_mode(my_hand_cards)
            if card == None:
                self.htapi.errmsg("Cannot pick a card to pass")
            output.append(card.toString())
            
        self.htapi.dbg(self.get_name() + " pass 3 cards: " + format(output))
        return output
    
    def _pass_cards_anti_score_mode(self, data):
        """
        Pick 3 cards which can avoid taking score
        """
        my_hand_cards = self.stat['hand']
        
        output = []
        for i in range(3):
            card = self._select_card2pass(my_hand_cards)
            if card == None:
                self.htapi.errmsg("Cannot pick a card to pass")
            output.append(card.toString())
            
        self.htapi.dbg(self.get_name() + " pass 3 cards: " + format(output))
        return output
        
    def pass_cards(self, data):
        """
        Event: Pick 3 cards to pass to others
        """
        self.stat['hand'] = self.htapi.clone_cards([Card(x) for x in data['self']['cards']])
        self.stat['hand'] = self.htapi.arrange_cards(self.stat['hand'])
        
        self.htapi.dbg("Select 3 cards from: " + format(self.stat['hand']))
        
        sm_ability = self._pass_cards_calc_shoot_moon_ability()
        self.stat['pass3_sm_ability'] = sm_ability
        self.stat['pass3_antiscore_ability'] = self._pass_cards_calc_antiscore_ability(data)
        self.htapi.dbg("Ability stat. sm: ", format(sm_ability), "antiscore: ", format(self.stat['pass3_antiscore_ability']))
        if sm_ability > self.SM_THOLD_PASS3:
            self.htapi.dbg("shoot moon mode pass3: " + str(sm_ability))
            return self._pass_cards_shoot_moon_mode(data)
        else:
            self.htapi.dbg("anti score mode pass3")
            return self._pass_cards_anti_score_mode(data)

    def receive_opponent_cards(self, data):
        """
        Event: Recv 3 cards from one opponent
        """
        pass
    
    def ______pass3(self):
        pass

    def expose_my_cards(self, data):
        """
        Event: The server asks me to expose AH...
        """
        output = []
        candidates = data['cards']
        if candidates == None or len(candidates) == 0:
            return output

        candidates = [Card(x) for x in candidates]
        
        if self.htapi.find_card(candidates, Card('AH')) == None:
            return output
        
        if self.stat['pass3_sm_ability'] > self.SM_THOLD_PASS3:
            output = ['AH']
            return output
        
        if self.stat['pass3_antiscore_ability'] > self.ANTISCORE_THOLD_PASS3:
            # I have confidence not taking score...
            output = ['AH']
            return output
        
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
                self.stat['expose_ah_mode'] = True
            else:
                local_player['expose'] = False
    
    def ______expose_card(self):
        pass
    
    def _pick_card_calc_shoot_moon_ability(self, data=None):
        """
        Detect if I can shoot the moon.
        """
        my_hand_cards = self.stat['hand']
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
            
        my_sm_point = 0.0
        for c in my_hand_cards:
            this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
            if this_sm_point >= 1.0:
                my_sm_point += this_sm_point * 2
            else:    
                my_sm_point += this_sm_point       
            
        return my_sm_point 
        
    def _pick_card_should_i_sm(self, data):
        """
        Predict my ability to shoot moon.
        """
        if self.stat['shoot_moon_mode'] == False:
            return False
                
        return True
    
    def _pick_card_sm_mode_leadplay(self, data):
        
        self.htapi.errmsg("BUG")
    
    def _pick_card_sm_mode_midplay(self, data):
        
        self.htapi.errmsg("BUG")
        
    def _pick_card_sm_mode_lastplay(self, data):
        
        self.htapi.errmsg("BUG")
        
    def _pick_card_sm_mode(self, data):
        """
        Pick a card!
        """
        # roundPlayers is in the correct order of shooting cards.
        round_players = data['roundPlayers']
          
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())
  
#         # Get players in next turn.
#         self.stat['nextPlayers'] = data['roundPlayers'][(my_pos + 1):]
        
        if my_pos == 0:
            card = self._pick_card_sm_mode_leadplay(data)            
        elif my_pos == 3:
            card = self._pick_card_sm_mode_midplay(data)
        else:
            card = self._pick_card_sm_mode_lastplay(data)
            
        return card
    
    def _pick_card_antiscore_mode_leadplay(self, data):
        """
        I don't want to take a trick...
        """
        my_hand_cards = self.stat['hand']
        oppo_unused_cards = self.get_unused_cards(my_hand_cards)

        candidates = []
        current_min_point = None
        for c in my_hand_cards:
            as_point = self._calc_antiscore_point(c, oppo_unused_cards)
            
            if current_min_point == None:
                current_min_point = as_point
                candidates = [c]
            elif as_point < current_min_point:
                candidates = [c]
                current_min_point = as_point
            else:
                candidates += c
                
        #
        # Pick small rank cards from shortage suit.
        #
        card_num_stat_sorted = self._calc_hand_cards_num(my_hand_cards)
           
            
        
    
    def _pick_card_antiscore_mode_midplay(self, data):
        
        self.htapi.errmsg("BUG")
        
    def _pick_card_antiscore_mode_lastplay(self, data):
        
        self.htapi.errmsg("BUG")
        
    def _pick_card_antiscore_mode(self, data):
        """
        Pick a card!
        """
        # roundPlayers is in the correct order of shooting cards.
        round_players = data['roundPlayers']
          
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())
  
#         # Get players in next turn.
#         self.stat['nextPlayers'] = data['roundPlayers'][(my_pos + 1):]
        
        if my_pos == 0:
            card = self._pick_card_antiscore_mode_leadplay(data)            
        elif my_pos == 3:
            card = self._pick_card_antiscore_mode_lastplay(data)
        else:
            card = self._pick_card_antiscore_mode_midplay(data)
            
        return card
        
    def pick_card(self, data):
        """
        Event: My turn to shoot a card.
        """
#         # roundPlayers is in the correct order of shooting cards.
#         round_players = data['roundPlayers']
#          
#         # Identify my position in this round
#         my_pos = round_players.index(self.get_name())
#  
#         # Get players in next turn.
#         self.stat['nextPlayers'] = data['roundPlayers'][(my_pos + 1):]
#         
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        self.stat['hand'] = self.htapi.arrange_cards(self.stat['hand'])
#         my_hand_cards = self.htapi.clone_cards(self.stat['hand'])
#         my_avail_cards = self.htapi.clone_cards([Card(x) for x in data['self']['candidateCards']])    

        if self._pick_card_should_i_sm(data) == True:
            card2shoot = self._pick_card_sm_mode(data)
        else:
            card2shoot = self._pick_card_antiscore_mode(data)

        self.htapi.dbg(self.get_name() + " shoot card: " + format(card2shoot) + ", from: " + format(data['self']['cards']) + ", next players: " + format(self.stat['nextPlayers']))
        return card2shoot.toString()
    
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
        
    def ______pick(self):
        pass
        
    def _round_end_detect_shoot_moon_ability(self):
        #
        # Check if somebody get any score and give up shoot-moon mode.
        #
        
        if self.stat['shoot_moon_mode'] == False:
            # Already disable shoot moon mode.
            return
        
        for key in self.players:
            lp = self.players[key]
            score = self.htapi.calc_score(lp['pick'], is_expose_ah=self.stat['expose_ah_mode'])
            if score != 0 and lp['playerName'] != self.get_name():
                self.htapi.dbg("Give up shoot-moon mode...So sad.")
                self.stat['shoot_moon_mode'] = False
                
    def round_end(self, data):
        """
        Event: round end
        """
        round_player_name = data['roundPlayer']
        round_cards = self.stat['roundCard']
        
        local_player = self.players[round_player_name]
        local_player['pick'] += round_cards
        
        self.htapi.dbg("Player: " + round_player_name + " picked 4 cards: " + format(round_cards), " overall pick: " + format(local_player['pick']))
        
        # Disable shoot moon mode if somebody rx a score.
        self._round_end_detect_shoot_moon_ability()
        
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
                if player['playerName'] == self.get_name():
                    self.stat['pass3_sm_ability_history'].append(self.stat['pass3_sm_ability'])
            
            if player['gameScore'] == 0 and self.get_name() == player['playerName']:
                self.stat['pass3_antiscore_ability_history'].append(self.stat['pass3_antiscore_ability'])

        for key in self.players.keys():
            p = self.players[key]
            # Reset deal-specific data.
            p['score'] = 0
            p['shoot'] = []
            p['expose'] = False
            p['pick'] = []
        
        self.stat['usedCard'] = []
        self.stat['shoot_moon_mode'] = True
        self.stat['expose_ah_mode'] = False
        self.stat['pass3_sm_ability'] = 0.0
        self.stat['pass3_antiscore_ability'] = 0.0
    
    def game_over(self, data):
        """
        Event: game end
        """
        self.htapi.dbg(format(data))
        
        print(self.stat)
        print(self.players[self.get_name()])
