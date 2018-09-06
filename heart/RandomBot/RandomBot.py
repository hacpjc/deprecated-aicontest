
from PokerBot import PokerBot, system_log, Card, Htapi

class RandomBot(PokerBot, Htapi):
    """
    Random bot. Life is luck. Life is random. Life is life.
    """
    def __init__(self, name, is_debug=False):
        super(RandomBot, self).__init__(name)

        self.htapi = Htapi(is_debug=is_debug)
        
        self.stat = {}
    
    def new_game(self, data):
        """
        Event: The start of a new game.
        """
        pass
            
    def receive_cards(self, data):
        """
        Event: Receive my 13 cards.
        """
        self.stat['hand'] = self.get_cards(data)
        
    def pass_cards(self, data):
        """
        Event: Pick 3 cards to pass to others
        """
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        
        output = []
        my_hand_cards = self.htapi.shuffle_cards(my_hand_cards)
        output.append(my_hand_cards.pop(0))
        output.append(my_hand_cards.pop(0))
        output.append(my_hand_cards.pop(0))
        
        output = [x.toString() for x in output]
            
        self.htapi.dbg(self.get_name() + " Pass 3 cards: " + format(output))
        return output

    def receive_opponent_cards(self, data):
        """
        Event: Recv 3 cards from one opponent
        """
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
        
        output = ['AH']
        return output

    def expose_cards_end(self, data):
        """
        Event: Check if somebody expose AH. Damn. 
        """
        pass
        
    def pick_card(self, data):
        """
        Event: My turn to shoot a card.
        """
        # roundPlayers is in the correct order of shooting cards.
        round_players = data['roundPlayers']
        
        # Identify my position in this round
        my_pos = round_players.index(self.get_name())

        # Get players in next turn.
        self.stat['nextPlayers'] = data['roundPlayers'][(my_pos + 1):]
        
        self.stat['hand'] = [Card(x) for x in data['self']['cards']]
        my_hand_cards = self.stat['hand']
        my_avail_cards = [Card(x) for x in data['self']['candidateCards']]    
        
        my_avail_cards = self.htapi.shuffle_cards(my_avail_cards)
        
        card2shoot = my_avail_cards[0]
        
        return card2shoot.toString()
    
    def turn_end(self, data):
        """
        Event: turn end
        """
        pass
                
    def pick_history(self, data, is_timeout, pick_his):
        """
        Event: turn end
        """
        self.turn_end(data)
    
    def round_end(self, data):
        """
        Event: round end
        """
        pass
    
    def deal_end(self, data):
        """
        Event: deal end
        """
        pass
    
    def game_over(self, data):
        """
        Event: game end
        """
        pass
