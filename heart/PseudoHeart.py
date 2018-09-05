# coding=UTF-8
import os, sys, json, random
from PokerBot import Card, system_log, Htapi

class PseudoHeart(Htapi):
    """
    Create a virtual game which can play faster!
    """
    game_score_cards = [Card("QS"), Card("TC"),
                        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
                        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
                        Card("QH"), Card("KH"), Card("AH")]
    
    # If have all penalty cards, the player shoots the moon and win a lot.
    game_penalty_cards = [Card("QS"),
                        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
                        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
                        Card("QH"), Card("KH"), Card("AH")]
    
    def __init__(self, player_bots):
        if len(player_bots) != 4:
            print ("Invalid player num != 4")
            sys.exit()
    
        self.db = {}  
        self.htapi = Htapi(is_debug=True)
        self.game_heart_cards = self.htapi.get_cards_by_suit(self.htapi.get52cards(), 'H')
        
        # Save bot object into self.player_bots 
        self.player_tups = []
        id = 0
        for p in player_bots:
            player_tup = {
                # Constant data
                'bot': p, 'name': p.get_name(), 'id': id,
                # Deal data
                'hand_origin': [], 'recv3': [], 'pass3': [],
                'hand': [], 'pick': [], 'round_pick': [], 'shoot': [], 'expose': False, 'score': 0, 'shoot_moon': False,
                # Game data 
                'score_game': 0,
                # MISC data 
                'score_accl': 0, 'shoot_moon_accl': 0
                            }
            self.player_tups.append(player_tup)
            self.htapi.msg("Add new player: " + player_tup['name'])
            id += 1
        
        self.db['dealNumber'] = 0
        self.db['gameNumber'] = 0
        
    def player_tups_rotate(self, shift=1):
        """
        Shift order of the players.
        """
        for i in range(shift):
            p = self.player_tups.pop(0)
            self.player_tups.append(p)
        
    def game_next_deal(self):
        self.db['dealNumber'] += 1
        self.db['heartBreak'] = False
        self.db['expose'] = False
        self.db['unusedCards'] = self.htapi.get52cards()
        self.db['usedCards'] = []
        
        self.db['roundNumber'] = 0
        self.db['is_first_play'] = True
        
        for ptup in self.player_tups:
            ptup['pick'] = []
            
            ptup['recv3'] = []
            ptup['pass3'] = []
            ptup['hand_origin'] = []
            ptup['hand'] = []
            
            ptup['shoot'] = []
            ptup['score'] = 0
            ptup['shoot_moon'] = False
            
        # Re-arrange position to default layout
        for i in range(0, 4):
            ctup = self.player_tups[0]
            if ctup['id'] == 0:
                break
            else:
                self.player_tups_rotate(1)
        
    def game_next_round(self):
        self.db['roundNumber'] += 1
        self.db['roundCards'] = []
        
        for ptup in self.player_tups:
            ptup['round_pick'] = []
            
    def _ev_new_game(self, ptup):
        """
        Event: new game
        """
        players = []
        for ptup_this in self.player_tups:
            pdata = {
                'playerName': ptup_this['name'],
                'playerNumber': ptup_this['id'],
                'status': 0 
                     }
            players.append(pdata)            
        
        data = {
            'players': players
            }
        
        pbot = ptup['bot']
        pbot.new_game(data)

    def _ev_receive_cards(self, ptup):
            """
            Event: receive_cards
            
            data = {"players": [{"playerName": "hac", "cards": ["3S", "8S", "9S", "TS", "JS", "4H", "6H", "9H", "3D", "7D", "9D", "JD", "8C"], "dealNumber": 1, "gameNumber": 1}]}
            """
            data = {
                    'players': [
                        {
                            'playerName': ptup['name'],
                            'cards': self.htapi.clone_cards([x.toString() for x in ptup['hand']]),
                            
                            'gameNumber': self.db['gameNumber'],
                            'dealNumber': self.db['dealNumber'],
                        },
                        {
                            'playerName': 'self',
                            'cards': self.htapi.clone_cards([x.toString() for x in ptup['hand']]),
                            
                            'gameNumber': self.db['gameNumber'],
                            'dealNumber': self.db['dealNumber'],
                        },
                        # TBD: Add other players' data? Not necessary, I guess.
                    ]
                }

            # Call player method.            
            pbot = ptup['bot']
            pbot.receive_cards(data)
    
    def _ev_deal_end(self, ptup):
        """
        End of a deal
        """
        data = {}
        data['dealNumber'] = self.db['dealNumber']
        data['roundNumber'] = self.db['roundNumber']
        data['gameNumber'] = self.db['gameNumber']
        
        data['players'] = []
        data_players = data['players']
        
        for ptup_this in self.player_tups:
            # Setup this player data. 
            pld = {}
            
            pld['playerNumber'] = ptup_this['id']
            pld['playerName'] = ptup_this['name']
            pld['dealScore'] = ptup_this['score']
            pld['gameScore'] = ptup_this['score_game']
            
            pld['scoreCards'] = self.htapi.clone_cards([x.toString() for x in ptup_this['pick']])
            pld['initialCards'] = self.htapi.clone_cards([x.toString() for x in ptup_this['hand_origin']]) 
            pld['receivedCards'] = self.htapi.clone_cards([x.toString() for x in ptup_this['recv3']])
            pld['pickedCards'] = self.htapi.clone_cards([x.toString() for x in ptup_this['pass3']])
            pld['shootingTheMoon'] = ptup_this['shoot_moon']
            
            # Add data into list
            data_players.append(pld)
        
        pbot = ptup['bot']
        pbot.deal_end(data)

    def _ev_pass3cards(self, ptup):
        """
        Output: picked 3 cards
        """
        data = {}
        data['self'] = {
            'cards': self.htapi.clone_cards([x.toString() for x in ptup['hand']])
            }
        
        pbot = ptup['bot']
        picked = pbot.pass_cards(data)
        
        if picked == None or len(picked) != 3:
            self.htapi.errmsg("Invalid picked num of bot: " + ptup['name'])
        
        # Convert ['XX', 'OO', 'AA'] into Card list
        picked = [Card(c) for c in picked]
        
        # Verify if there's any duplicated picked card to avoid buggy bot.
        for c in picked:
            if picked.count(c) != 1:
                self.errmsg("Player: " + ptup['name'] + " tries to pick invalid cards: " + format(picked))
            
        # Check picked cards are really in list to keep away from stupid bot.
        found_cards = self.htapi.find_cards(ptup['hand'], picked)
        if found_cards == None or len(found_cards) != 3:
            self.htapi.errmsg("Player: " + ptup['name'] + " attemps to pick invalid cards")
        
        return picked

    def _ev_receive_opponent_cards(self, ptup, picked, received):
        """
        Pass 3 cards to the player
        """
        data = {
                'players': [
                    {
                        'playerName': ptup['name'],
                        'cards': self.htapi.clone_cards([x.toString() for x in ptup['hand']]),
                        'pickedCards': self.htapi.clone_cards([x.toString() for x in picked]),
                        'receivedCards': self.htapi.clone_cards([x.toString() for x in received]),
                        
                        'gameNumber': self.db['gameNumber'],
                        'dealNumber': self.db['dealNumber'],
                    },
                    {
                        'playerName': 'self',
                        'cards': self.htapi.clone_cards([x.toString() for x in ptup['hand']]),
                        'pickedCards': self.htapi.clone_cards([x.toString() for x in picked]),
                        'receivedCards': self.htapi.clone_cards([x.toString() for x in received]),
                        
                        'gameNumber': self.db['gameNumber'],
                        'dealNumber': self.db['dealNumber'],
                    },
                    # TBD: Add other players' data? Not necessary, I guess.
                ]
            }
        
        pbot = ptup['bot']
        pbot.receive_opponent_cards(data)
        
    def _ev_expose_ah(self, ptup):
        """
        Ask the player if he wants to expose AH.
        """
        data = {
            'dealNumber': self.db['dealNumber'],
            'cards': ['AH'] 
            }
                                      
        pbot = ptup['bot']
        card = pbot.expose_my_cards(data)
        if card == None:
            # The player rejects to expose AH
            return False
        
        return True
    
    def _ev_turn_end(self, ptup, turn_ptup, card2shoot):
        data_players = []
        
        data_player = {}
        data_player['playerName'] = turn_ptup['name']
        data_player['cards'] = self.htapi.clone_cards([card2shoot.toString()]) 
        
        data_players.append(data_player)

        data = {
            'turnCard': card2shoot.toString(),
            'turnPlayer': turn_ptup['name'],
            'players': data_players,
            'serverRandom': str(False)
            }
        
        pbot = ptup['bot']
        pbot.turn_end(data)

    def _ev_round_end(self, ptup, next_lead_ptup):
        """
        Inform the user the end of a round
        """
        data = {'roundPlayers': [], 'roundPlayer': next_lead_ptup['name'], 'players': []}
        
        data_round_players = data['roundPlayers']
        for ptup_this in self.player_tups:
            data_round_players.append(ptup_this['name'])
        
        data_players = data['players']    
        for ptup_this in self.player_tups:
            dp = {}
            
            dp['playerNumber'] = ptup_this['id']
            dp['playerName'] = ptup_this['name']
            dp['gameScore'] = ptup_this['score_game']
            dp['dealScore'] = ptup_this['score']
            dp['shootingTheMoon'] = ptup_this['shoot_moon']
            dp['roundCard'] = ptup_this['shoot'][-1].toString()
            
            data_players.append(dp)
        
        pbot = ptup['bot']
        pbot.round_end(data)  
        
    def _ev_expose_ah_end(self, ptup):
        """
        Inform the player the expose result.
        """
        data = {'players': []}
        data_players = data['players']
        
        for ptup_this in self.player_tups:
            data_this = {}
            
            data_this['playerNumber'] = ptup_this['id']
            data_this['playerName'] = ptup_this['name']
            
            if ptup_this['expose'] == True:
                data_this['exposedCards'] = [Card('AH').toString()]
            else:
                data_this['exposedCards'] = []                
                
            data_players.append(data_this)
            
            if ptup_this['name'] == ptup['name']:
                # Add a 'self'!
                another_data_this = dict(data_this)
                another_data_this['playerName'] = 'self'
                data['self'] = another_data_this

        pbot = ptup['bot']
        pbot.expose_cards_end(data)
        
    def _ev_game_end(self, ptup):
        """
        Inform the player the game result.
        """
        data = {'players': []}
        data_players = data['players']
        
        for ptup_this in self.player_tups:
            data_this = {}
            
            data_this['playerName'] = ptup_this['name']
            data_this['gameScore'] = ptup_this['score_accl']
                
            data_players.append(data_this)
            
        pbot = ptup['bot']
        pbot.game_over(data)
        
    def game_new_deal_manual_deliver(self):
        """
        Deliever fixed 13 cards to each player.
        
        ['7C', '2C', '2D', 'JS', 'QD', '4C', 'QC', 'QS', '3C', 'TD', '2H', '7D', 'KS', 
        '8C', 'JD', '6D', '3D', 'KC', 'AS', '9D', '8S', 'AD', 'TS', '7H', '5D', '4H', 
        '8H', '3H', 'AC', '8D', 'KH', 'KD', '4S', '9C', '2S', '4D', 'JH', '5C', 'JC', 
        'AH', '9H', 'TH', '9S', '6S', '6H', '7S', 'QH', 'TC', '3S', '6C', '5H', '5S']
        """
        card2deliver = [
            ['8C', 'JD', '6D', '3D', 'KC', 'AS', '9D', '8S', 'AH', 'TS', 'JH', '5D', 'QH'],
            ['7C', '2C', '2D', 'JS', 'QD', '4C', 'QC', 'QS', '3C', 'TD', '2H', '7D', 'KS'],
            ['8H', '3H', 'AC', '8D', 'AD', 'KD', '4S', '9C', '2S', '4D', '7H', '5C', 'JC'],
            ['KH', '9H', 'TH', '9S', '6S', '6H', '7S', '4H', 'TC', '3S', '6C', '5H', '5S']            
            ]
        
        # Avoid stupid assignment error. Check if there're 52 different cards
        tgt = []
        card52 = self.htapi.get52cards()
        for card13 in card2deliver:
            card13 = [Card(x) for x in card13]
            tgt += card13
        
        if len(self.htapi.find_cards(tgt, card52)) != 52:
            self.htapi.errmsg("Invalid card2deliver table.")
                
        for ptup in self.player_tups:
            if ptup['id'] >= 4: 
                self.htapi.errmsg("Cannot allow player id >= 4")
                
            # Assume player id is from 0 ~ 3, so assign the cards directly.
            ptup['hand'] = [Card(x) for x in card2deliver[ptup['id']]]
            ptup['hand_origin'] = [Card(x) for x in card2deliver[ptup['id']]]
                        
    def game_new_deal_random_deliver(self):   
        unused_card = self.htapi.get52cards()
        unused_card = self.htapi.shuffle_cards(unused_card)
        
        if len(self.player_tups) != 4:
            self.htapi.errmsg("Invalid player bot num")
        
        # Save 13 cards
        for ptup in self.player_tups:
            picked = []
            for i in range(13):
                picked.append(unused_card.pop())
            
            # The player get 13 cards. Generate event: 'receive_cards'
            self.htapi.arrange_cards(picked)
            ptup['hand'] = picked
            ptup['hand_origin'] = self.htapi.clone_cards(picked)

    def game_new_deal(self):
        """
        Deliver 13 cards to each player
        """             
        manual_deliver = False
        if manual_deliver == True:
            self.htapi.msg(" *** WARNING: You are running in manual-deliver mode")
            self.game_new_deal_manual_deliver()
        else:
            self.game_new_deal_random_deliver()

        # Inform every player            
        for ptup in self.player_tups:
            self._ev_receive_cards(ptup)
        
    def game_pass3cards(self):
        """
        Each player has to pick 3 cards and pass to one opponent.
        """
        
        picked = {}
        for ptup in self.player_tups:
            picked[ptup['name']] = self._ev_pass3cards(ptup)
            
            # Remove the picked 3 cards!
            removed = self.htapi.remove_cards(ptup['hand'], picked[ptup['name']])
            if len(removed) != 3:
                self.htapi.errmsg("Cannot pop picked 3 cards of user: " + ptup['name'])

        card2pass = {}
        for i in range(0, 4):
            src_ptup = self.player_tups[0]
            self.player_tups_rotate(1)
            dst_ptup = self.player_tups[0]
            
            card2pass[dst_ptup['name']] = picked[src_ptup['name']]
            
        for ptup in self.player_tups:
            # Add the recevied 3 cards (from opponent)
            for c in card2pass[ptup['name']]:
                ptup['hand'].append(c)
            self.htapi.arrange_cards(ptup['hand'])
            
            # Then inform the player
            ptup['recv3'] = card2pass[ptup['name']]
            ptup['pass3'] = picked[ptup['name']]         
            self._ev_receive_opponent_cards(ptup, picked[ptup['name']], card2pass[ptup['name']])

    def _get_player_pos(self, ptup):
        """
        Get position of a player. (position=1 ~ 4)
        
        position = 1 means he is the lead playerr.
        """
        position = 1
        for p in self.player_tups:
            if p['name'] == ptup['name']:
                return position
            
            position += 1
            
        self.errmsg("Cannot find player position")
        return None
            
    def _get_candidates(self, ptup):
        """
        Help players to find candidate cards.
        """
        
        if self.db['is_first_play'] == True:
            self.db['is_first_play'] = False
            candidates = [Card('2C')]
            return candidates
        
        player_pos = self._get_player_pos(ptup)

        if player_pos == 1:           
            if self.db['heartBreak'] == True:
                # Can select any card after heart break.
                candidates = ptup['hand']
                return candidates       
            else:
                # Not heart break. Cannot pick heart unless there's no other suit.
                candidates = self.htapi.get_cards_by_suits(ptup['hand'], ['S', 'D', 'C'])
                if len(candidates) == 0:
                    # Only heart suit left. Allow heart break, of course.
                    candidates = ptup['hand']
                
                return candidates
        else:
            # Follow the leading card unless there's no the same suit.
            round_cards = self.db['roundCards']
            lead_card = round_cards[0]
            
            candidates = self.htapi.get_cards_by_suit(ptup['hand'], lead_card.get_suit())
            if len(candidates) > 0:
                return candidates
            else:
                # No card in the same suit. Can pick any card.
                candidates = ptup['hand']
                return candidates
            
        self.errmsg("Cannot get candidate cards")
        return None
    
    def _ev_pick_card(self, ptup):
        """
        Event: pick_card - Ask the player to shoot a card.
        """
        # round cards
        round_cards = self.db['roundCards']
        
        # Candidate cards
        candidates = self._get_candidates(ptup)
        self.htapi.arrange_cards(candidates)
        candidates = self.htapi.clone_cards(candidates)
        
        # Round players
        round_players = []
        for ptup_this in self.player_tups:
            rp = {}
            rp = ptup_this['name']
            round_players.append(rp)
        
        data = {'self': {
                        'cards': [x.toString() for x in ptup['hand']],
                        'candidateCards': [x.toString() for x in candidates],
                        
                        'gameNumber': self.db['gameNumber'],
                        'dealNumber': self.db['dealNumber'],
                        'roundCard': [x.toString() for x in round_cards]
                    },
            'roundPlayers': round_players
        }
        
        pbot = ptup['bot']
        card2shoot = pbot.pick_card(data)
        card2shoot = Card(card2shoot)
        
        return card2shoot    
        
    def game_shoot1card(self, ptup):
        """
        Make the player shoot 1 card!
        """

        card2shoot = self._ev_pick_card(ptup)
        if self.htapi.find_card(ptup['hand'], card2shoot) == None:
            self.errmsg("Cannot shoot un-existed card at player: " + ptup['name'])
            
