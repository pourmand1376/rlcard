import numpy as np
from rlcard.games.base import Card
from rlcard.games.hokm.player import HokmPlayer
from rlcard.games.hokm.judger import HokmJudger
from rlcard.games.hokm.dealer import HokmDealer

class HokmGame:
    ''' Game class for Hokm
    '''
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
        ''' Get the number of players in the game

        Returns:
            int: The number of players in the game
        '''
        return 4  # Hokm is always played with 4 players

    def get_num_actions(self):
        ''' Get the number of possible actions in the game

        Returns:
            int: The number of possible actions
        '''
        return 52  # 52 cards in a standard deck

    def init_game(self):
        ''' Initialize a new game '''
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
        ''' Take a game step
        
        Before modifying state, save current state for potential step_back
        '''
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
        ''' Take a step back for RL training purposes
        
        Returns:
            bool: True if the step back is successful
        '''
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
        ''' Set the hokm suit

        Args:
            hokm (str): The hokm suit to set
        '''
        self.hokm = hokm
        for player in self.players:
            player.set_hokm(hokm)

    def get_state(self, player_id):
        ''' Get the state of the game

        Args:
            player_id (int): The ID of the player

        Returns:
            dict: The state of the game
        '''
        state = {}
        state['hand'] = self.players[player_id].get_hand()
        state['table'] = self.table
        state['hokm'] = self.hokm
        state['hakem'] = self.hakem
        state['current_player'] = self.current_player
        state['legal_actions'] = self.judger.get_legal_actions(self.players[player_id], self.table)
        state['player_scores'] = [p.my_team_score for p in self.players]  # Changed my_score to my_team_score
        return state

    def get_payoffs(self):
        ''' Get the payoffs of the game '''
        return self.judger.get_payoffs(self.players)

    def get_legal_actions(self):
        ''' Get the legal actions for the current player

        Returns:
            list: A list of legal actions
        '''
        return self.judger.get_legal_actions(self.players[self.current_player], self.table)

    def is_over(self):
        ''' Check if the game is over

        Returns:
            bool: True if the game is over
        '''
        # Game is over when a player reaches 7 points
        return any(player.my_team_score >= 7 for player in self.players)

