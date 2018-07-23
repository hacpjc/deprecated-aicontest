from deuces import Card, Evaluator

from websocket import create_connection
import math
import random
import json
import numpy as np
import sys, traceback

# OK;
def roundup(x, to):
    return int(math.floor(x / 10.0)) * 10

# OK; Input 'AH' -> Ouptut: 'Ah'
def convert_card_str(card_str):
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
        print ("Invalid input: ", card_str)

    return "".join(card_str_list)

# OK; Output: ['2s', '3s', '4s', '5s', '6s' ... 'Tc', 'Jc', 'Qc', 'Kc', 'Ac' ]
def get_all_cardstr():
    tbl= []
    suit = ['s', 'h', 'd', 'c']
    rank = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    
    for s in suit:
        for r in rank:
            tbl.append("".join(r + s))
    return tbl

# OK; Output: [Card.new('2s'), ...]
def get_all_card():
    output = []
    tbl = get_all_cardstr()
    
    for c in tbl:
        output.append(Card.new(c))
        
    return output


# OK; Output: [ ['playerName' => v, 'chips' => ...], [...]]
def rebuild_player_table(players_json):
    tbl = []
    for p in players_json:
        this = [
                {'playerName': p['playerName'], 
                 'chips': p['chips'],
                 'action': [],
                 'alive': p['isSurvive']
                 }
                ]
        tbl.append(this)
    print (tbl)
    return tbl

# OK;
def get_hole_power(hole):  
    ha = Card.get_rank_int(hole[0])
    hb = Card.get_rank_int(hole[1])
    
    power = ha + hb

    if Card.get_suit_int(hole[0]) == Card.get_suit_int(hole[1]):
        power += 25
            
    if ha == hb:
        power += 50
        
    if ha >= 8:
        power += ha * 3
        
    if hb >= 8:
        power += hb * 3

    if power >= 100:
        power = 100

    return power

# OK;
# OK;
def calc_mont_win_rate(holes, boards, max_sample):
    global my_evaluator
    i = 0
    
    mypow = my_evaluator.evaluate(boards, holes)
    
    alltbl = get_all_card()
    unused_tbl = []
    
    used = holes + boards

    unused_tbl = [x for x in alltbl if not x in used]
    
    win_cnt = 0
    while i < max_sample:
        i += 1
        ohole = random.sample(unused_tbl, 2)
        opow = my_evaluator.evaluate(boards, ohole)
        if (mypow < opow):
            win_cnt += 1
    
    return 100 * (win_cnt / float(max_sample))

# OK;
def get_my_power(holes, boards, my_chips, my_call_bet, playernum):
    global my_evaluator
    
    # Normalize power to 0 ~ 100
    mypow = my_evaluator.evaluate(boards, holes)
    mypow = (7642 - mypow) / float(7641)
    mypow = mypow * 100
    
    win_rate = calc_mont_win_rate(holes, boards, 30000)
    percent = win_rate / 100
    
    win_rate = math.pow(percent, playernum - 1) * 100
    
    print ("...pow / rate", mypow, win_rate, "user", playernum)
    mypow = ((mypow * 5) + win_rate) / float(6)
    print ("...mypow", mypow)
    
    # Decrease power if chips is in danger, Increase power if chips is a lot
    rate = my_call_bet / float(my_call_bet + my_chips)
    rate = 1 - rate
    rate = rate * 100
    
    mypow = ((mypow * 9) + rate) / float(10)
    
    print ("...my power is: ", mypow)
    return mypow
    
# OK;
def get_random_hit(hitrate):
    obj = random.SystemRandom()
    num = obj.randrange(0, 100, 1) 
    if num <= hitrate:
        return True
    else:
        return False
    
# OK;
def may_i_raise(my_power, my_raise_bet, my_chips):
    if my_power < random.randrange(65, 75):
        return False
    
    # Can win! Try to raise if we have money
    if my_raise_bet < (my_chips / 2):
        return True
    else:
        return False

def may_i_call_at_flop(my_power, my_call_bet, my_chips):
    if my_power < random.randrange(5, 10):
        return False
    
    if my_power >= random.randrange(5, 25):
        return True
    else:
        return False
    
def may_i_call_at_turn(my_power, my_call_bet, my_chips):
    if (my_chips < 100):
        return True
    
    if my_power < random.randrange(15, 25):
        return False
    
    if my_power >= random.randrange(30, 40):
        return True
    else:
        return False

def may_i_call_at_river(my_power, my_call_bet, my_chips, my_spend):
    print("reiver spend: ", my_spend)
    
    if (my_chips < 100):
        return True
    
    if (my_call_bet + my_spend) / float(my_call_bet + my_spend + my_chips) >= 0.5:
        return True
    
    if my_power < random.randrange(25, 35):
        return False
    
    return True

