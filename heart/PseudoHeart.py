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

class PseudoHeart(Htapi):
    """
    Create a virtual game which can play faster!
    """
    def __init__(self, player_bots):
        if len(player_bots) != 4:
            print ("Invalid player num != 4")
            sys.exit()
            
        self.htapi = Htapi()
        
        # Save bot object into self.player_bots 
        self.player_tups = []
        for p in player_bots:
            player_tup = {'bot': p, 'name': p.get_name(),
                            'hand': [], 'pick': [], 'shoot': [],
                            'score': 0, 'score_accl': 0, 'shoot_moon': [],
                            }
            self.player_tups.append(player_tup)
            print ("...Add new player: " + player_tup['name'])

        self.db = {}            
        self.game_reset()
        
    def player_tups_rotate(self, shift=1):
        """
        Shift order of the players.
        """
        for i in range(shift):
            p = self.player_tups.pop(0)
            self.player_tups.append(p)
        
    def game_reset(self):
        self.db['dealNumber'] = 1
        self.db['gameNumber'] = 1

    def _ev_receive_cards(self, ptup):
            """
            Event: receive_cards
            
            data = {"players": [{"playerName": "hac", "cards": ["3S", "8S", "9S", "TS", "JS", "4H", "6H", "9H", "3D", "7D", "9D", "JD", "8C"], "dealNumber": 1, "gameNumber": 1}]}
            """
            data = {
                    'players': [
                        {
                            'playerName': ptup['name'],
                            'cards': [x.toString() for x in ptup['hand']],
                            
                            'gameNumber': self.db['gameNumber'],
                            'dealNumber': self.db['dealNumber'],
                        },
                        {
                            'playerName': 'self',
                            'cards': [x.toString() for x in ptup['hand']],
                            
                            'gameNumber': self.db['gameNumber'],
                            'dealNumber': self.db['dealNumber'],
                        },
                        # TBD: Add other players' data? Not necessary, I guess.
                    ]
                }
            self.htapi.msg(json.dumps(data))

            # Call player method.            
            pbot = ptup['bot']
            pbot.receive_cards(data)

    def _ev_pass3cards(self, ptup):
        """
        Output: picked 3 cards
        """
        
        self.htapi.msg("Ask player: " + ptup['name'] + " to pick 3 cards")
        
        data = {}
        data['self'] = {
            'cards': [x.toString() for x in ptup['hand']]
            }
        
        pbot = ptup['bot']
        picked = pbot.pass_cards(data)
        
        if picked == None or len(picked) != 3:
            self.htapi.errmsg("Invalid picked num of bot: " + ptup['name'])
        
        # Convert ['XX', 'OO', 'AA'] into Card list
        picked = [Card(c) for c in picked]
            
        # Check picked cards are really in list to keep away from stupid bot.
        found_cards = self.htapi.find_cards(ptup['hand'], picked)
        if found_cards == None or len(found_cards) != 3:
            self.htapi.errmsg("Player: " + ptup['name'] + " attemps to pick invalid cards")
        
        self.htapi.msg("Player: " + ptup['name'] + ", picked: ", format(picked))
        
        return picked

    def _ev_receive_opponent_cards(self, ptup, picked, received):
        """
        Pass 3 cards to the player
        """
        print (ptup['hand'])
        data = {
                'players': [
                    {
                        'playerName': ptup['name'],
                        'cards': [x.toString() for x in ptup['hand']],
                        'pickedCards': [x.toString() for x in picked],
                        'receivedCards': [x.toString() for x in received],
                        
                        'gameNumber': self.db['gameNumber'],
                        'dealNumber': self.db['dealNumber'],
                    },
                    {
                        'playerName': 'self',
                        'cards': [x.toString() for x in ptup['hand']],
                        'pickedCards': [x.toString() for x in picked],
                        'receivedCards': [x.toString() for x in received],
                        
                        'gameNumber': self.db['gameNumber'],
                        'dealNumber': self.db['dealNumber'],
                    },
                    # TBD: Add other players' data? Not necessary, I guess.
                ]
            }
        
        print (data)
        pbot = ptup['bot']
        pbot.receive_opponent_cards(data)

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
            picked = self.htapi.arrange_cards(picked)
            ptup['hand'] = picked
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
            
            self.msg("Player: " + ptup['name'] + ": " + format(picked[ptup['name']]) + ", -> " + format(card2pass[ptup['name']]))
          
            # Then inform the player            
            self._ev_receive_opponent_cards(ptup, picked[ptup['name']], card2pass[ptup['name']])
            
        
    def game_start(self):
        """
        event: new_deal
        """
        self.game_new_deal()
        
        """
        event: receive_opponent_cards & pass_cards
        """
        self.game_pass3cards()
        
        """
        event: your_turn & turn_end & expose_cards & expose_cards_end && round_end
        """
        

    def game_loop(self, loop_max=1):
        for loop in range(1, loop_max + 1):
            self.game_start()

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
    print (format(allcards))
    print (format(htapi.get_cards_by_suit(allcards, 'S')))
    print (format(htapi.find_card(allcards, Card('2H'))))
    
    c = htapi.remove_card(allcards, Card('2H'))
    print (c)
    

if __name__ == "__main__":
    unitest()
    pseudo_contest()