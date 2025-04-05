import numpy as np
from rlcard.envs import Env
from rlcard.games.hokm import HokmGame
from rlcard.games.base import Card

class HokmEnv(Env):
    ''' Hokm Environment
    '''
    def __init__(self, config):
        ''' Initialize the Hokm environment

        Args:
            config (dict): A configuration dictionary
        '''
        self.name = 'hokm'
        self.game = HokmGame()
        super().__init__(config)
        self.state_shape = [5, 52]  # 5 features x 52 cards (hand, table, hokm, tricks won, current player)
        self.action_shape = [52]    # 52 possible card actions
        self.allow_step_back = config.get('allow_step_back', False)

    def _extract_state(self, player_id):
        ''' Extract useful information directly from game for RL '''
        obs = np.zeros((5, 52), dtype=int)
        
        # Encode hand cards
        for card in self.game.get_player_hand(player_id):
            card_idx = self._card_to_idx(card)
            obs[0][card_idx] = 1
            
        # Encode table cards
        for card in self.game.get_table_cards():
            card_idx = self._card_to_idx(card)
            obs[1][card_idx] = 1
            
        # Encode hokm
        hokm = self.game.get_current_hokm()
        if hokm:
            for i in range(52):
                if i // 13 == ['S', 'H', 'D', 'C'].index(hokm):
                    obs[2][i] = 1
                    
        # Encode tricks won
        tricks = self.game.get_tricks_won(player_id)
        obs[3][:tricks] = 1
        
        # Encode current player
        obs[4][self.game.get_current_player() * 13:(self.game.get_current_player() + 1) * 13] = 1

        return {
            'obs': obs,
            'legal_actions': self._get_legal_actions()
        }

    def reset(self):
        ''' Start a new game '''
        self.game.init_game()
        current_player = self.game.get_current_player()
        return self._extract_state(current_player), current_player

    def step(self, action):
        ''' Take one step in the game '''
        # Decode and validate action
        decoded_action = self._decode_action(action)
        legal_actions = self.game.get_legal_actions()
        
        if legal_actions:
            for card in legal_actions:
                if card.suit == decoded_action.suit and card.rank == decoded_action.rank:
                    decoded_action = card
                    break

        # Take step in game
        _, next_player, _, _ = self.game.step(decoded_action)
        return self._extract_state(next_player), next_player

    def _get_legal_actions(self):
        ''' Get all legal actions for current state

        Returns:
            dict: Dictionary of legal action ids
        '''
        if self.game.hokm is None:
            raise Exception("Hokm is not set. Please select a hokm before playing.")

        legal_cards = self.game.get_legal_actions()
        legal_actions = {}
        for card in legal_cards:
            action_id = self._card_to_idx(card)
            legal_actions[action_id] = card
            
        return legal_actions

    def _decode_action(self, action_id):
        ''' Decode action id to the action in the game

        Args:
            action_id (int): The id of the action

        Returns:
            (Card): The action that will be passed to the game engine
        '''
        suit_idx = action_id // 13
        rank_idx = action_id % 13
        suit = ['S', 'H', 'D', 'C'][suit_idx]
        rank = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K'][rank_idx]
        return Card(suit, rank)

    def get_perfect_information(self):
        ''' Get the perfect information of the current state '''
        return {
            'current_player': self.game.get_current_player(),
            'current_hand': self.game.get_player_hand(self.game.get_current_player()),
            'hokm': self.game.get_current_hokm(),
            'table': self.game.get_table_cards(),
            'scores': self.game.get_player_scores()
        }

    def _card_to_idx(self, card):
        ''' Convert a card to its index in the action space

        Args:
            card (Card): The card to convert

        Returns:
            int: The index of the card
        '''
        suit_idx = ['S', 'H', 'D', 'C'].index(card.suit)
        rank_idx = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K'].index(card.rank)
        return suit_idx * 13 + rank_idx

    def _idx_to_card(self, idx):
        ''' Convert an index to a card

        Args:
            idx (int): The index to convert

        Returns:
            Card: The card at the index
        '''
        suit_idx = idx // 13
        rank_idx = idx % 13
        suit = ['S', 'H', 'D', 'C'][suit_idx]
        rank = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K'][rank_idx]
        return Card(suit, rank)

    def get_payoffs(self):
        ''' Get the payoffs of the game

        Returns:
            list: The payoffs of the game
        '''
        return self.game.get_payoffs()

    def run(self, is_training=False):
        ''' Run a complete game, either for evaluation or training

        Args:
            is_training (bool): True if for training purpose

        Returns:
            (tuple): Tuple containing:
                (list): A list of trajectories for each player
                (list): A list of payoffs for each player
        '''
        trajectories = [[] for _ in range(self.num_players)]
        state, player_id = self.reset()
        
        # Initial hokm selection for hakem
        if player_id == self.game.hakem:
            trajectories[player_id].append(state)
            hokm_action = self.agents[player_id].step(state)
            trajectories[player_id].append(hokm_action)
            hokm_card = self._decode_action(hokm_action)
            self.game.set_hokm(hokm_card.suit)
        
        while not self.game.is_over():
            # Get current state
            state = self._extract_state(player_id)
            trajectories[player_id].append(state)
            
            # Get action from agent
            action = self.agents[player_id].step(state)
            trajectories[player_id].append(action)
            
            # Apply action
            try:
                decoded_action = self._decode_action(action)
                next_state, next_player = self.step(action)
                player_id = next_player
            except Exception as e:
                print(f"Invalid action {action} from player {player_id}: {str(e)}")
                return trajectories, [0] * self.num_players

        # Add final state
        for pid in range(self.num_players):
            trajectories[pid].append(self._extract_state(pid))

        return trajectories, self.get_payoffs()