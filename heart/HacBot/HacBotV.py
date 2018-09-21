
from PokerBot import PokerBot, system_log, Card, Htapi

class HacBotV(PokerBot, Htapi):
    """
    Anti-Score Mode (AS)
    Shoot-Moon Mode (SM)
    """
    SM_THOLD_PASS3 = 10.0
    SM_THOLD_PICK = 12.0
    AS_THOLD_PASS3 = 8.0
    
    def __init__(self, name, is_debug=False):
        super(HacBotV, self).__init__(name)

        self.htapi = Htapi(is_debug=is_debug)
                       
        self.players = {}
        self.stat = {}
        self.stat['roundCard'] = [] 
        self.stat['usedCard'] = []
        self.stat['nextPlayers'] = []
        self.stat['roundPlayers'] = []
        
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
        self.stat['sm_mode'] = True
        
        self.stat['pass3_as_ability'] = 0
        self.stat['pass3_as_ability_history'] = []
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
                'sm': 0,
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
        self.stat['hand'] = self.htapi.clone_cards(self.stat['hand'])
        
    def _calc_hand_cards_num(self, my_hand_cards, reverse=False):
        card_num_stat = {'S': 0, 'H': 0, 'D': 0, 'C': 0}        
        for c in my_hand_cards:
            card_num_stat[c.get_suit()] += 1
             
        card_num_stat_sorted = sorted(card_num_stat.iteritems(), key=lambda (k, v): (v, k), reverse=reverse)
        return card_num_stat_sorted

    def _select_card2pass_sm_mode(self, my_hand_cards):
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
#         card_num_stat_sorted_dict = dict(card_num_stat_sorted)
        
        if self.htapi.find_card(my_hand_cards, Card('QS')) == None:
            card = self.htapi.remove_card(my_hand_cards, Card('AS'))
            if card != None:
                return card
            
            # Spade in shortage. KS and AS will be dangerous.
            card = self.htapi.remove_card(my_hand_cards, Card('KS'))
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
    
    def _get_used_cards(self):
        return self.stat['usedCard']
    
    def _get_used_cards_by_suits(self, suits=[]):
        used_cards = self.stat['usedCard']
        output = self.htapi.get_cards_by_suits(used_cards, suits)
        return output
    
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
    
    def _get_round_cards(self):
        round_cards = self.stat['roundCard']
        return round_cards
    
    def _get_avail_cards(self):
        my_avail_cards = self.stat['avail']
        return my_avail_cards
    
    def _get_hand_cards(self):
        my_hand_cards = self.stat['hand']
        return my_hand_cards
    
    def _calc_as_point(self, card, oppo_unused_cards):
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
        
        point = lose_cnt / float(len(oppo_unused_same_suit_cards))
        return point 

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
    
    def _pass_cards_calc_sm_ability(self, data=None):
        """
        Detect if I can shoot the moon.
        """
        my_hand_cards = self._get_hand_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
        
        if len(oppo_unused_cards) != (52 - 13) or len(my_hand_cards) != 13:
            self.htapi.errmsg("BUG")
            
        return self._pick_card_calc_sm_ability(data=None)
    
    def _pass_cards_calc_as_ability(self, data=None):
        """
        Detect if I can anti-score
        """
        return self._pick_card_calc_as_ability(data=None)
    
    def _pass_cards_sm_mode(self, data):
        """
        Pick 3 cards which can help myself to shoot moon.
        """
        my_hand_cards = self._get_hand_cards()

        output = []
        for i in range(3):
            card = self._select_card2pass_sm_mode(my_hand_cards)
            if card == None:
                self.htapi.errmsg("Cannot pick a card to pass")
            output.append(card.toString())
            
        self.htapi.dbg(self.get_name() + " pass 3 cards: " + format(output))
        return output
    
    def _pass_cards_as_mode(self, data):
        """
        Pick 3 cards which can avoid taking score
        """
        my_hand_cards = self._get_hand_cards()
        
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
        
        sm_ability = self._pass_cards_calc_sm_ability()
        as_ability = self._pass_cards_calc_as_ability()
        self.stat['pass3_sm_ability'] = sm_ability
        self.stat['pass3_as_ability'] = as_ability
        self.htapi.dbg("Ability stat. sm: ", format(sm_ability), ", as: ", format(self.stat['pass3_as_ability']))
        if sm_ability > self.SM_THOLD_PASS3:
            self.htapi.dbg("shoot moon mode pass3: " + str(sm_ability))
            return self._pass_cards_sm_mode(data)
        else:
            
