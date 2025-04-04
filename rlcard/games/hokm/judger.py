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

    def get_payoffs(self, players, cards_history, use_traditional_scoring=False):
        ''' Calculate the payoffs for all players at the end of the game.
        
        Args:
            players (list): List of 4 Player objects representing all players in order.
            cards_history (list): List of lists, where each inner list contains the 4 cards
                                played in order for each round.
            use_traditional_scoring (bool, optional): Scoring system selection:
                                                    - True: Winners get positive points, losers get 0
                                                    - False: Winners get positive points, losers get negative
                                                    Defaults to False.
        
        Returns:
            list: List of 4 integers representing payoffs for each player where:
                 - Normal win: ±1 point
                 - First 7 consecutive hands as hakem: ±2 points
                 - First 7 consecutive hands as non-hakem: ±3 points
        
        Examples:
            >>> judger = HokmJudger()
            >>> # Normal win for team 0,2
            >>> payoffs = judger.get_payoffs(players, cards_history)  # Returns [1, -1, 1, -1]
            
            >>> # First 7 consecutive win as hakem for team 1,3
            >>> payoffs = judger.get_payoffs(players, cards_history)  # Returns [-2, 2, -2, 2]
        
        Note:
            - Players 0,2 form one team and players 1,3 form the other team
            - A team wins by taking 7 or more hands in the game
            - First 7 consecutive wins have special scoring rules
        '''
        payoffs = []
        
        # Determine which team won
        team_0_2_won = players[0].my_score >= 7 or players[2].my_score >= 7
        team_1_3_won = players[1].my_score >= 7 or players[3].my_score >= 7
        
        # Get winning player and check if they're hakem
        winning_player = players[0] if team_0_2_won else players[1]
        is_hakem = winning_player.is_hakem_team()
        
        # Check first 7 rounds history for consecutive wins
        is_first_seven = False
        if len(cards_history) >= 7:
            first_seven_winners = []
            for round_cards in cards_history[:7]:
                winner_id = self.get_winner(round_cards, winning_player.hokm)
                first_seven_winners.append(winner_id % 2)  # Convert to team ID
                
            # Check if all first 7 hands were won by same team
            if len(set(first_seven_winners)) == 1:
                winning_team_id = first_seven_winners[0]
                if (winning_team_id == 0 and team_0_2_won) or \
                   (winning_team_id == 1 and team_1_3_won):
                    is_first_seven = True
        
        # Determine win multiplier
        win_multiplier = 1
        if is_first_seven:
            win_multiplier = 2 if is_hakem else 3
            
        # Assign payoffs based on winning team and scoring system
        for i in range(4):
            if i % 2 == 0:  # Team 0,2
                if team_0_2_won:
                    payoffs.append(win_multiplier)
                else:
                    payoffs.append(0 if use_traditional_scoring else -win_multiplier)
            else:  # Team 1,3
                if team_1_3_won:
                    payoffs.append(win_multiplier)
                else:
                    payoffs.append(0 if use_traditional_scoring else -win_multiplier)
        
        return payoffs

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