# OK; For preflop to decide to gamble or not.
def may_i_call_at_preflop(my_hole, my_chips, my_call_bet):
    #
    # If I have a lot of chips, raise the gamble rate!
    #
    basic_rate = my_call_bet / float(my_chips + my_call_bet)
    basic_rate = 1 - basic_rate
    basic_rate = basic_rate * 100
    
    my_hole_power = get_hole_power(my_hole)
    
    gamble_rate = ((basic_rate * 4) + my_hole_power) / 5
    
    print("...gamble rate: ", gamble_rate)
    return get_random_hit(gamble_rate)


class PokerSocket(object):
    ws = ""
    board = []
    hole = []
    my_raise_bet = 0
    my_call_bet = 0
    number_players = 0
    my_chips = 0
    table_bet = 0
    my_name = None
    raise_count = 0
    bet_count = 0
    total_bet = 0
    player_table = []
    
    my_chips_in_round = 0
    
    def __init__(self,my_name,connect_url, pokerbot):
        self.pokerbot = pokerbot
        self.my_name = my_name
        self.connect_url = connect_url

    def next_round_action(self):
        self.bet_count = 0
        self.raise_count = 0
        self.total_bet = 0

    def getAction(self, data):
        roundnum = data['game']['roundName']
        players = data['game']['players']
        chips = data['self']['chips']
        hands = data['self']['cards']

        self.raise_count = data['game']['raiseCount']
        self.bet_count = data['game']['betCount']
        self.my_chips = chips
        self.my_name = data['self']['playerName']

        self.number_players = len(players)
        self.my_call_bet = data['self']['minBet']
        self.my_raise_bet = roundup(chips / 4, self.my_call_bet)
        
        self.hole = []
        for card in (hands):
            card = convert_card_str(card)
            card = Card.new(card)
            self.hole.append(card)
        
        print ("...roundnum: ", format(roundnum))
        print ('...my_call_bet:', format(self.my_call_bet), "my_raise_bet", format(self.my_raise_bet), "my_chips", format(self.my_chips), "table bet", format(self.table_bet))
        
        Card.print_pretty_cards (self.hole)
        Card.print_pretty_cards (self.board)

        action, amount = self.pokerbot.declareAction(
                self.hole, self.board, roundnum, self.my_raise_bet, self.my_call_bet, self.table_bet, 
                self.number_players, self.raise_count, self.bet_count, self.my_chips, self.total_bet)
        
        self.total_bet += amount
        
        if action == 'raise':
            self.raise_count += 1
        elif action == 'call':
            self.bet_count += 1
        
        return action, amount

    def takeAction(self, event_name, data):
        print ("...dispatch event: ", event_name)
        
        if event_name == '__new_round':
            self.player_table = rebuild_player_table(data['players'])
        
        if event_name == "__show_action" or event_name == '__deal' :
            table = data['table']
            players = data['players']
            boards = table['board']
            self.number_players = len(players)
            self.table_bet = table['totalBet']
            self.board = []
            for card in (boards):
                card = convert_card_str(card)
                card = Card.new(card)
                self.board.append(card)
            print ('...number_players: ', format(self.number_players))
            if len(self.board) > 0:
                Card.print_pretty_cards(self.board)
            else:
                print ("...board empty (preflop)")
                
            print ('...total_bet: ', format(self.table_bet))
        elif event_name == "__bet":
            action, amount = self.getAction(data)
            print ("...action: ", format(action))
            print ("...action amount: ", format(amount))
            
            output_msg = json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.my_name,
                    "amount": amount
                }})
            self.ws.send(output_msg)
        elif event_name == "__action":
            action, amount = self.getAction(data)
            print ("...action: ", format(action), "amount: ", format(amount))

            output_msg = json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.my_name,
                    "amount": amount
                }})
            self.ws.send(output_msg)
        elif event_name == "__game_over":
            print("...table end w/ my chips: ", self.my_chips)
            sys.exit()
        elif event_name == "__round_end":           
            players = data['players']
            is_winner = False
            my_win_chips = 0
            for player in players:
                winMoney = player['winMoney']
                playerid = player['playerName']
                if (self.my_name == playerid):
                    if (winMoney == 0):
                        is_winner = False
                    else:
                        is_winner = True
                    my_win_chips = winMoney
                    
            print ("...winPlayer:", format(is_winner), "winChips:", format(my_win_chips))
            self.pokerbot.game_over(is_winner, my_win_chips, data)
            self.next_round_action()
        else:
            print ("...skip event: ", event_name)

    def doListen(self):
        try:
            self.ws = create_connection(self.connect_url)
            
            print("...Join game")
            self.ws.send(json.dumps({
                "eventName": "__join",
                "data": {
                    "playerName": self.my_name
                }
            }))
    
            print ("...start event loop")
            while 1:
                result = self.ws.recv()
                print ("")
                
                msg = json.loads(result)
                
                event_name = msg["eventName"]
                data = msg["data"]
