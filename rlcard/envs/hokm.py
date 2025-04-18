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
        self.game = HokmGame(allow_step_back=config.get('allow_step_back', False))
        super().__init__(config)
        self.num_players = self.game.get_num_players()
        self.num_actions = self.game.get_num_actions()
        self.agents = [None for _ in range(self.num_players)]
        self.allow_step_back = config.get('allow_step_back', False)
        # Track played cards with player info
        self.action_record = []
        self.state_shape = [5, 52]  # 5 features x 52 cards (hand, table, hokm, tricks won, current player)
        self.action_shape = [52]    # 52 possible card actions

    def _extract_state(self, state):
        ''' Extract useful information directly from game for RL '''
        player_id = state['current_player'] if isinstance(state, dict) else state
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

        # Get team scores - in Hokm, team 0 consists of players 0,2; team 1 consists of players 1,3
        player_team = player_id % 2  # 0 or 1
        other_team = 1 - player_team
        
        # Get scores from player objects
        my_team_score = self.game.players[0].my_team_score if player_team == 0 else self.game.players[1].my_team_score
        other_team_score = self.game.players[1].my_team_score if player_team == 0 else self.game.players[0].my_team_score
        
        # Count completed tricks
        completed_tricks = my_team_score + other_team_score

        return {
            'obs': obs,
            'legal_actions': self._get_legal_actions(),
            'action_record': self.action_record.copy(),
            'current_player': player_id,
            'my_team_score': my_team_score,
            'other_team_score': other_team_score,
            'completed_tricks': completed_tricks
        }

    def reset(self):
        ''' Start a new game '''
        self.game.init_game()
        current_player = self.game.get_current_player()
        # Reset action record
        self.action_record = []
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

        # Record the action with player info
        self.action_record.append((self.game.current_player, decoded_action))
        
        # Take step in game
        _, next_player, trick_completed, trick_info = self.game.step(decoded_action)
        
        # Add trick completion info to the state if a trick was completed
        if trick_completed:
            # Get winner information
            winner = trick_info.get('winner', -1)
            if winner >= 0:
                # Get updated scores from the game
                team_0_score = self.game.players[0].my_team_score
                team_1_score = self.game.players[1].my_team_score
                
                # Add the trick completion info to the action record for display
                self.action_record.append(('trick_complete', {
                    'winner': winner,
                    'team_0_score': team_0_score,
                    'team_1_score': team_1_score,
                    'completed_tricks': team_0_score + team_1_score
                }))
        
        return self._extract_state(next_player), next_player

    def _get_legal_actions(self):
        ''' Get all legal actions for current state '''
        legal_actions = {}
        
        # Special case: Hokm selection for hakem
        if self.game.hokm is None and self.game.current_player == self.game.hakem:
            # Allow selecting hokm using first card of each suit
            for i, suit in enumerate(['S', 'H', 'D', 'C']):
                legal_actions[i * 13] = Card(suit, 'A')
            return legal_actions

        # Normal gameplay
        if self.game.hokm is None:
            raise Exception("Hokm is not set. Please select a hokm before playing.")

        legal_cards = self.game.get_legal_actions()
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
        current_player = self.game.get_current_player()
        return {
            'current_player': current_player,
            'current_hand': self.game.get_player_hand(current_player),
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
            # Special case: Force legal hokm selection actions
            state['legal_actions'] = {i * 13: Card(suit, 'A') 
                                    for i, suit in enumerate(['S', 'H', 'D', 'C'])}
            trajectories[player_id].append(state)
            hokm_action = self.agents[player_id].step(state)
            trajectories[player_id].append(hokm_action)
            hokm_card = self._decode_action(hokm_action)
            self.game.set_hokm(hokm_card.suit)
            state = self._extract_state(player_id)
            
            # Ensure legal actions aren't empty after hokm selection
            if not state['legal_actions']:
                # Get first player's legal actions after hokm is set
                legal_cards = self.game.get_legal_actions()
                state['legal_actions'] = {self._card_to_idx(card): card for card in legal_cards}

        # Continue with normal gameplay
        while not self.game.is_over():
            # Get current state with legal actions
            state = self._extract_state(player_id)
            
            # Always ensure there are legal actions before agent.step
            if not state['legal_actions']:
                legal_cards = self.game.get_legal_actions()
                if legal_cards:
                    state['legal_actions'] = {self._card_to_idx(card): card for card in legal_cards}
                else:
                    # If still no legal actions, game is likely over or in a terminal state
                    # Provide a default action (e.g., first card in hand or pass)
                    hand = self.game.get_player_hand(player_id)
                    if hand:
                        default_action = self._card_to_idx(hand[0])
                        state['legal_actions'] = {default_action: hand[0]}
                    else:
                        # No hand and no legal actions, game is truly stuck
                        # Return empty trajectories and zero payoffs
                        print("Game stuck, returning empty trajectories")
                        return trajectories, [0] * self.num_players

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