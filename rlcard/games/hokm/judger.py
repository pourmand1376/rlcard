class HokmJudger:
    ''' Judger class for Hokm
    '''
    def __init__(self):
        ''' Initialize a Hokm judger
        '''
        self.value_map = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        for i in range(2, 10):
            self.value_map[str(i)] = i

    def get_winner(self, played_cards, hokm):
        ''' Get the winner of a round

        Args:
            played_cards (list): List of cards played in the round
            hokm (str): The current hokm suit

        Returns:
            int: The player id of the winner
        '''
        if not played_cards:
            return None

        # Get the first card's suit as the round suit
        round_suit = played_cards[0].suit
        max_value = -1
        winner = 0

        for i, card in enumerate(played_cards):
            # If the card is hokm, it's stronger than non-hokm cards
            if card.suit == hokm and round_suit != hokm:
                return i
            # If both cards are hokm or both are not hokm, compare their values
            elif card.suit == round_suit:
                value = self.value_map[card.rank]
                if value > max_value:
                    max_value = value
                    winner = i

        return winner

    def get_payoffs(self, players):
        ''' Get the payoffs of the game

        Args:
            players (list): List of players

        Returns:
            list: List of payoffs for each player
        '''
        payoffs = []
        for player in players:
            if player.my_score >= 7:  # Winning score is 7
                payoffs.append(1)
            else:
                payoffs.append(-1)
        return payoffs

    def get_legal_actions(self, player, table):
        ''' Get the legal actions for the current player

        Args:
            player (HokmPlayer): The current player
            table (list): The cards on the table

        Returns:
            list: List of legal actions (cards that can be played)
        '''
        if not table:  # If table is empty, all cards are legal
            return player.hand

        # Get the round suit from the first card
        round_suit = table[0].suit
        
        # Find cards of the same suit in player's hand
        legal_cards = [card for card in player.hand if card.suit == round_suit]
        
        # If player has no cards of the round suit, all cards are legal
        if not legal_cards:
            return player.hand
            
        return legal_cards 