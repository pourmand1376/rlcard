import numpy as np
from rlcard.games.base import Card
from rlcard.games.hokm.player import HokmPlayer
from rlcard.games.hokm.judger import HokmJudger
from rlcard.games.hokm.dealer import HokmDealer

class HokmGame:
    """
    Game class for Hokm - a four-player trick-taking card game.
    
    The game is played with a standard 52-card deck between two teams of two players each.
    Players must follow suit if possible. If a player cannot follow suit, they may play any card.
    The hokm (trump) suit is chosen by the hakem (dealer) and beats all other suits.
    
    Attributes:
        allow_step_back (bool): Whether stepping back to previous states is allowed
        np_random (RandomState): NumPy random number generator
        judger (HokmJudger): Handles game rules and scoring
        payoffs (list): Current game payoffs for each player
        players (list): List of HokmPlayer instances
        current_player (int): ID of the current player (0-3)
        hakem (int): ID of the player who chose hokm
        hokm (str): The current trump suit ('S', 'H', 'D', or 'C')
        state_history (list): History of game states for step_back
        table (list): Cards played in current trick
        round_history (list): History of completed tricks
    """
    def __init__(self, allow_step_back=False):
        ''' Initialize the game

        Args:
            allow_step_back (bool): Whether to allow step back
        '''
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        self.judger = HokmJudger()
        self.payoffs = [0 for _ in range(4)]  # 4 players
        self.players = []
        self.current_player = 0
        self.hakem = 0  # The player who chooses hokm
        self.hokm = None
        self.state_history = []
        self.table = []  # Current round's cards
        self.round_history = []  # History of all rounds

    def get_num_players(self):
        """
        Get the number of players in Hokm.

        Returns:
            int: Always 4, as Hokm is strictly a four-player game
        """
        return 4  # Hokm is always played with 4 players

    def get_num_actions(self):
        """
        Get the number of possible actions in the game.

        Returns:
            int: 52, representing each card in a standard deck
        """
        return 52  # 52 cards in a standard deck

    def init_game(self):
        """
        Initialize a new game of Hokm.

        This method:
        1. Creates a new dealer
        2. Initializes 4 players
        3. Randomly selects hakem (dealer)
        4. Deals cards to all players
        5. Lets hakem choose hokm (trump suit)
        6. Resets game state trackers

        Returns:
            dict: Initial game state for current player
        """
        # Initialize dealer
        self.dealer = HokmDealer(self.np_random)

        # Initialize players
        self.players = [HokmPlayer(i) for i in range(4)]
        
        # Set hakem attributes for all players
        self.hakem = self.np_random.randint(0, 4)
        for player in self.players:
            player.hakem = self.hakem
        
        self.current_player = self.hakem

        # Deal and initialize cards
        dealt_cards = self.dealer.deal_initial_cards()
        for player_id, cards in dealt_cards.items():
            if player_id == self.hakem:
                self.players[player_id].add_cards_to_hand(cards[:5])
                selected_hokm = self.players[player_id].select_hokm()
                self.hokm = selected_hokm
                for p in self.players:
                    p.set_hokm(selected_hokm)
                self.players[player_id].add_cards_to_hand(cards[5:])
            else:
                self.players[player_id].add_cards_to_hand(cards)

        # Reset state trackers
        self.state_history = []
        self.table = []
        self.round_history = []

        return self.get_state(self.current_player)

    def step(self, action):
        """
        Execute one step of the game by playing a card.

        Args:
            action (Card): The card being played

        Returns:
            tuple: Contains:
                - dict: The game state after the action
                - int: ID of the next player
                - bool: Whether the current trick is complete
                - dict: Additional information (e.g., trick winner)

        Raises:
            ValueError: If the action is not legal
        """
        if self.allow_step_back:
            # Save complete game state
            state = {
                'current_player': self.current_player,
                'hokm': self.hokm,
                'table': self.table.copy(),
                'hands': [p.get_hand().copy() for p in self.players],
                'scores': [p.my_team_score for p in self.players]
            }
            self.state_history.append(state)

        # Add card to table
        if action not in self.get_legal_actions():
            raise ValueError(f'Illegal action: {action}')
        
        self.table.append(action)
        self.players[self.current_player].remove_from_hand(action)

        # Check if round is over (4 cards played)
        round_over = len(self.table) == 4

        if round_over:
            # Get round winner
            winner = self.judger.get_winner(self.table, self.hokm)
            
            # Update scores
            self.players[winner].update_score(True)
            for i in range(4):
                if i != winner and i != (winner + 2) % 4:
                    self.players[i].update_score(False)

            # Store round history and reset table
            self.round_history.append(self.table)
            self.table = []
            self.current_player = winner

            if self.is_over():
                return self.get_state(self.current_player), self.current_player, True, {'winner': winner}
        else:
            # Move to next player
            self.current_player = (self.current_player + 1) % 4

        return self.get_state(self.current_player), self.current_player, round_over, {}

    def step_back(self):
        """
        Revert the game to the previous state.

        Used primarily for reinforcement learning training.
        Restores:
        - Current player
        - Table cards
        - Player hands
        - Scores
        - Hokm

        Returns:
            bool: True if step back was successful, False if not allowed or no history
        """
        if not self.allow_step_back or len(self.state_history) == 0:
            return False

        # Restore the previous state with complete game info
        prev_state = self.state_history.pop()
        
        # Restore game state
        self.current_player = prev_state['current_player']
        self.hokm = prev_state['hokm']
        self.table = prev_state['table'].copy()
        
        # Important: Restore player hands
        for player, hand in zip(self.players, prev_state['hands']):
            player.hand = hand.copy()
            
        # Restore any other necessary game state
        if 'scores' in prev_state:
            for player, score in zip(self.players, prev_state['scores']):
                player.my_team_score = score
                
        return True

    def set_hokm(self, hokm):
        """
        Set the trump suit for the game.

        Args:
            hokm (str): The trump suit to set ('S', 'H', 'D', or 'C')
        """
        self.hokm = hokm
        for player in self.players:
            player.set_hokm(hokm)

    def get_player_hand(self, player_id):
        """
        Retrieve the cards in a player's hand.

        Args:
            player_id (int): The ID of the player (0-3)

        Returns:
            list: List of Card objects in the player's hand
        """
        return self.players[player_id].get_hand()

    def get_table_cards(self):
        """
        Get the cards currently played in the active trick.

        Returns:
            list: List of Card objects on the table
        """
        return self.table

    def get_current_hokm(self):
        """
        Get the current trump suit.

        Returns:
            str: Current hokm suit ('S', 'H', 'D', or 'C')
        """
        return self.hokm

    def get_hakem(self):
        """
        Get the ID of the hakem (dealer) player.

        Returns:
            int: Player ID of the hakem (0-3)
        """
        return self.hakem

    def get_current_player(self):
        """
        Get the ID of the player whose turn it is.

        Returns:
            int: Current player's ID (0-3)
        """
        return self.current_player

    def get_player_scores(self):
        """
        Get the current scores for all players.

        Returns:
            list: List of team scores for each player. Players on the same team
                 will have the same score.
        """
        return [p.my_team_score for p in self.players]

    def get_state(self, player_id):
        """
        Get the complete game state from a player's perspective.

        Args:
            player_id (int): The ID of the player (0-3)

        Returns:
            dict: Current game state including:
                - hand: Player's current cards
                - table: Cards in current trick
                - hokm: Current trump suit
                - hakem: ID of hakem player
                - current_player: ID of active player
                - legal_actions: List of legal plays
                - player_scores: Current team scores
        """
        return {
            'hand': self.get_player_hand(player_id),
            'table': self.get_table_cards(),
            'hokm': self.get_current_hokm(),
            'hakem': self.get_hakem(),
            'current_player': self.get_current_player(),
            'legal_actions': self.get_legal_actions(),
            'player_scores': self.get_player_scores()
        }

    def get_payoffs(self):
        """
        Calculate the current payoffs for all players.

        Returns:
            list: Payoff values for each player. Team members receive the same payoff.
                 Winning team gets positive values, losing team gets negative.
                 Values are doubled for 7-0 victories.
        """
        return self.judger.get_payoffs(self.players)

    def get_legal_actions(self):
        """
        Determine the legal cards that can be played by current player.

        Takes into account:
        - Cards in player's hand
        - Requirement to follow suit if possible
        - Ability to play any card if can't follow suit

        Returns:
            list: List of Card objects that can be legally played
        """
        return self.judger.get_legal_actions(self.players[self.current_player], self.table)

    def is_over(self):
        """
        Check if the game has ended.

        The game ends when one team reaches 7 tricks.

        Returns:
            bool: True if a team has won, False otherwise
        """
        # Game is over when a player reaches 7 points
        return any(player.my_team_score >= 7 for player in self.players)

    def get_player(self, player_id):
        """
        Get the player object for a specific player ID.

        Args:
            player_id (int): The ID of the player (0-3)

        Returns:
            HokmPlayer: The player object corresponding to the given ID
        """
        return self.players[player_id]

    def get_player_id(self):
        """Get current player's ID.
        Returns:
            int: Current player ID (0-3)
        """
        return self.current_player

    def get_tricks_won(self, player_id):
        """
        Get the number of tricks won by a player's team.
        
        Args:
            player_id (int): The ID of the player (0-3)
            
        Returns:
            int: Number of tricks won by the player's team
        """
        return self.players[player_id].my_team_score