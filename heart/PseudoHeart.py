# coding=UTF-8
import os, sys, json, random
from PokerBot import Card, system_log
from HacBot import HacBot

class Htapi():
    
    def __init__(self):
        from uptime import uptime
        random.seed(int(uptime()))

    def logdict(self, dict):
        """
        Output log to stdout by a python dict input
        TODO: Write to a file, maybe?
        """
        print(format(dict))
        sys.stdout.flush()

    # Debug tool - Print a list of string(s)
    def msg(self, *argv):
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
    
    def shuffle_cards(self, card_list):
        random.shuffle(card_list)
        return card_list
    
    def clone_cards(self, cards):
        output = cards[:]
        return output
        

class PseudoHeart(Htapi):
    """
    Create a virtual game which can play faster!
    """
    game_score_cards = {Card("QS"), Card("TC"),
                        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
                        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
                        Card("QH"), Card("KH"), Card("AH")}
    
    # If have all penalty cards, the player shoots the moon and win a lot.
    game_penalty_cards = {Card("QS"),
                        Card("2H"), Card("3H"), Card("4H"), Card("5H"), Card("6H"), 
                        Card("7H"), Card("8H"), Card("9H"), Card("TH"), Card("JH"), 
                        Card("QH"), Card("KH"), Card("AH")}
    
    def __init__(self, player_bots):
        if len(player_bots) != 4:
            print ("Invalid player num != 4")
            sys.exit()
    
        self.db = {}  
        self.htapi = Htapi()
        self.game_heart_cards = self.htapi.get_cards_by_suit(self.htapi.get52cards(), 'H')
        
        # Save bot object into self.player_bots 
        self.player_tups = []
        for p in player_bots:
            player_tup = {'bot': p, 'name': p.get_name(),
                            'hand': [], 'pick': [], 'round_pick': [], 'shoot': [], 'expose': False,
                            'score': 0, 'score_accl': 0, 'shoot_moon': False,
                            }
            self.player_tups.append(player_tup)
            print ("...Add new player: " + player_tup['name'])
        
        # Decide next lead player
        self.db['next_lead_ptup'] = self.player_tups[1]
          
        self.game_reset()
        
    def player_tups_rotate(self, shift=1):
        """
        Shift order of the players.
        """
        for i in range(shift):
            p = self.player_tups.pop(0)
            self.player_tups.append(p)
        
    def game_reset(self):
        self.db['dealNumber'] = 0
        self.db['gameNumber'] = 0
        
    def game_next_deal(self):
        self.db['dealNumber'] += 1
        self.db['heartBreak'] = False
        self.db['expose'] = False
        self.db['unusedCards'] = self.htapi.get52cards()
        self.db['usedCards'] = []
        
        self.db['roundNumber'] = 0
        
        for ptup in self.player_tups:
            ptup['pick'] = []
            ptup['hand'] = []
            ptup['shoot'] = []
            ptup['score'] = 0
            ptup['shoot_moon'] = False
            
        # Re-arrange position
        next_lead_ptup = self.db['next_lead_ptup']
        for i in range(0, 4):
            ctup = self.player_tups[0]
            if ctup['name'] == next_lead_ptup['name']:
                # The player's at position 0, so he will be the lead player.
                break
            else:
                self.player_tups_rotate(1)
            
        #  Now decide the next lead player
        self.db['next_lead_ptup'] = self.player_tups[1]
        
    def game_next_round(self):
        self.db['roundNumber'] += 1
        self.db['roundCards'] = []
        
        for ptup in self.player_tups:
            ptup['round_pick'] = []

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
        pass

    def _ev_pass3cards(self, ptup):
        """
        Output: picked 3 cards
        """
        data = {}
        data['self'] = {
            'cards': self.htapi.clone_cards([x.toString() for x in ptup['hand']])
            }
        
        print(data)
        
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
        data = self.htapi.clone_cards(ptup['hand'])
                                      
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

    def _ev_round_end(self, ptup):
        """
        Inform the user the end of a round
        """
        data = {'roundPlayers': []}
        data_round_players = data['roundPlayers']
        
        for ptup_this in self.player_tups:
            data_round_players.append(ptup_this['name'])
        
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
                data_players.append(another_data_this)

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

    def game_new_deal(self):
        """
        Deliver 13 cards to each player
        """
        unused_card = self.htapi.get52cards()
        unused_card = self.htapi.shuffle_cards(unused_card)
        
        if len(self.player_tups) != 4:
            self.htapi.errmsg("Invalid player bot num")
        
        for ptup in self.player_tups:
            picked = []
            for i in range(13):
                picked.append(unused_card.pop())
            
            # The player get 13 cards. Generate event: 'receive_cards'
            self.htapi.arrange_cards(picked)
            ptup['hand'] = picked
            self._ev_receive_cards(ptup)
            self.msg("Deliver cards to " + ptup['name'], format(ptup['hand']))
        
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
            self._ev_receive_opponent_cards(ptup, picked[ptup['name']], card2pass[ptup['name']])
            self.msg("Pass 3 cards to player " + ptup['name'], format(card2pass[ptup['name']]))

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
        
    def game_shoot1card(self, ptup):
        """
        Make the player shoot 1 card!
        """
        candidates = self._get_candidates(ptup)
        self.htapi.arrange_cards(candidates)
        candidates = self.htapi.clone_cards(candidates)
        
        print ("Player " + ptup['name'] + " candidate cards: ", candidates)
        
        data = {'self': {
                        'cards': [x.toString() for x in ptup['hand']],
                        'candidateCards': [x.toString() for x in candidates],
                        
                        'gameNumber': self.db['gameNumber'],
                        'dealNumber': self.db['dealNumber'],
                    }}
        
        pbot = ptup['bot']
        card2shoot = pbot.pick_card(data)
        card2shoot = Card(card2shoot)
        if self.htapi.find_card(ptup['hand'], card2shoot) == None:
            self.errmsg("Cannot shoot un-existed card at player: " + ptup['name'])
            
        print ("Player shoots: ", card2shoot, self.db['unusedCards'], ptup['hand'])
        
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
                    print ("player " + ptup['name'] + " is temporarily win.")
                    
            idx += 1
        
        # The cards belong to the next lead player. Give him the cards.
        next_lead_ptup['pick'] += round_cards
        next_lead_ptup['round_pick'] = round_cards
        
        if rotate > 0:
            self.player_tups_rotate(rotate)
        
        """
        Calculate scores of this round and store the result.
        """
        for ptup in self.player_tups:
            self._recalculate_round_score(ptup)
        
        """
        Inform the user an event
        """
        for ptup in self.player_tups:
            self._ev_round_end(ptup)
            
       
    def game_round(self, round_num):
        """
        Play 1 round = 4 turn
        """
        print("")
        print("Round: " + str(round_num))
        for ptup in self.player_tups:
            self.game_shoot1card(ptup)
            
        self.game_round_end(round_num)

    def game_finish_deal(self):
        """
        The end of a single game.
        """
        for ptup in self.player_tups:
            ptup['score_accl'] += ptup['score']
    
    def game_expose_ah(self):
        for ptup in self.player_tups:
            hand_cards = ptup['hand']
            
            card_ah = self.htapi.find_card(hand_cards, Card('AH'))
            if card_ah != None:
                if self._ev_expose_ah(ptup):
                    # The player decides to expose, all heart score will double 
                    ptup['expose'] = True
                    self.db['expose'] = True   
                    self.htapi.msg("Player " + ptup['name'] + " exposed AH")             
                break
        
        # Inform players expose end.
        for ptup in self.player_tups:
            self._ev_expose_ah_end(ptup)
        
    def game_play1deal(self):
        """
        event: new_deal
        """
        self.game_new_deal()
        
        """
        event: receive_opponent_cards & pass_cards
        """
        self.game_pass3cards()
        
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
        
        DEAL_PER_GAME = 16
        for deal in range(1, DEAL_PER_GAME + 1):
            self.game_next_deal()
            self.game_play1deal()
            
        self.game_over()

    def game_loop(self, loop_max=1):
        for loop in range(1, loop_max + 1):
            self.game_single()

def pseudo_contest():
    """
    Pseudo contest to play much more quickly than real contest mode.
    """
    mybot = HacBot('hac')
    pseudo_player1 = HacBot('bota')
    pseudo_player2 = HacBot('botb')
    pseudo_player3 = HacBot('botc')
    players = [mybot, pseudo_player1, pseudo_player2, pseudo_player3]
    
    hgame = PseudoHeart(players)
    
    hgame.game_loop(loop_max = 1)

def unitest():
    htapi = Htapi()
    allcards = htapi.get52cards()
#     print (format(allcards))
#     print (format(htapi.get_cards_by_suit(allcards, 'S')))
#     print (format(htapi.find_card(allcards, Card('2H'))))
    
    for c in allcards:
        print(c, c.get_suit_num(), c.get_rank_num())
    

if __name__ == "__main__":
#     unitest()
    pseudo_contest()