#             if as_ability >= self.AS_THOLD_PASS3:
#                 self.htapi.dbg("Possibly do not have chance to sm because of high as ability: ", format(as_ability))
#                 self.stat['sm_mode'] = False
            
            self.htapi.dbg("anti score mode pass3")
            return self._pass_cards_as_mode(data)

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
        
        if self.stat['pass3_as_ability'] > self.AS_THOLD_PASS3:
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
    
    def _do_i_have_lead_suit(self):
        """
        Cannot be called at lead play!!
        """
        round_cards = self._get_round_cards()
        if len(round_cards) == 0:
            self.errmsg("BUG")
        
        lead_card = round_cards[0]
        
        my_avail_cards = self._get_avail_cards()
        
        if len(self.htapi.get_cards_by_suit(my_avail_cards, lead_card.get_suit())) == 0:
            return False
        
        return True        
    
    def _pick_card_calc_sm_ability(self, data=None):
        """
        Detect if I can shoot the moon.
        """
        my_hand_cards = self._get_hand_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
            
        my_sm_point = 0.0
        for c in my_hand_cards:
            this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
            if this_sm_point >= 1.0:
                my_sm_point += this_sm_point * 2
            else:    
                my_sm_point += this_sm_point
                
        my_sm_point *= (13 / float(len(my_hand_cards)))
        my_sm_point = round(my_sm_point, 3)       
        print("my_hand_cards: ", my_hand_cards, ", sm ability -> " + format(my_sm_point))
        return my_sm_point 
        
    def _pick_card_calc_as_ability(self, data=None):
        """
        Detect if I can anti-score
        """
        my_hand_cards = self._get_hand_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
         
        my_as_point = 0.0
        for c in my_hand_cards:
            this_as_point = self._calc_as_point(c, oppo_unused_cards)
            if this_as_point >= 1.0:
                my_as_point += this_as_point * 2
            else:    
                my_as_point += this_as_point       
        
        my_as_point *= (13 / float(len(my_hand_cards)))
        my_as_point = round(my_as_point, 3)
        print("my_hand_cards: ", my_hand_cards, ", as ability -> " + format(my_as_point))
        return my_as_point 
        
    def _pick_card_should_i_sm(self, data):
        """
        Predict my ability to shoot moon.
        """  
        sm_ability = self._pick_card_calc_sm_ability(data=None)
        as_ability = self._pick_card_calc_as_ability(data=None)
            
        if self.stat['sm_mode'] == False:
            return False

        if sm_ability > self.SM_THOLD_PICK:
            return True
                
        return False
    
    def _pick_card_sm_mode_leadplay(self, data):
        """
        I am the leader. If I have sm ability. Eat! Eat! Eat you to the hole!
        """       
        my_hand_cards = self._get_hand_cards()
        my_avail_cards = self._get_avail_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
        
        for c in my_avail_cards:
            this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
            
            if this_sm_point >= 1.0 and c.get_suit() == 'H':
                self.htapi.dbg("This card will win..." + format(c))
                return c
            
        for c in my_avail_cards:
            this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
            
            if this_sm_point >= 1.0 and c.get_suit() == 'S':
                self.htapi.dbg("This card will win..." + format(c))
                return c
        
        for c in my_avail_cards:
            this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
            
            if this_sm_point >= 1.0:
                self.htapi.dbg("This card will win..." + format(c))
                return c
        
        # Pick short suit candidates
        self.htapi.dbg("Low strength stage... I am weak :-(.")
        
        max_sm_point = 0
        candidates = []
        for c in my_avail_cards:
            this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
            
            if len(candidates) == 0:
                candidates = [c]
                max_sm_point = this_sm_point
            elif this_sm_point > max_sm_point:
                candidates = [c]
                max_sm_point = this_sm_point    
            else:
                candidates.append(c)
        
        card_num_stat_sorted = self._calc_hand_cards_num(my_hand_cards)
                 
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            prefer_candidates = self.htapi.get_cards_by_suit(my_avail_cards, suit)
            if len(prefer_candidates) > 0:
                prefer_candidates = self.htapi.arrange_cards(prefer_candidates)
                return prefer_candidates[-1]
        
        self.htapi.errmsg("BUG")
        
    def _pick_card_sm_mode_freeplay(self, data):
        """
        Do not have the same suit to follow. So I am free to shoot.
        """
        my_hand_cards = self._get_hand_cards()
        my_avail_cards = self._get_avail_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
        
        my_noscore_cards = self.htapi.find_no_score_cards(my_avail_cards)
        
        if len(my_noscore_cards) == 0:
            # Too bad... I have to give up sm. Turn to as mode.
            return self._pick_card_as_mode(data)
        
        min_sm_cards = []
        min_sm_point = None
        for c in my_noscore_cards:
            this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
            if min_sm_point == None:
                min_sm_point = this_sm_point
                min_sm_cards = [c]
            elif this_sm_point < min_sm_point:
                min_sm_point = this_sm_point
                min_sm_cards = [c]
            else:
                min_sm_cards.append(c)
                
        card_num_stat_sorted = self._calc_hand_cards_num(my_hand_cards)
                 
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            prefer_candidates = self.htapi.get_cards_by_suit(min_sm_cards, suit)
            if len(prefer_candidates) > 0:
                prefer_candidates = self.htapi.arrange_cards(prefer_candidates)
                return prefer_candidates[-1] # TBD: Use the big rank one!?
        
        self.htapi.errmsg("BUG")
    
    def _pick_card_sm_mode_midplay(self, data):
        """
        I am the mid player. 
        
        Try to win...
        """
        round_cards = self._get_round_cards()
        lead_card = round_cards[0]
        filtered_round_cards = self.htapi.get_cards_by_suit(round_cards, lead_card.get_suit())
        round_card_score = self.htapi.calc_score(round_cards)
        
        my_hand_cards = self._get_hand_cards()
        my_avail_cards = self._get_avail_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
        
        if self._do_i_have_lead_suit() == True:
            # Try to win this round.
            if self.htapi.pick_bigger_card(my_avail_cards, filtered_round_cards) == None:
                # ...I don't have bigger card to win.
                self.htapi.dbg("Give up sm... Oops")
                return self._pick_card_as_mode(data)
            else:
                # I have chance to win.            
                king_cards = []
                max_sm_point = 0
                my_avail_cards = self.htapi.arrange_cards(my_avail_cards)
                for c in my_avail_cards:
                    this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
                    
                    if this_sm_point > max_sm_point:
                        max_sm_point = this_sm_point
                        king_cards = [c]
                    elif this_sm_point < max_sm_point:
                        pass
                    else:
                        king_cards.append(c)
                        
                print(" + king cards to win next players are: ", format(king_cards))
                
                if len(king_cards) == 0:
                    self.htapi.errmsg("BUG")                        
                
                return king_cards[0]
        else:
            if round_card_score > 0:
                # Cannot win this round. Have to give up shoot moon.
                self.htapi.dbg("Give up sm... Oops")
                return self._pick_card_as_mode(data)
            else: 
                return self._pick_card_sm_mode_freeplay(data)
        
    def _pick_card_sm_mode_lastplay(self, data):
        """
        I am the last player. I can decide to win or not to win.
        
        Try to win...maybe.
        """
        round_cards = self._get_round_cards()
        lead_card = round_cards[0]
        filtered_round_cards = self.htapi.get_cards_by_suit(round_cards, lead_card.get_suit())
        round_card_score = self.htapi.calc_score(round_cards)
        
        my_hand_cards = self._get_hand_cards()
        my_avail_cards = self._get_avail_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
        
        if self._do_i_have_lead_suit() == True:
            if round_card_score > 0:
                #
                # Have score on this round. I have to decide to take or not to take...
                #
                
                # Try to win...
                bigger_card = self.htapi.pick_bigger_card(my_avail_cards, filtered_round_cards)
                if bigger_card != None:
                    return bigger_card
                else:
                    # Cannot win this round. Have to give up shoot moon.
                    self.htapi.dbg("Give up sm... Oops")
                    return self._pick_card_as_mode(data)
            else:
                #            
                # Have no score, I can give up to win if I have a too weak point.
                #
                same_suit_card_num = self.htapi.calc_card_num_by_suit(my_hand_cards + oppo_unused_cards, lead_card.get_suit())
                
                min_sm_card = None
                min_sm_point = None
                for c in my_avail_cards:
                    this_sm_point = self._calc_sm_point(c, oppo_unused_cards)
                    if min_sm_point == None:
                        min_sm_point = this_sm_point
                        min_sm_card = c
                    elif this_sm_point < min_sm_point:
                        min_sm_point = this_sm_point
                        min_sm_card = c
                
                if same_suit_card_num > 9:
                    return min_sm_card
                else:
                    # Try to win this round...
                    bigger_card = self.htapi.pick_bigger_card(my_avail_cards, filtered_round_cards)
                    if bigger_card != None:
                        return bigger_card
                    else:
                        # Cannot win this round.
                        return min_sm_card
                                        
        else:
            if round_card_score > 0:
                # Cannot win this round. Have to give up shoot moon.
                self.htapi.dbg("Give up sm... Oops")
                return self._pick_card_as_mode(data)
            else: 
                return self._pick_card_sm_mode_freeplay(data)
        
    def _pick_card_sm_mode(self, data):
        """
        Pick a card!
        """
        # roundPlayers is in the correct order of shooting cards.
        round_players = self.stat['roundPlayers']
          
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())
        
        if my_pos == 0:
            card = self._pick_card_sm_mode_leadplay(data)            
        elif my_pos == 3:
            card = self._pick_card_sm_mode_midplay(data)
        else:
            card = self._pick_card_sm_mode_lastplay(data)
            
        return card
    
    def _pick_card_as_mode_leadplay(self, data):
        """
        I don't want to take a trick...
        """
        my_avail_cards = self._get_avail_cards()
        
        my_hand_cards = self._get_hand_cards()
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)
        
        candidates = []
        current_max_point = None
        for c in my_avail_cards:
            as_point = self._calc_as_point(c, oppo_unused_cards)
            
            if current_max_point == None:
                current_max_point = as_point
                candidates = [c]
            elif as_point > current_max_point:
                candidates = [c]
                current_max_point = as_point
            else:
                candidates.append(c)
                
        if len(candidates) == 0:
            self.htapi.errmsg("BUG")
        
        #
        # Try to make others eat 'QS'
        #
        spade_candidates = self.htapi.get_cards_by_suit(candidates, 'S')
        if len(spade_candidates) > 0:
            used_spade_cards = self._get_used_cards_by_suits(['S'])
            if self.htapi.find_card(used_spade_cards, Card('QS')) != None:
                for c in spade_candidates:
                    if self._calc_as_point(c, oppo_unused_cards) == 1.0:
                        return c

        #
        # Pick strong small heart cards first, so that I won't eat more later.
        #
        heart_candidates = self.htapi.get_cards_by_suit(candidates, 'H')
        if len(heart_candidates) > 0:
            for c in heart_candidates:
                if self._calc_as_point(c, oppo_unused_cards) == 1.0:
                    return c   

        #
        # Pick small rank cards from shortage suit first
        #
        card_num_stat_sorted = self._calc_hand_cards_num(my_hand_cards)
                 
        for di in card_num_stat_sorted:
            suit, num = di
            if num == 0:
                continue
            
            prefer_candidates = self.htapi.get_cards_by_suit(candidates, suit)
            if len(prefer_candidates) > 0:
                return prefer_candidates[0]
        
        self.htapi.errmsg("BUG")            

    def _get_current_winner(self):
        
        round_players = self.stat['roundPlayers']
        
        round_cards = self._get_round_cards()
        if len(round_cards) == 0:
            self.errmsg("BUG")
            
        lead_card = round_cards[0]
        
        idx = 0
        winner_idx = 0
        for c in round_cards:
            if c.get_suit() == lead_card.get_suit() and c.get_rank_num() > lead_card.get_rank_num():
                winner_idx = idx
            idx += 1
            
        winner = round_players[winner_idx]
        
        return winner

    def _pick_card_as_mode_freeplay(self, data):
        """
        I am in midplay or last play. I don't have lead suit, so I can shoot anything.
        """
        my_avail_cards = self.htapi.arrange_cards(self._get_avail_cards())
        my_hand_cards = self._get_hand_cards()
        
        round_cards = self._get_round_cards()
        if len(round_cards) == 0:
            self.errmsg("BUG")
            
        oppo_unused_cards = self._get_unused_cards(my_hand_cards)

        #
        # Shoot QS out if I have chance.
        #
        card = self.htapi.find_card(my_avail_cards, Card('QS'))
        if card != None:
            return card 

        #
        # Prefer AS, KS if the oppo has QS. Otherwise, KS, AS are not so dangerous...
        #
        if self.htapi.find_card(oppo_unused_cards, Card('QS')) != None:
            card = self.htapi.find_card(my_avail_cards, Card('AS'))
            if card != None:
                return card
            
            card = self.htapi.find_card(my_avail_cards, Card('KS'))
            if card != None:
                return card            
        
        #
        # Shoot dangerous heart while opponents still have hearts.
        #
        oppo_heart_cards = self.htapi.get_cards_by_suit(oppo_unused_cards, 'H')
        if len(oppo_heart_cards) > 0:
            my_heart_cards = self.htapi.get_cards_by_suit(my_avail_cards, 'H')
            my_heart_cards = self.htapi.arrange_cards(my_heart_cards)
            for c in reversed(my_heart_cards):
                point = self._calc_as_point(c, oppo_unused_cards)
                
                if point < 0.5:
                    return c
        
        #
        # Shoot 'TC'
        #
        card = self.htapi.find_card(my_avail_cards, Card('TC'))
        if card != None:
            return card 
        
        #
        # Choose the most dangerous cards 
        #
        candidates = []
        as_point_min = None
        for c in my_avail_cards:
            this_as_point = self._calc_as_point(c, oppo_unused_cards)
            
            if self.htapi.calc_card_num_by_suit(oppo_unused_cards, c.get_suit()) == 0:
                # Don't worry. The oppo won't send the suit again... so I won't eat the trick.
                # But if I am the lead... I will eat 100%.
                continue
            
            if as_point_min == None:
                as_point_min = this_as_point
                candidates = [c]
            elif this_as_point < as_point_min:
                as_point_min = this_as_point
                candidates = [c]
            else:
                candidates.append(c)

                
        if len(candidates) > 0:
            card_num_stat_sorted = self._calc_hand_cards_num(my_hand_cards)
            
            # Remove small cards in shortage suit.
            for di in card_num_stat_sorted:
                suit, num = di
                if num == 0:
                    continue
                
                prefer_candidates = self.htapi.get_cards_by_suit(candidates, suit)
                if len(prefer_candidates) > 0:
                    prefer_candidates = self.htapi.arrange_cards(prefer_candidates)
                    return prefer_candidates[-1]

        #
        # Shoot the min as point card
        #
        candidates = []
        as_point_min = None
        for c in my_avail_cards:
            this_as_point = self._calc_as_point(c, oppo_unused_cards)
            
            if as_point_min == None:
                as_point_min = this_as_point
                candidates = [c]
            elif this_as_point < as_point_min:
                as_point_min = this_as_point
                candidates = [c]
            else:
                candidates.append(c)
        
        if len(candidates) == 0:
            self.htapi.errmsg("BUG")
                
        candidates = self.htapi.arrange_cards(candidates)
        return candidates[-1]  
    
    def _pick_card_as_mode_midplay(self, data):
        my_hand_cards = self._get_hand_cards()
        my_avail_cards = self._get_avail_cards()
        
        round_cards = self._get_round_cards()
        lead_card = round_cards[0]
        
        oppo_same_suit_cards = self._get_unused_cards_by_suits(my_hand_cards, [lead_card.get_suit()])
        
        round_card_score = self.htapi.calc_score(round_cards)

        if self._do_i_have_lead_suit() == True:
            #
            # I have the lead suit... Don't have many choice...
            #
            filtered_round_cards = self.htapi.get_cards_by_suit(round_cards, lead_card.get_suit())
            card2shoot = self.htapi.pick_smaller_card(my_avail_cards, filtered_round_cards, auto_choose_big=False)
            if card2shoot != None:
                return card2shoot
            else:
                if self.stat['sm_mode'] == False and len(oppo_same_suit_cards) > 9:
                    return self.htapi.pick_big_card(my_avail_cards)
                else:
                    return self.htapi.pick_bigger_card(my_avail_cards, filtered_round_cards)
        else:
            #
            # I don't have the same suit. Can do anything.
            #
            return self._pick_card_as_mode_freeplay(data)
                
        self.htapi.errmsg("BUG")
        
    def _pick_card_as_mode_lastplay(self, data):
        my_hand_cards = self._get_hand_cards()
        my_avail_cards = self._get_avail_cards()
        
        round_cards = self._get_round_cards()
        lead_card = round_cards[0]
        
        oppo_same_suit_cards = self._get_unused_cards_by_suits(my_hand_cards, [lead_card.get_suit()])
        
        round_card_score = self.htapi.calc_score(round_cards)

        if self._do_i_have_lead_suit() == True:
            #
            # I have the lead suit... Don't have many choice...
            #
            if round_card_score > 0:
                filtered_round_cards = self.htapi.get_cards_by_suit(round_cards, lead_card.get_suit())
                card2shoot = self.htapi.pick_smaller_card(my_avail_cards, filtered_round_cards, auto_choose_big=False)
                if card2shoot != None:
                    return card2shoot
                else:
                    if self.stat['sm_mode'] == False:
                        return self.htapi.pick_big_card(my_avail_cards)
                    else:
                        return self.htapi.pick_bigger_card(my_avail_cards, filtered_round_cards)
            else:
                return self.htapi.pick_big_card(my_avail_cards)
        else:
            return self._pick_card_as_mode_freeplay(data)
        
    def _pick_card_as_mode(self, data):
        """
        Pick a card!
        """
        # roundPlayers is in the correct order of shooting cards.
        round_players = self.stat['roundPlayers']
          
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())
        
        if my_pos == 0:
            card = self._pick_card_as_mode_leadplay(data)            
        elif my_pos == 3:
            card = self._pick_card_as_mode_lastplay(data)
        else:
            card = self._pick_card_as_mode_midplay(data)
            
        return card
        
    def pick_card(self, data):
        """
        Event: My turn to shoot a card.
        """
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        self.stat['hand'] = self.htapi.arrange_cards(self.stat['hand'])
        
        self.stat['avail'] = self.htapi.arrange_cards([Card(x) for x in data['self']['candidateCards']])
  
        self.stat['roundPlayers'] = data['roundPlayers'][:] 
  
        # Get players in next turn.
        round_players = self.stat['roundPlayers']
        my_pos = round_players.index(self.get_name())
        self.stat['nextPlayers'] = data['roundPlayers'][(my_pos + 1):]
        
        if self._pick_card_should_i_sm(data) == True:
            self.htapi.dbg("sm mode")
            card2shoot = self._pick_card_sm_mode(data)
        else:
            self.htapi.dbg("as mode")
            card2shoot = self._pick_card_as_mode(data)

        self.htapi.dbg(self.get_name() + " shoot card: " + format(card2shoot) + ", from: " + format(data['self']['cards']) + ", next players: " + format(self.stat['nextPlayers']))
        return card2shoot.toString()
    
    def _detect_card_shortage(self, local_player, turn_card):
        #
        # If the player is not lead player and he shoots a card not the same as lead card,
        # mark the player as card shortage.
        #
        # If I know the shortage status of players, can have advantage to predict.
        #
        
        round_cards = self._get_round_cards()
        
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
        
    def _round_end_detect_sm_ability(self):
        #
        # Check if somebody get any score and give up shoot-moon mode.
        #
        
        if self.stat['sm_mode'] == False:
            # Already disable shoot moon mode.
            return
        
        for key in self.players:
            lp = self.players[key]
            score = self.htapi.calc_score(lp['pick'], is_expose_ah=self.stat['expose_ah_mode'])
            if score != 0 and lp['playerName'] != self.get_name():
                self.htapi.dbg("Give up shoot-moon mode...So sad.")
                self.stat['sm_mode'] = False
                
    def round_end(self, data):
        """
        Event: round end
        """
        round_player_name = data['roundPlayer']
        round_cards = self._get_round_cards()
        
        local_player = self.players[round_player_name]
        local_player['pick'] += round_cards
        
        self.htapi.dbg("Player: " + round_player_name + " picked 4 cards: " + format(round_cards), " overall pick: " + format(local_player['pick']))
        
        # Disable shoot moon mode if somebody rx a score.
        self._round_end_detect_sm_ability()
        
        #
        # Reset round data
        #
        self.stat['roundCard'] = []
        self.stat['nextPlayers'] = []
        self.stat['roundPlayers'] = []
    
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
                local_player['sm'] += 1
                if player['playerName'] == self.get_name():
                    self.stat['pass3_sm_ability_history'].append(self.stat['pass3_sm_ability'])
            
            if player['gameScore'] == 0 and self.get_name() == player['playerName']:
                self.stat['pass3_as_ability_history'].append(self.stat['pass3_as_ability'])

        for key in self.players.keys():
            p = self.players[key]
            # Reset deal-specific data.
            p['score'] = 0
            p['shoot'] = []
            p['expose'] = False
            p['pick'] = []
        
        self.stat['usedCard'] = []
        self.stat['sm_mode'] = True
        self.stat['expose_ah_mode'] = False
        self.stat['pass3_sm_ability'] = 0.0
        self.stat['pass3_as_ability'] = 0.0
    
    def game_over(self, data):
        """
        Event: game end
        """
        self.htapi.dbg(format(data))
        
        print(self.stat)
        print(self.players[self.get_name()])