#         print ("Player " + ptup['name'] + " shoots: ", card2shoot, ", hand: ", ptup['hand'], self.db['unusedCards'])
        
        # Shoot the card.
        removed = self.htapi.remove_card(ptup['hand'], card2shoot)
        if removed == None:
            self.errmsg("(BUG) Cannot remove card: " + card2shoot.toString()) 
        
        ptup['shoot'].append(card2shoot)
           
        self.db['roundCards'].append(card2shoot)
        self.db['usedCards'].append(card2shoot)
        self.db['unusedCards'].remove(card2shoot)

        if card2shoot.get_suit() == 'H':
            self.db['heartBreak'] = True
            
        for ptup_this in self.player_tups:
            self._ev_turn_end(ptup_this, ptup, card2shoot)
            
    def _recalculate_round_score(self, ptup):
        """
        Calculate player's score in current round.
        """
        score = 0
        picked_cards = ptup['pick']
 
        my_score_cards = self.htapi.find_cards(picked_cards, self.game_score_cards)
        my_heart_cards = self.htapi.find_cards(picked_cards, self.game_heart_cards)
        my_penalty_cards = self.htapi.find_cards(picked_cards, self.game_penalty_cards)
        
        if self.db['expose'] == True:
            score = len(my_heart_cards) * 2 * (-1)
        else:
            score = len(my_heart_cards) * (-1)
        
        if self.htapi.find_card(my_score_cards, Card('QS')) != None:
            score += -13
            
        if self.htapi.find_card(my_score_cards, Card('TC')) != None:
            score *= 2
            
        if len(self.htapi.find_cards(my_score_cards, my_penalty_cards)) == len(self.game_penalty_cards):
            # Shoot the moon. Score becomes postive! Score x 4! 
            score *= -1
            score *= 4
            ptup['shoot_moon'] = True
                
        ptup['score'] = score
        
    def game_round_end(self, round_num):
        """
        Decide round player, round player = the player "win" the round.
        """
        round_cards = self.db['roundCards']
        if len(round_cards) != 4:
            self.htapi.errmsg("Invalid cards of this round.")

        lead_card = round_cards[0]
        lead_ptup = self.player_tups[0]
        
        lead_card_suit = lead_card.get_suit_num()
        lead_card_rank = lead_card.get_rank_num()

        idx = 0
        rotate = 0
        next_lead_ptup = lead_ptup
        highest_rank = lead_card_rank
        for ptup in self.player_tups:
            if idx == 0:
                # This is lead player. Skip
                idx += 1
                continue         
            
            shoot_card = round_cards[idx]
            shoot_card_suit = shoot_card.get_suit_num()
            shoot_card_rank = shoot_card.get_rank_num()
            
            if shoot_card_suit == lead_card_suit:
                if shoot_card_rank > highest_rank:
                    next_lead_ptup = ptup
                    rotate = idx
                    highest_rank = shoot_card_rank
                    
            idx += 1
        
        # The cards belong to the next lead player. Give him the cards.
        next_lead_ptup['pick'] += round_cards
        next_lead_ptup['round_pick'] = round_cards
        
        """
        Calculate scores of this round and store the result.
        """
        for ptup in self.player_tups:
            self._recalculate_round_score(ptup)
             
        
        """
        Inform the user an event
        """
        for ptup in self.player_tups:
            self._ev_round_end(ptup, next_lead_ptup)
        
        """
        Rotate ptup position for next round.
        """
        if rotate > 0:
            self.player_tups_rotate(rotate)
            
    def show_score(self):
        for ptup in self.player_tups:
            self.htapi.dbg(
                "Player: " + ptup['name'] + 
                ", score: " + str(ptup['score']) + 
                ", score_accl: " + str(ptup['score_accl']) + 
                ", shoot_moon_accl: " + str(ptup['shoot_moon_accl'])
                )
       
    def game_round(self, round_num):
        """
        Play 1 round = 4 turn
        """
        self.htapi.dbg("Round: " + str(self.db['roundNumber']) + 
                       ", Deal: " + str(self.db['dealNumber']) + 
                       ", Game: " + str(self.db['gameNumber']))
        
        for ptup in self.player_tups:
            self.game_shoot1card(ptup)
            
        self.game_round_end(round_num)

    def game_finish_deal(self):
        """
        The end of a single deal.
        """
        for ptup in self.player_tups:
            ptup['score_accl'] += ptup['score']
            ptup['score_game'] += ptup['score']
            if ptup['shoot_moon'] == True:
                ptup['shoot_moon_accl'] += 1   
            
        # Inform players
        for ptup in self.player_tups:
            self._ev_deal_end(ptup)
    
    def game_expose_ah(self):
        for ptup in self.player_tups:
            hand_cards = ptup['hand']
            
            card_ah = self.htapi.find_card(hand_cards, Card('AH'))
            if card_ah != None:
                if self._ev_expose_ah(ptup):
                    # The player decides to expose, all heart score will double 
                    ptup['expose'] = True
                    self.db['expose'] = True   
                break
        
        # Inform players expose end.
        for ptup in self.player_tups:
            self._ev_expose_ah_end(ptup)
    
    def game_decide_lead_player(self):
        """
        Decide who must start the deal, i.e. the player has 2C.
        """        
        for i in range(0, 4):
            ptup = self.player_tups[0]
            
            card2c = self.htapi.find_card(ptup['hand'], Card('2C'))
            if card2c != None:
                break
            else:
                self.player_tups_rotate(1)
    
    def game_play1deal(self):
        """
        event: new_deal
        """
        self.game_new_deal()
        
        """
        event: receive_opponent_cards & pass_cards
        """
        self.game_pass3cards()
        
        self.game_decide_lead_player()
        
        """
        event: Ask if the player wants to expose AH
        """
        self.game_expose_ah()
        
        """
        event: your_turn & turn_end & expose_cards & expose_cards_end && round_end
        """
        for round in range(1, 14):
            # Round 1 to 13
            self.game_next_round()
            self.game_round(round)
            
        self.game_finish_deal()
        
    def game_next_game(self):
        self.db['gameNumber'] += 1
        self.db['dealNumber'] = 0
                
        for ptup in self.player_tups:
            # Reset game-specific data
            ptup['score_game'] = 0
            
    def game_over(self):
        """
        playerName, gameScore
        """
        for ptup in self.player_tups:
            self._ev_game_end(ptup)
            
    def game_single(self):
        """
        There're 16 deals in a game
        """
        self.game_next_game()
        
        # Inform the players there's a new game to start.
        for ptup in self.player_tups:
            self._ev_new_game(ptup)
        
        DEAL_PER_GAME = 16
        for deal in range(1, DEAL_PER_GAME + 1):
            self.game_next_deal()
            self.game_play1deal()
            
        self.game_over()

    def game_loop(self, loop_max=1):
        for loop in range(1, loop_max + 1):
            self.game_single()
            self.show_score()

