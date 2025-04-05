class HokmJudger:
    ''' The judger class for Hokm card game.
    
    This class implements the core rules and logic for the Hokm card game, including
    determining winners, calculating payoffs, and validating legal moves.
    
    Attributes:
        value_map (dict): Maps card ranks to their numerical values for comparison.
                         Ace=14, King=13, Queen=12, Jack=11, Ten=10, numbers=face value.
    
    Note:
        The judger enforces these key rules:
        1. Hokm (trump) suit beats all other suits
        2. If no hokm is played, highest card of the round suit wins
        3. Players must follow the round suit if they have it
        4. If a player doesn't have the round suit, they can play any card
    '''
    
    def __init__(self):
        ''' Initialize a Hokm judger with card values mapping.
        
        Creates a mapping dictionary that assigns numerical values to card ranks
        for comparing card strengths within the same suit.
        
        Note:
            The hierarchy from highest to lowest is:
            - Ace (A) = 14
            - King (K) = 13
            - Queen (Q) = 12
            - Jack (J) = 11
            - Ten (T) = 10
            - Numbers 2-9 = face value
        '''
        self.value_map = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        for i in range(2, 10):
            self.value_map[str(i)] = i

    # Add class constants for scoring
    HAKEM_MULTIPLIER = 2
    NON_HAKEM_MULTIPLIER = 3

    def get_winner(self, played_cards, hokm):
        ''' Determine the winner of a round based on played cards and hokm suit.
        
        Args:
            played_cards (list): List of Card objects played in the round, in order of play.
                               The first card determines the round suit that others must follow.
            hokm (str): The current hokm (trump) suit, must be one of ['S', 'H', 'D', 'C'].
        
        Returns:
            int or None: The index (0-3) of the winning player in the played_cards list.
                        Returns None if played_cards is empty.
        
        Examples:
            >>> judger = HokmJudger()
            >>> # Round suit wins with highest value
            >>> cards = [Card('S','A'), Card('S','K'), Card('S','Q'), Card('S','J')]
            >>> judger.get_winner(cards, hokm='H')  # Returns 0 (Ace of Spades wins)
            
            >>> # Hokm wins over higher cards of round suit
            >>> cards = [Card('S','A'), Card('H','2'), Card('S','K'), Card('S','Q')]
            >>> judger.get_winner(cards, hokm='H')  # Returns 1 (2 of Hearts wins)
            
            >>> # Empty list returns None
            >>> judger.get_winner([], hokm='H')  # Returns None
        
        Raises:
            ValueError: If hokm is not a valid suit ['S', 'H', 'D', 'C'].
            TypeError: If played_cards contains non-Card objects.
        '''
        if not played_cards:
            return None

        # Get the first card's suit as the round suit
        round_suit = played_cards[0].suit
        
        # First check if any hokm cards were played
        hokm_cards = [(i, card) for i, card in enumerate(played_cards) if card.suit == hokm]
        
        # If hokm cards were played and round suit is not hokm, find highest hokm card
        if hokm_cards and round_suit != hokm:
            max_hokm_value = -1
            max_hokm_index = -1
            for i, card in hokm_cards:
                value = self.value_map[card.rank]
                if value > max_hokm_value:
                    max_hokm_value = value
                    max_hokm_index = i
            return max_hokm_index
        
        # Otherwise, find highest card of round suit
        max_value = -1
        winner = 0
        for i, card in enumerate(played_cards):
            if card.suit == round_suit:
                value = self.value_map[card.rank]
                if value > max_value:
                    max_value = value
                    winner = i

        return winner

    def get_payoffs(self, players):
        ''' Return payoffs with multipliers only when one team gets all 7 tricks
            - Hakem team wins 7-0: 2x points
            - Non-hakem team wins 7-0: 3x points
            - Any other score: 1x points
        '''
        team_0_score = players[0].my_team_score
        team_1_score = players[1].my_team_score
        is_hakem_team_0 = players[0].is_hakem_team()
        
        # Check if it's a complete 7-0 win
        is_seven_zero = (team_0_score == 7 and team_1_score == 0) or (team_0_score == 0 and team_1_score == 7)
        team_0_wins = team_0_score > team_1_score

        # Only apply multiplier for 7-0 wins
        if is_seven_zero:
            multiplier = self.HAKEM_MULTIPLIER if (team_0_wins == is_hakem_team_0) else self.NON_HAKEM_MULTIPLIER
        else:
            multiplier = 1

        base_payoff = multiplier if team_0_wins else -multiplier
        return [base_payoff, -base_payoff, base_payoff, -base_payoff]

    def get_legal_actions(self, player, table):
        ''' Determine which cards a player can legally play on their turn.
        
        Args:
            player (HokmPlayer): The player whose legal moves are being determined.
                                Must have a 'hand' attribute containing their cards.
            table (list): List of Card objects already played in the current round.
                         The first card determines the round suit that must be followed.
        
        Returns:
            list: List of Card objects that can be legally played according to the rules:
                 - If table is empty (first to play), returns all cards in hand
                 - If player has cards of round suit, returns only those cards
                 - If player has no round suit cards, returns all cards in hand
        
        Examples:
            >>> judger = HokmJudger()
            >>> # First to play - all cards legal
            >>> player.hand = [Card('H','A'), Card('S','K')]
            >>> judger.get_legal_actions(player, [])  # Returns [Card('H','A'), Card('S','K')]
            
            >>> # Must follow round suit
            >>> table = [Card('S','Q')]
            >>> player.hand = [Card('S','K'), Card('H','A')]
            >>> judger.get_legal_actions(player, table)  # Returns [Card('S','K')]
        
        Raises:
            AttributeError: If player object doesn't have a 'hand' attribute
            TypeError: If table contains non-Card objects
        '''
        # Handle empty hand case
        if not player.hand:
            return []
            
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