#                print ("->", event_name, ":", json.dumps(data))
                self.takeAction(event_name, data)
        except Exception, e:
            print (" * EXCEPTION: ", e.message)
            traceback.print_exc(file=sys.stdout)
            sys.exit()
            

class PokerBot(object):
    def declareAction(self,hole, board, round, my_Raise_Bet, my_Call_Bet,Table_Bet,number_players,raise_count,bet_count,my_Chips,total_bet):
        err_msg = self.__build_err_msg("declare_action")
        raise NotImplementedError(err_msg)
    def game_over(self,isWin,winChips,data):
        err_msg = self.__build_err_msg("game_over")
        raise NotImplementedError(err_msg)

class my_battle_poker_bot(PokerBot):   
    raise_count = 0
    bet_count = 0
    spend_money = 0
    
    def __init__(self):
        pass

    def game_over(self, is_winner, my_win_chips, data):
        # Round end
        self.bet_count = 0
        self.raise_count = 0
        self.spend_money = 0
        print ("...round over: ", is_winner, my_win_chips, "spend: ", self.spend_money, "counter: ", self.bet_count, "/", self.raise_count)
    
    def do_preflop(self, holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet):      
        #
        # Don't bet too much at preflop. always: call or fold.
        #
        if may_i_call_at_preflop(holes, my_chips, my_call_bet):
            self.spend_money += my_call_bet
            return 'call', my_call_bet
        else:
            return 'fold', 0

    def do_flop(self, holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet):

        my_power = get_my_power(holes, boards, my_chips, my_call_bet, number_players)
        if may_i_raise(my_power, my_raise_bet, my_chips):
            self.raise_count += 1
            self.spend_money += my_raise_bet
            return 'raise', my_raise_bet
        elif may_i_call_at_flop(my_power, my_call_bet, my_chips):
            self.bet_count += 1
            self.spend_money += my_call_bet
            return 'call', my_call_bet
        else:
            return 'fold', 0

    def do_turn(self, holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet):
        my_power = get_my_power(holes, boards, my_chips, my_call_bet, number_players)
        
        if may_i_raise(my_power, my_raise_bet, my_chips):
            self.raise_count += 1
            self.spend_money += my_raise_bet
            return 'raise', my_raise_bet
        elif may_i_call_at_turn(my_power, my_call_bet, my_chips):
            self.bet_count += 1
            self.spend_money += my_call_bet
            return 'call', my_call_bet
        else:
            return 'fold', 0

    def do_river(self, holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet):
        my_power = get_my_power(holes, boards, my_chips, my_call_bet, number_players)
        
        if may_i_raise(my_power, my_raise_bet, my_chips):
            self.raise_count += 1
            self.spend_money += my_raise_bet
            return 'raise', my_raise_bet
        elif may_i_call_at_river(my_power, my_call_bet, my_chips, self.spend_money):
            self.bet_count += 1
            self.spend_money += my_call_bet
            return 'call', my_call_bet
        else:
            return 'fold', 0

    def declareAction(self, holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet):       
        # preflop -> Flop -> Turn -> River
        if roundnum == 'Deal':
            return self.do_preflop(holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet)
        elif roundnum == 'Flop':
            return self.do_flop(holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet)
        elif roundnum == 'Turn':
            return self.do_flop(holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet)
        elif roundnum == 'River':
            return self.do_flop(holes, boards, roundnum, my_raise_bet, my_call_bet, table_bet, number_players, raise_count, bet_count, my_chips, total_bet) 
        else:
            print ("BUG: Do not expect ", roundnum)
            sys.exit()
            
if __name__ == '__main__':
        if len(sys.argv) == 3: 
            name = sys.argv[1] 
        else: 
            print (sys.argv[0], " <name> <url>") 
            print (sys.argv[0], " <name> ws://poker-dev.wrs.club:3001/ ws://poker-training.vtr.trendnet.org:3001 ws://poker-battle.vtr.trendnet.org:3001") 
            sys.exit() 
     
        if len(sys.argv) == 3: 
            connect_url = sys.argv[2] 
        else: 
            print (format(sys.argv[0]), " <name> <url>") 
            sys.exit()

        print ("...Start game with name: ", name, "url: ", connect_url)

        my_name=name
        print ("...name: {}".format(my_name), "url: {}".format(connect_url))

        my_evaluator = Evaluator()
        myPokerBot = my_battle_poker_bot()

        myPokerSocket = PokerSocket(my_name, connect_url, myPokerBot)
        myPokerSocket.doListen()
