from rlcard.utils.utils import print_card
from rlcard.games.base import Card

class HumanAgent(object):
    ''' A human agent for Hokm. It can be used to play against trained models
    or other human agents.
    '''

    def __init__(self, num_actions):
        ''' Initialize the human agent

        Args:
            num_actions (int): The size of the action space
        '''
        self.use_raw = True
        self.num_actions = num_actions

    @staticmethod
    def step(state):
        ''' Human agent will display the state and make decisions through interfaces

        Args:
            state (dict): A dictionary that represents the current state

        Returns:
            action (int): The action decided by human
        '''
        _print_state(state)
        action = int(input('>> You choose action (integer): '))
        while action < 0 or action >= len(state['legal_actions']):
            print('Action illegal...')
            action = int(input('>> Re-choose action (integer): '))
        return list(state['legal_actions'].keys())[action]

    def eval_step(self, state):
        ''' 
        Predict the action given the current state for evaluation.
        The same as step here since we are not training.
        
        Args:
            state (dict): An dictionary that represents the current state

        Returns:
            action (int): The action predicted (chosen) by the human agent
            probs (list): The list of action probabilities
        '''
        return self.step(state), []

def _print_state(state):
    ''' Print out the state of the game '''
    perfect_info = state.get('obs', {})
    hand_cards = [_idx_to_card(i) for i in range(52) if perfect_info[0][i]]
    table_cards = [_idx_to_card(i) for i in range(52) if perfect_info[1][i]]
    
    # Print player's hand
    print('\n=============== Your Hand ===============')
    print_card(hand_cards)
    
    # Print table cards
    if table_cards:
        print('\n============ Table Cards =============')
        print_card(table_cards)

    # Print hokm if set
    hokm_idx = -1
    for i in range(52):
        if perfect_info[2][i]:
            hokm_idx = i
            break
    if hokm_idx >= 0:
        hokm_suit = ['S', 'H', 'D', 'C'][hokm_idx // 13]
        print(f'\nHokm (Trump suit): {hokm_suit}')

    print('\n=========== Actions You Can Choose ===========')
    for i, (action_id, _) in enumerate(state['legal_actions'].items()):
        card = _idx_to_card(action_id)
        print(f'{i}: {card}', end='  ')
    print('\n')

def _idx_to_card(idx):
    ''' Convert card index to Card object

    Args:
        idx (int): card index

    Returns:
        Card: Card object
    '''
    suit = ['S', 'H', 'D', 'C'][idx // 13]
    rank = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K'][idx % 13]
    return Card(suit, rank)