def pseudo_contest():
    """
    Pseudo contest to play much more quickly than real contest mode.
    """
    from HacBot.HacBot import HacBot
    from SampleBot.SampleBot import SampleBot
#     from SelmonBot.selmon_bot import MCTSBot
    
    #
    # Decide game loops from argv[1]
    #
    if len(sys.argv) < 2:
        game_max = 4 
    else:
        game_max = int(sys.argv[1])
    
    #
    # If you feel the msg is to annoying, disable it in Htapi
    #
    mybot = HacBot('hac', is_debug=True)
    pseudo_player1 = SampleBot('bota')
    pseudo_player2 = SampleBot('botb')
    pseudo_player3 = SampleBot('botc')
    players = [mybot, pseudo_player1, pseudo_player2, pseudo_player3]

    #    
    # Start the game loop by specified bots.
    #
    hgame = PseudoHeart(players)
    hgame.game_loop(loop_max = game_max)

def unitest():
    htapi = Htapi()
    allcards = htapi.get52cards()
    random.shuffle(allcards)
    print (format(allcards))
    print (format(htapi.get_cards_by_suit(allcards, 'S')))
    print (format(htapi.find_card(allcards, Card('2H'))))
    
#     for c in allcards:
#         print(c, c.get_suit_num(), c.get_rank_num())
    

if __name__ == "__main__":
#     unitest()
    pseudo_contest()