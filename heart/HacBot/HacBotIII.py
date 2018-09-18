from PokerBot import PokerBot, system_log, Card, Htapi

class HacBotIII(PokerBot, Htapi):
    """
    Hac's policy-based bot.
    
    This is a bot able to shoot moon. When I get a lot of big-rank cards. DO IT!
    Don't want to avoid opponents shooting the moon, because I don't loss any money :-) 
    """
    
    SM_THOLD_PASS3 = 0.6
    SM_THOLD_PICK = 0.1
    
    def __init__(self, name, is_debug=False):
        super(HacBotIII, self).__init__(name)

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
        
    def _select_card2pass_shoot_moon_mode(self, my_hand_cards):
        """
        Pop out 1 card to pass
        
        The rule here is to pick the small cards in shortage
        """
        
        #
        # Find the non-empty suit but the card num is low.
        # 
        # TODO: Try to remove non-heart suit can help shoot-moon ability.
        #
        card_num_stat = {'S': 0, 'H': 0, 'D': 0, 'C': 0}        
        for c in my_hand_cards:
            card_num_stat[c.get_suit()] += 1
            
        card_num_stat_sorted = sorted(card_num_stat.iteritems(), key=lambda (k, v): (v, k))
        
        #
        # Try to remove a suit
        #
        for di in card_num_stat_sorted:
            k, v = di
            if v != 0:
                pick_suit, v = di
                
                tgt_cards = self.htapi.get_cards_by_suit(my_hand_cards, pick_suit)
                tgt_cards = self.htapi.arrange_cards(tgt_cards)
                
                smaller_card = self.htapi.pick_smaller_card(tgt_cards, [Card('9S')])
                if smaller_card != None:
                    return self.htapi.remove_card(my_hand_cards, smaller_card)


        #        
        # In case...
        #
        for di in card_num_stat_sorted:
            k, v = di
            if v != 0:
                pick_suit, v = di
                
                tgt_cards = self.htapi.get_cards_by_suit(my_hand_cards, pick_suit)
                tgt_cards = self.htapi.arrange_cards(tgt_cards)
                
                card = tgt_cards[0]
                return self.htapi.remove_card(my_hand_cards, card)
            
        self.htapi.errmsg("BUG")
        
        card = my_hand_cards[0]
        return self.htapi.remove_card(my_hand_cards, card)
        
    def _select_card2pass(self, my_hand_cards):
        """
        Pop out 1 card to pass
        """
        
        card = self.htapi.remove_card(my_hand_cards, Card('KS'))
        if card != None:
            return card
        
        card = self.htapi.remove_card(my_hand_cards, Card('AS'))
        if card != None:
            return card
        
        #
        # It's important to remove high rank cards if I have too many...
        #
        # TODO: Remove high-rank cards in shortage.
        #
        my_high_rank_cards = self.htapi.find_cards(my_hand_cards, self.big_rank_cards)
        my_high_rank_noscore_cards = self.htapi.find_no_penalty_cards(my_high_rank_cards)
        if len(my_high_rank_noscore_cards) >= 4:
            suit_list = []
            
            for c in my_high_rank_noscore_cards:
                this_suit = c.get_suit()
                
                if suit_list.count(this_suit) == 0:
                    suit_list.append(this_suit)
            
            if len(suit_list) == 0:
                self.htapi.errmsg("Invalid suit list: 0")
        else:
            suit_list = ['S', 'H', 'D', 'C']
            
        # Found the suit in shortage
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
        candidate_list = self.htapi.arrange_cards(candidate_list)
        card = candidate_list.pop()
        
        return self.htapi.remove_card(my_hand_cards, card)
    
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
    
    def _do_i_have_too_many_low_rank_cards(self):
        my_hand_cards = self.stat['hand']
        
        low_rank_card_num = 0
        for c in my_hand_cards:
            if c.get_rank_num() < Card("TS").get_rank_num:
                low_rank_card_num += 1
                
        # TBD
        if low_rank_card_num >= 9:
            return True
        else:
            return False
    
    def pass_cards(self, data):
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        self.stat['hand'] = self.htapi.arrange_cards(self.stat['hand'])
        
        self.htapi.dbg("Select 3 cards from: " + format(self.stat['hand']))
        
        sm_ability = self._calc_shoot_moon_ability(data) 
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
        
        #
        # TODO: Be smarter... calculate shoot-moon ability, or anti-score ability
        # If I know I won't take any score, expose AH!
        # If I want to shoot the moon, expose AH!
        # 
                
        # Calculate the rate that I will get penalty...
        # The simplest calculation is to check if I have too many big-rank cards
        my_big_cards = self.htapi.find_cards(my_hand_cards, self.big_rank_cards)
        my_big_card_num = len(my_big_cards)
        if my_big_card_num > 2 and my_big_card_num < 5:
            """
            Have some but not many high-rank.
            """
            return output
        
        #        
        # Expose AH!
        #
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
                self.stat['expose_ah_mode'] = True
            else:
                local_player['expose'] = False

    def _lead_play_monte_carlo_predict_penalty(self, card2shoot, opponent_cards, round_cards=[]):
        """
        Will I take the trick if I select the card2shoot!?
        
        Output: The possibility to get score if I shoot the card: 0 ~ 100.0
        """

        # TODO: Improve prediction by the players!
