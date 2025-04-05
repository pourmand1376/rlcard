import random  # Add this import at the top of the file

class HokmPlayer:
    ''' A player class for Hokm
    '''
    def __init__(self, player_id):
        ''' Initialize a Hokm player

        Args:
            player_id (int): The id of the player
        '''
        # Basic player attributes
        self.player_id = player_id
        self.team_id = player_id % 2  # Team 0: players 0,2; Team 1: players 1,3
        self.partner_id = (player_id + 2) % 4
        self.hand = []
        self.hokm = None
        self.my_team_score = 0
        self.other_team_score = 0
        
        # Simplified but complete tracking structures
        self.current_round = 0
        self.hakem_id = None
        
        # Most important tracking structures
        self.round_history = {}  # {round_num: [(player_id, card), ...]}
        self.played_cards_by_suit = {'S': [], 'H': [], 'D': [], 'C': []}
        
        # Value map for card evaluation
        self.value_map = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        for i in range(2, 10):
            self.value_map[str(i)] = i

        # Initialize memory structures
        self.memory_finished_cards = {}
        self.memory_cards_state = {}
        self.memory_of_hakem = None
        self.hakem = None  # Add hakem attribute

    def is_hakem_team(self):
        ''' Check if the player is in the hakem team
        '''
        return self.player_id == self.hakem or self.partner_id == self.hakem

    def get_player_id(self):
        ''' Return the player's id
        '''
        return self.player_id

    def get_hand(self):
        ''' Get the player's hand
        '''
        return self.hand

    def set_hokm(self, val):
        ''' Set the hokm to player's mind
        '''
        self.hokm = val

    def add_cards_to_hand(self, cards):
        ''' Add cards to the player's hand
        '''
        self.hand.extend(cards)

    def remove_from_hand(self, card):
        ''' Remove a card from the player's hand '''
        for hand_card in self.hand:
            if hand_card.suit == card.suit and hand_card.rank == card.rank:
                self.hand.remove(hand_card)
                return
        raise ValueError(f"Card {card} not found in hand")

    def update_score(self, win_trick=False, points=1):
        ''' Update the player's team score when winning a trick
        
        Args:
            win_trick (bool): True if this player's team won the trick
            points (int): Number of points to add (usually 1 per trick)
        '''
        if win_trick:
            self.my_team_score += points

    def add_my_score(self, score=1):
        ''' Add score to the player's team total
        '''
        self.my_team_score += score

    def set_other_score(self, n_hand):
        ''' Set the score of the other team
        '''
        self.other_team_score = 13 - n_hand - self.my_team_score

    def remember_hakem(self, hakem):
        ''' Remember who is the hakem
        '''
        self.memory_of_hakem = hakem

    def update_finished_cards_state(self, player_number, card_type):
        ''' Update the player's memory of finished cards in other players' hands
        '''
        self.memory_finished_cards[card_type + "_of_" + str(player_number)] = 1

    def update_cards_state(self, cards, new_states):
        ''' Update the player's memory of cards state
        '''
        for card, state in zip(cards, new_states):
            self.memory_cards_state[str(card)] = state

    def select_hokm(self):
        ''' Select Hokm based on the cards in hand
        
        Note: In a real RL implementation, this method should be replaced by
        the RL agent's decision based on the current state and learned policy.
        For now, we're using random selection as a placeholder.
        '''
        possible_hokms = list(set([card.suit for card in self.hand]))
        return random.choice(possible_hokms)

    def _get_card_value(self, card):
        ''' Get the value of a card for scoring purposes
        '''
        value_map = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        if card.rank in value_map:
            return value_map[card.rank]
        return int(card.rank)

    def get_state(self):
        ''' Get the state of the player
        '''
        return {
            'hand': self.hand,
            'hokm': self.hokm,
            'my_team_score': self.my_team_score,
            'other_team_score': self.other_team_score
        }

    def record_played_card(self, round_num, player_id, card):
        ''' Simplified card recording with only essential tracking
        
        Args:
            round_num (int): The round number
            player_id (int): The player who played the card
            card (Card): The card that was played
        '''
        # Update current round if needed
        if round_num > self.current_round:
            self.current_round = round_num
            
        # Add to round-specific history
        if round_num not in self.round_history:
            self.round_history[round_num] = []
        self.round_history[round_num].append((player_id, card))
        
        # Add to suit-specific history
        self.played_cards_by_suit[card.suit].append((round_num, player_id, card))
    
    def get_player_played_cards(self, player_id):
        ''' Get all cards played by a specific player from round history
        '''
        cards = []
        for round_num, round_plays in self.round_history.items():
            for pid, card in round_plays:
                if pid == player_id:
                    cards.append((round_num, card))
        return cards

    def get_team_score(self, team_id):
        ''' Get the score for a specified team
        
        In Hokm, team 0 consists of players 0 and 2, and team 1 consists of players 1 and 3.
        
        Args:
            team_id (int): 0 for team of players 0,2; 1 for team of players 1,3
            
        Returns:
            int: The total score for the specified team
        '''
        if team_id == self.team_id:
            return self.my_team_score
        else:
            return self.other_team_score

    def set_cards(self, cards):
        ''' Set the cards in the player's hand
        
        Args:
            cards (list): List of Card objects to set as the player's hand
        '''
        self.hand = cards