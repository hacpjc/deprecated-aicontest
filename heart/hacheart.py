# coding=UTF-8

import os, sys, json

from PokerBot import Card, PokerBot, system_log

from websocket import create_connection
class PokerSocket(object):
    ws = ""

    def __init__(self, player_name, player_number, token, connect_url, poker_bot):
        self.player_name = player_name
        self.connect_url = connect_url
        self.player_number = player_number
        self.poker_bot = poker_bot
        self.token = token

    def event_dispatch(self, event, data):
        """
        Event dispatch! Call bot method.
        """
        if event == "new_deal":
            self.poker_bot.receive_cards(data)
        elif event == "new_game":
            self.poker_bot.new_game(data)
        elif event == "receive_opponent_cards":
            self.poker_bot.receive_opponent_cards(data)
        elif event == "pass_cards":
            pass_cards = self.poker_bot.pass_cards(data)
            self.ws.send(json.dumps(
                {
                    "eventName": "pass_my_cards",
                    "data": {
                        "dealNumber": data['dealNumber'],
                        "cards": pass_cards
                    }
                }))
        elif event == "your_turn":
            pick_card = self.poker_bot.pick_card(data)
            
            message = "Send message:{}".format(json.dumps(
                {
                   "eventName": "pick_card",
                   "data": {
                       "dealNumber": data['dealNumber'],
                       "roundNumber": data['roundNumber'],
                       "turnCard": pick_card
                   }
               }))
            system_log.show_message(message)
            system_log.save_logs(message)
            
            self.ws.send(json.dumps(
                {
                    "eventName": "pick_card",
                    "data": {
                        "dealNumber": data['dealNumber'],
                        "roundNumber": data['roundNumber'],
                        "turnCard": pick_card
                    }
                }))
        elif event == "turn_end":
            self.poker_bot.turn_end(data)
        elif event == "expose_cards":
            expose_cards = self.poker_bot.expose_my_cards(data)
            if expose_cards != None:
                self.ws.send(json.dumps(
                    {
                        "eventName": "expose_my_cards",
                        "data": {
                            "dealNumber": data['dealNumber'],
                            "cards": expose_cards
                        }
                    }))
        elif event == "expose_cards_end":
            self.poker_bot.expose_cards_end(data)
        elif event == "round_end":
            self.poker_bot.round_end(data)
        elif event == "deal_end":
            self.poker_bot.deal_end(data)
            self.poker_bot.reset_card_his()
        elif event == "game_end":
            self.poker_bot.game_over(data)
            self.ws.close()
            
    def event_loop(self):
        try:
            self.ws = create_connection(self.connect_url)
            self.ws.send(json.dumps({
                "eventName": "join",
                "data": {
                    "playerNumber":self.player_number,
                    "playerName":self.player_name,
                    "token":self.token
                }
            }))
            while 1:
                result = self.ws.recv()
                msg = json.loads(result)
                
                event_name = msg["eventName"]
                data = msg["data"]
                
                system_log.show_message(event_name)
                system_log.save_logs(event_name)
                system_log.show_message(data)
                system_log.save_logs(data)
                
                self.event_dispatch(event_name, data)
        except Exception, e:
            system_log.show_message(e)
            system_log.save_logs(e)
            self.event_loop()


def real_contest():
    """
    Real contest. Boom!
    """
    argv_count = len(sys.argv)
    if argv_count > 2:
        player_name = sys.argv[1]
        player_number = sys.argv[2]
        token = sys.argv[3]
        connect_url = sys.argv[4]
    else:
        player_name = "hacII"
        player_number = 99
        token = "12345678"
        connect_url = "ws://localhost:8080/"
    
    print("Real contest mode, name: ", player_name, "num: ", player_number, "token: ", token, "url: ", connect_url)

    # Change this into developed bot
    from HacBot.HacBotIII import HacBotIII
    mybot = HacBotIII(player_name, is_debug=True)
    
    myPokerSocket = PokerSocket(player_name, player_number, token, connect_url, mybot)
    myPokerSocket.event_loop()

if __name__ == "__main__":
    real_contest()