#         next_players = self.stat['nextPlayers'] 
#         next_player_num = len(next_players)

        # Calculate the number of cards will... make me eat the trick.
        opponent_same_suit_cards = self.htapi.get_cards_by_suit(opponent_cards, card2shoot.get_suit())
        if len(opponent_same_suit_cards) == 0:
            opponent_score_cards = self.htapi.find_score_cards(opponent_cards)
            if len(opponent_score_cards) > 0:
                return 100.0
            else:
                # There's no penalty card now. Won't eat 
                return 0.0                
        
        # Danger level means the chance I will eat a trick. 
        # If the card2shoot is high-rank, the chance is higher, of course.
        danger_level = 0
        for ocard in opponent_same_suit_cards:
            if ocard.get_rank_num() < card2shoot.get_rank_num():
                # Oops...
                danger_level += 1
        
        percentage_max = float(len(opponent_same_suit_cards))
        percentage = danger_level / percentage_max
        return percentage
    
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
        
    def __leadplay(self, data):
        """
        I am the round leader. I want to avoid tacking the trick, so choose the best!
        """
        
        my_hand_cards = self.stat['hand']
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]    
        
        opponent_cards = self._get_unused_cards_by_suits(my_hand_cards)
        
        selected = []
        peak_percentage = 0
        for c in my_avail_cards:
            # If I pick this card, will I take the trick?            
            percentage = self._lead_play_monte_carlo_predict_penalty(c, opponent_cards, round_cards=[])
            
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
        card2shoot = prefer_cards.pop(0)
        self.htapi.dbg("Select card" + format(card2shoot))
        
        return card2shoot
    
    def __midplay(self, data):
        round_cards = self.stat['roundCard']
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
        round_cards = self.stat['roundCard']
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
    
    def pick_card_anti_score_mode(self, data):
        # roundPlayers is in the correct order of shooting cards.
        round_players = data['roundPlayers']
        
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())

        # Get players in next turn.
        self.stat['nextPlayers'] = data['roundPlayers'][(my_pos + 1):]
        
        if my_pos == 0:
            card = self.__leadplay(data)            
        elif my_pos == 3:
            card = self.__lastplay(data)
        else:
            card = self.__midplay(data)
        
        return card
    
    def _calc_shoot_moon_ability(self, data):
        """
        Detect if I can shoot the moon.
        """
        if self.stat['shoot_moon_mode'] == False:
            # I know it's unlikely to shoot the moon... Give up
            return 0.0
        
        # Detect factors: all played turn cards, hand_card
        my_hand_cards = self.stat['hand']
        all_used_cards = self.stat['usedCard']
        
        opponent_unused_cards = self._get_unused_cards_by_suits(my_hand_cards)
        opponent_unused_penalty_cards = self.htapi.find_penalty_cards(opponent_unused_cards)
        
        left_turn_num = len(my_hand_cards)
        
        """
        The prediction is simple, calculate how many turns I can win.
        """
        win_count = 0
        for c in my_hand_cards:
            unused_same_suit_cards = self.htapi.get_cards_by_suit(opponent_unused_cards, c.get_suit())
            if len(unused_same_suit_cards) > 0:
                unused_same_suit_cards = self.htapi.arrange_cards(unused_same_suit_cards)
                
                if c.get_rank_num() > unused_same_suit_cards[-1].get_rank_num():
                    win_count += 1
                    
        """
        Patch: If I have many high-rank cards, win_count ++
        """
        if len(self.htapi.find_cards(my_hand_cards, self.big_rank_cards)) > (len(my_hand_cards) / 2):
            win_count += len(self.htapi.find_cards(my_hand_cards, self.big_rank_cards)) - (len(my_hand_cards) / 2) 
        
        self.htapi.dbg("shoot moon ability: " + str(win_count) + " / " + str(left_turn_num))
        return win_count / float(left_turn_num)
      
    
    def __leadplay_shoot_moon_mode(self, data):
        """
        I am the lead player. Try to eat heart and QS!
        
        Make sure I have the a card that can win a score. 
        If I don't have, I will fail to shoot. Try Monte Carlo simulation.
        """
        my_hand_cards = self.stat['hand']
        
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]
        all_used_cards = self.stat['usedCard']
        opponent_cards = self._get_unused_cards_by_suits(my_hand_cards)
        
        #
        # Shoot the card that nobody has the same suit.
        #
        for c in my_avail_cards:
            my_same_suit_card_num = self.htapi.get_cards_by_suit(my_avail_cards, c.get_suit())
            used_same_suit_card_num = self.htapi.get_cards_by_suit(all_used_cards, c.get_suit())
            
            if my_same_suit_card_num + used_same_suit_card_num == 13:
                self.htapi.dbg("Select nobody have suit to play the trick.")
                return c
        
        #
        # Heart eater.
        #
        my_heart_cards = self.htapi.get_cards_by_suit(my_avail_cards, 'H')
        if len(my_heart_cards) > 0:
            unused_heart_cards = self.htapi.get_cards_by_suit(opponent_cards, 'H')
            if len(unused_heart_cards) > 0:
                unused_heart_cards = self.htapi.arrange_cards(unused_heart_cards)
            
                for c in my_heart_cards:
                    if c.get_rank_num() > unused_heart_cards[-1].get_rank_num():
                        return c      
        
        #        
        # Shoot the card that I will win the round.
        #
        for c in my_avail_cards:
            unused_same_suit_cards = self.htapi.get_cards_by_suit(opponent_cards, c.get_suit())
            if len(unused_same_suit_cards) > 0:
                unused_same_suit_cards = self.htapi.arrange_cards(unused_same_suit_cards)
                
                if c.get_rank_num() > unused_same_suit_cards[-1].get_rank_num():
                    return c
            
        #
        # If I don't have cards can win, ...shoot no score suit left a lot.
        #
        pick_suit = None
        pick_suit_num = 0
        for c in my_avail_cards:
            unused_same_suit_cards = self.htapi.get_cards_by_suit(opponent_cards, c.get_suit())
            
            if pick_suit_num == 0:
                pick_suit_num = len(unused_same_suit_cards)
                pick_suit = c.get_suit()
            elif  len(unused_same_suit_cards) > pick_suit_num:
                pick_suit_num = len(unused_same_suit_cards)
                pick_suit = c.get_suit()
                
        candidates = self.htapi.get_cards_by_suit(my_avail_cards, pick_suit)
        candidates = self.htapi.arrange_cards(candidates)
        
        return candidates[-1] 
    
    def __midplay_shoot_moon_mode(self, data):
        """
        Check if the next players are in shortage of lead card suit.
        If they are in shortage, shoot the biggest card I have to win the leader ship.
        
        TBD: Use Monte Carlo simulation here?
        """
        return self.__leadplay_shoot_moon_mode(data)
    
    def __lastplay_shoot_moon_mode(self, data):
        """
        I am the last player: See if there's a score card!
        """
        
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]
        
        round_cards = self.stat['roundCard']
        lead_card = round_cards[0]
        if self.htapi.calc_card_num_by_suit(my_avail_cards, lead_card.get_suit()) == 0:
            """
            I don't have the same suit. Pick a no-score small card :-)
            """
            candidates = self.htapi.find_no_penalty_cards(my_avail_cards)
            if len(candidates) == 0:
                # Sorry, don't have no penalty card. The shoot-moon action will fail.
                return self.pick_card_anti_score_mode(data)                
            
            #
            # Detect the suit in shortage 
            #
            card_num_stat = {'S': 0, 'H': 0, 'D': 0, 'C': 0}
            for c in candidates:
                card_num_stat[c.get_suit()] += 1

            # Sort the card_num_stat
            card_num_stat_sorted = sorted(card_num_stat.iteritems(), key=lambda (k, v): (v, k))

            # Fetch the suit in shortage, but ignore zero number suit.
            for di in card_num_stat_sorted:
                k, v = di
                if v != 0:
                    pick_suit, v = di
                    break
                
            candidates = self.htapi.get_cards_by_suit(candidates, pick_suit)
            candidates = self.htapi.arrange_cards(candidates)
            no_score_small_card = candidates.pop(0)
            
            return no_score_small_card
        
        elif self.htapi.calc_score(round_cards) > 0:
            """
            I have the same suit. Try to win the score card.
            """
            bigger_card = self.htapi.pick_bigger_card(my_avail_cards, round_cards)
            if bigger_card == None:
                # Too bad, I can't win... switch to anti-score mode.
                return self.pick_card_anti_score_mode(data)
            else:
                return bigger_card
        else:
            """
            I have the same suit. No score on board... should I take the leadership? Yes?! TBD?
            """
            bigger_card = self.htapi.pick_bigger_card(my_avail_cards, round_cards)
            if bigger_card == None:
                # Too bad, I can't win... 
                return self.htapi.pick_small_card(my_avail_cards)
            else:
                return bigger_card
    
    def pick_card_shoot_moon_mode(self, data):
        # roundPlayers is in the correct order of shooting cards.
        round_players = data['roundPlayers']
        
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())

        # Get players in next turn.
        self.stat['nextPlayers'] = data['roundPlayers'][(my_pos + 1):]
        
        if my_pos == 0:
            self.htapi.dbg("sm lead play")
            card = self.__leadplay_shoot_moon_mode(data)            
        elif my_pos == 3:
            self.htapi.dbg("sm last play")
            card = self.__lastplay_shoot_moon_mode(data)
        else:
            self.htapi.dbg("sm mid play")
            card = self.__midplay_shoot_moon_mode(data)
            
        return card
    
    def detect_sm_player(self, data):
        """
        If there are two player have score. Not possible to shoot moon.
        
        If there's a player having all the score... he is suspicious.
        """
        score_player_cnt = 0
        score_player = None
        for key in self.players:
            lp = self.players[key]
            score = self.htapi.calc_score(lp['pick'], is_expose_ah=self.stat['expose_ah_mode'])
            if score != 0:
                score_player_cnt += 1
                score_player = lp
                
        if score_player_cnt >= 2:
            # No player can shoot moon.
            return False
        
        if score_player_cnt == 1:
            if score_player['playerName'] == self.get_name():
                return False
            
            if len(self.htapi.find_penalty_cards(score_player['pick'])) >= 5:
                if self.htapi.find_card(score_player['pick'], Card('QS')) != None:
                    self.htapi.dbg("There's a pig " + score_player['playerName'] + ", kill!")
                    return True
                else:
                    self.htapi.dbg("There's a pig " + score_player['playerName'] + ", but...")
                    return False
            
            return False
        
        return False

    def pick_card(self, data):
        """
        Event: My turn to shoot a card.
        """
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        
        if self.detect_sm_player(data) == True:
            self.htapi.dbg("anti-shoot-moon mode")
            card = self.pick_card_shoot_moon_mode(data)
            
        if self._calc_shoot_moon_ability(data) >= self.SM_THOLD_PICK:
            self.htapi.dbg("shoot-moon mode")
            card = self.pick_card_shoot_moon_mode(data)
        else:
            self.htapi.dbg("aniti-score mode")
            card = self.pick_card_anti_score_mode(data)
            
        # NOTE: Do not remove the card in hand card, do it ad turn end event.
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
    
    def game_over(self, data):
        """
        Event: game end
        """
        self.htapi.dbg(format(data))
