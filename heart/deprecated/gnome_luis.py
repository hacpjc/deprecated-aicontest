from deuces import Card
import sys
import random

from htapi import htapi, htplayer, htgame

class ai_louis(htapi):
	ht = htapi();

	def __init__(self):
		pass

	def deal(self, data):
		"""
		got initial 13 cards
		"""

		my_unused_cards = data['player_unused_card']
		self.ht.msg("gnome_luis card before exchange: {}".format(self.ht.get_card_pretty_list(my_unused_cards)))

	def time2pass(self, data):
		"""
		select 3 cards to pass, no '2c'
		"""

		output = []
		my_all_card = data['unused_card']
		my_avail_card = data['avail_card'][:]

		if self.ht.str2card('Qs', fixfmt = False) in my_avail_card:
			output.append(self.ht.str2card('Qs', fixfmt = False))
			my_avail_card.remove(self.ht.str2card('Qs', fixfmt = False))

		if self.ht.str2card('Ks', fixfmt = False) in my_avail_card:
			output.append(self.ht.str2card('Ks', fixfmt = False))
			my_avail_card.remove(self.ht.str2card('Ks', fixfmt = False))

		if self.ht.str2card('As', fixfmt = False) in my_avail_card:
			output.append(self.ht.str2card('As', fixfmt = False))
			my_avail_card.remove(self.ht.str2card('As', fixfmt = False))

		club_suit = self.ht.str2suit('Club')
		diamond_suit = self.ht.str2suit('Diamond')
		heart_suit = self.ht.str2suit('Heart')
		while len(output) < 3:
			club_list = self.ht.card_select_by_suit(club_suit, my_avail_card)
			diamond_list = self.ht.card_select_by_suit(diamond_suit, my_avail_card)
			heart_list = self.ht.card_select_by_suit(heart_suit, my_avail_card)

			if len(club_list) == 1:
				card = club_list[0]
			elif len(diamond_list) == 1:
				card = diamond_list[0]
			elif len(heart_list):
				card = heart_list.pop()
			else:
				card = my_avail_card[0]

			output.append(card)
			my_avail_card.remove(card)

		return output

	def __open_trick(self, data):
		# If I have only hearts, play the lowest
		heart_suit = self.ht.str2suit('Heart')
		heart_list = self.ht.card_select_by_suit(heart_suit, self.my_unused_card)
		if len(self.my_unused_card) == len(heart_list):
			return self.my_avail_card[0]

		# If I have the two of clubs, play it
		# FIXME: This should honor the clubs_lead = false rule
		if self.ht.str2card('2c', fixfmt = False) in self.my_unused_card:
			return self.ht.str2card('2c', fixfmt = False)

		# If I don't have the queen of spades or higher and the queen hasn't been played, open with high spades
		spade_suit = self.ht.str2suit('Spade')
		spade_list = self.ht.card_select_by_suit(spade_suit, self.my_unused_card)
		queen_played = 0
		if self.ht.str2card('Qs', fixfmt = False) in self.all_used_card:
			queen_played = 1

		if len(spade_list) and queen_played == 0 and (not self.ht.str2card('Qs', fixfmt = False) in spade_list) and (not self.ht.str2card('Ks', fixfmt = False) in spade_list) and (not self.ht.str2card('As', fixfmt = False) in spade_list):
			return spade_list[-1]

		# Try playing a suit that hasn't been played much
		diamond_suit = self.ht.str2suit('Diamond')
		diamond_list = self.ht.card_select_by_suit(diamond_suit, self.my_unused_card)
		diamond_played = self.ht.calc_card_num_by_suit(diamond_suit, self.all_used_card)
		if len(diamond_list) and diamond_played < 2:
			return diamond_list[0]

		club_suit = self.ht.str2suit('Club')
		club_list = self.ht.card_select_by_suit(club_suit, self.my_unused_card)
		club_played = self.ht.calc_card_num_by_suit(club_suit, self.all_used_card)
		if len(club_list) and club_played < 2:
			return club_list[0]

		# A low hearts to give them trouble
		heart_played = self.ht.calc_card_num_by_suit(heart_suit, self.all_used_card)
		if self.is_hb and len(heart_list):
			max_heart = 2 + ((heart_played + 1) * 3)
			if self.ht.get_card_rank(heart_list[0]) < max_heart:
				return heart_list[0]

		# Find a good card based on scores
		# TODO

		# Give up. Play random
		return random.choice(self.my_unused_card)

	def __follow_suit(self, data):
		# Play spades
		lead_card = self.all_board_card[0]
		lead_suit = self.ht.get_card_suit(lead_card)

		# suit num: Spade=1, Heart=2, Diamond=4, Club=8
		if lead_suit == 1:
			spade_suit = self.ht.str2suit('Spade')
			spade_list = self.ht.card_select_by_suit(spade_suit, self.my_unused_card)
			# Uh oh, I have the queen
			if self.ht.str2card('Qs', fixfmt = False) in spade_list:
				# See if I can dump the queen
				if self.ht.str2card('Ks', fixfmt = False) in self.all_board_card or self.ht.str2card('As', fixfmt = False) in self.all_board_card:
					return self.ht.str2card('Qs', fixfmt = False)

				# Try playing something else but the queen
				if spade_list[-1] == self.ht.str2card('Qs', fixfmt = False):
					# return the highest card. Could be the queen if that's all we have.
					return spade_list[0]

				return spade_list[-1]

			# I don't have the queen
			if self.ht.str2card('Ks', fixfmt = False) in spade_list or self.ht.str2card('As', fixfmt = False) in spade_list:
				if len(self.all_board_card) == 3 and not self.ht.str2card('Qs', fixfmt = False) in self.all_board_card:
					return spade_list[-1]

				if spade_list[0] == self.ht.str2card('Ks', fixfmt = False) or spade_list[0] == self.ht.str2card('As', fixfmt = False):
					# Forced to play high spades
					return spade_list[0]

				return spade_list[-1]

			return spade_list[-1]

		# Play hearts
		if lead_suit == 2:
			heart_suit = self.ht.str2suit('Heart')
                        heart_list = self.ht.card_select_by_suit(heart_suit, self.my_unused_card)
			highest_card = 0
			for c_card in self.all_board_card:
				if self.ht.get_card_rank(c_card) > highest_card:
					highest_card = self.ht.get_card_rank(c_card)

			if self.ht.get_card_rank(heart_list[0]) > highest_card:
				if len(self.all_board_card) == 3 or (len(self.all_board_card) == 2 and self.ht.get_card_rank(heart_list[0]) > (highest_card + 3)):
					# I'm going to get it anyway, so play the highest
					return heart_list[-1]

				return heart_list[0]

			# Play highest hearts that doesn't win
			low_list = []
			for c_card in heart_list:
				if self.ht.get_card_rank(c_card) < highest_card:
					low_list.append(c_card)

			if len(low_list):
				return low_list[0]

			# Play lowest card
			return heart_list[0]

		# Play clubs or diamonds
		suit_list = []
		suit_played = 0
		if lead_suit == 4:
			l_suit = self.ht.str2suit('Diamond')
			suit_list = self.ht.card_select_by_suit(l_suit, self.my_unused_card)
			suit_played = self.ht.calc_card_num_by_suit(l_suit, self.all_used_card)
		else:
			l_suit = self.ht.str2suit('Club')
			suit_list = self.ht.card_select_by_suit(l_suit, self.my_unused_card)
			suit_played = self.ht.calc_card_num_by_suit(l_suit, self.all_used_card)

		# Play high card if I don't take the queen of hearts
		if suit_played < 2 and not self.ht.str2card('Qs', fixfmt = False) in self.all_board_card:
			return suit_list[-1]

		# If I'm the last in the trick, take with high card
		if len(self.all_board_card) == 3 and not self.ht.str2card('Qs', fixfmt = False) in self.all_board_card:
			return suit_list[-1]

		# Play the highest card that doesn't win the trick
		highest_card = 0
		for c_card in self.all_board_card:
			if self.ht.get_card_rank(c_card) > highest_card:
				highest_card = self.ht.get_card_rank(c_card)

		low_list = []
		for c_card in suit_list:
			if self.ht.get_card_rank(c_card) < highest_card:
				low_list.append(c_card)

		if len(low_list):
			return low_list[-1]

		# Play lowest card
		return suit_list[0]

	def __dont_follow_suit(self, data):
		if self.ht.str2card('Qs', fixfmt = False) in self.my_unused_card:
			return self.ht.str2card('Qs', fixfmt = False)

		if self.ht.str2card('Ks', fixfmt = False) in self.my_unused_card:
			return self.ht.str2card('Ks', fixfmt = False)

		if self.ht.str2card('As', fixfmt = False) in self.my_unused_card:
			return self.ht.str2card('As', fixfmt = False)

		highest_score = 0
		highest_card = self.my_unused_card[0]
		for c_card in self.my_unused_card:
			if highest_score < self.ht.get_card_rank(c_card):
				highest_score = self.ht.get_card_rank(c_card)
				highest_card = c_card

		heart_suit = self.ht.str2suit('Heart')
		heart_list = self.ht.card_select_by_suit(heart_suit, self.my_unused_card)
		if self.ht.get_card_rank(highest_card) < 8 and len(heart_list):
			return highest_card

		return highest_card

	def time2shoot(self, data):
		self.all_used_card = data['used_card'][:]
		self.all_unused_card = data['unused_card'][:]
		self.all_board_card = data['board_card'][:]
		self.is_hb = data['is_hb']
		self.roundnum = data['roundnum']
		self.my_unused_card = data['player_unused_card'][:]
		self.my_avail_card = data['avail_card'][:]

		print ("unused card: " + self.ht.get_card_pretty_list(self.my_unused_card))
		print ("avail card: " + self.ht.get_card_pretty_list(self.my_avail_card))

		if len(self.all_board_card) == 0:
			return self.__open_trick(data)
		elif self.ht.calc_card_num_by_suit(self.ht.get_card_suit(self.all_board_card[0]), self.my_avail_card):
			return self.__follow_suit(data)
		else:
			return self.__dont_follow_suit(data)

		card = random.choice(self.my_avail_card)
		print ("...shoot card: " + self.ht.get_card_pretty(card))
		return card

	def nextround(self, data):
		"""
		next round
		"""

		pass

	def nextgame(self, data):
		"""
		next game
		"""

		pass
