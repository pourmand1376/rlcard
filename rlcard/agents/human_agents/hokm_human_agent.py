from rlcard.utils.utils import print_card
from rlcard.games.base import Card
import time

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
        
        while True:
            try:
                action = int(input('>> You choose action (integer): '))
                if action >= 0 and action < len(state['legal_actions']):
                    return list(state['legal_actions'].keys())[action]
                else:
                    print(f'Invalid action. Please enter a number between 0 and {len(state["legal_actions"]) - 1}.')
            except ValueError:
                print('Please enter a valid integer.')

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
    
    # Get action record to show trick completion information
    action_record = state.get('action_record', [])
    
    # Check if the most recent entry is a trick completion
    if action_record and action_record[-1][0] == 'trick_complete':
        trick_info = action_record[-1][1]
        winner = trick_info.get('winner', -1)
        team_0_score = trick_info.get('team_0_score', 0)
        team_1_score = trick_info.get('team_1_score', 0)
        completed_tricks = trick_info.get('completed_tricks', 0)
        
        # Calculate which team the winner belongs to
        winner_team = winner % 2  # 0 or 1
        
        # Display the trick winner and updated scores
        if winner_team == 0:
            winner_team_name = "Team 0 (Players 0 & 2)"
        else:
            winner_team_name = "Team 1 (Players 1 & 3)"
            
        print(f"\n🏆 {winner_team_name} won the trick! Player {winner} takes it.")
        print(f"Current scores - Team 0: {team_0_score}, Team 1: {team_1_score}")
        print(f"Completed tricks: {completed_tricks}/13")
        
        # Show if this was a winning trick
        if team_0_score >= 7:
            print("🎉 Team 0 (Players 0 & 2) has won the game!")
            print(f"Final score will be - Team 0: {team_0_score}, Team 1: {13-team_0_score}")
        elif team_1_score >= 7:
            print("🎉 Team 1 (Players 1 & 3) has won the game!")
            print(f"Final score will be - Team 0: {13-team_1_score}, Team 1: {team_1_score}")
        else:
            print(f"Tricks needed to win: Team 0 needs {7-team_0_score}, Team 1 needs {7-team_1_score}")
    
    # Get the previous trick's cards (the most recent completed trick)
    previous_trick = []
    for i in range(len(action_record) - 1, -1, -1):
        if action_record[i][0] == 'trick_complete':
            # Look for the last 4 cards before this trick completion
            for j in range(i - 1, max(i - 5, -1), -1):
                if isinstance(action_record[j], tuple) and len(action_record[j]) == 2 and isinstance(action_record[j][0], int):
                    previous_trick.insert(0, action_record[j])  # Insert at beginning to maintain order
            break
    
    # Print previous trick if available
    if previous_trick:
        print('\n=========== Previous Trick ===========')
        # Display cards horizontally
        cards_to_display = [card for _, card in previous_trick]
        print_card(cards_to_display)
        
        # Get player positions relative to the current player
        player_positions = ['You', 'Right', 'Partner', 'Left']
        current_player = state.get('current_player', 0)
        
        # Display player labels aligned with cards
        player_labels = []
        for player_id, _ in previous_trick:
            relative_pos = (player_id - current_player) % 4
            player_labels.append(player_positions[relative_pos])
        
        print("   ".join([f"   {label}    " for label in player_labels]))
            
    # Print player's hand
    print('\n=============== Your Hand ===============')
    print_card(hand_cards)
    
    # Print table cards with better formatting
    if table_cards:
        print('\n============ Table Cards =============')
        # Try to get action record if available
        if action_record:
            # Prepare a horizontal display of cards with their player labels
            player_positions = ['You', 'Right', 'Partner', 'Left']
            current_player = state.get('current_player', 0)
            
            # Create a list of (position_name, card) pairs for the most recent cards
            table_display = []
            for record in action_record:
                # Skip non-card records
                if not isinstance(record, tuple) or len(record) != 2:
                    continue
                
                # Skip trick completion records
                if record[0] == 'trick_complete':
                    continue
                
                # Make sure we only process player records (integers) with cards
                if not isinstance(record[0], int):
                    continue
                    
                player_id, card = record
                # Calculate relative position (0 = human, 1 = right, 2 = partner, 3 = left) for counter-clockwise play
                relative_pos = (player_id - current_player) % 4
                table_display.append((player_positions[relative_pos], card))
            
            # Only display the current trick's cards (maximum 4)
            table_display = table_display[-len(table_cards):]
            
            # Print cards horizontally
            print_card([card for _, card in table_display])
            
            # Print player labels aligned with cards
            print("   ".join([f"   {name}    " for name, _ in table_display]))
        else:
            # Default display if no action record
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

    # Print scores if available
    if 'my_team_score' in state and 'other_team_score' in state:
        # Get the completed tricks count
        completed_tricks = state.get('completed_tricks', state['my_team_score'] + state['other_team_score'])
        
        # Determine which team the player is on
        player_id = state.get('current_player', 0)
        player_team = player_id % 2  # 0 or 1
        
        # Get the team names and scores
        if player_team == 0:
            my_team_name = "Team 0 (Players 0 & 2)"
            other_team_name = "Team 1 (Players 1 & 3)"
            team_0_score = state['my_team_score']
            team_1_score = state['other_team_score']
        else:
            my_team_name = "Team 1 (Players 1 & 3)"
            other_team_name = "Team 0 (Players 0 & 2)"
            team_0_score = state['other_team_score']
            team_1_score = state['my_team_score']
            
        print('\n========== Current Scores ===========')
        print(f"{my_team_name}: {state['my_team_score']}")
        print(f"{other_team_name}: {state['other_team_score']}")
        print(f"Completed tricks: {completed_tricks}/13")
        print(f"Tricks needed to win: Your team needs {7-state['my_team_score']}, opponent team needs {7-state['other_team_score']}")

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
