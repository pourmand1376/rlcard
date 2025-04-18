''' A toy example of playing against rule-based bots on Hokm
'''

import rlcard
from rlcard.agents.random_agent import RandomAgent
from rlcard.agents.human_agents.hokm_human_agent import HumanAgent as HokmHumanAgent
from rlcard.utils import print_card

# Make environment
env = rlcard.make('hokm')
human_agent = HokmHumanAgent(env.num_actions)
agent_2 = RandomAgent(env.num_actions)
agent_3 = RandomAgent(env.num_actions)
agent_4 = RandomAgent(env.num_actions)
env.set_agents([
    human_agent,
    agent_2,
    agent_3,
    agent_4,
])

print(">> Hokm Human vs Random Agents")
print(">> You are player 0, your partner is player 2")
print(">> Players 1 and 3 are your opponents")

while (True):
    print("\n>> Start a new game")
    
    trajectories, payoffs = env.run(is_training=False)
    final_state = trajectories[0][-1]
    
    # Print game result
    if len(trajectories[0]) != 0:
        # Show the actions in the last round
        action_record = final_state.get('action_record', [])
        if action_record:
            print('\n>> Last trick played:')
            player_positions = ['You', 'Left opponent', 'Your partner', 'Right opponent']
            
            # Get the last 4 cards (or fewer if less than 4 were played)
            # Filter out any non-card records (like 'trick_complete')
            last_trick = []
            for record in action_record[-8:]:  # Look at last 8 records to find up to 4 cards
                if isinstance(record, tuple) and len(record) == 2 and isinstance(record[0], int):
                    last_trick.append(record)
            
            # Take only the last 4 card records
            last_trick = last_trick[-4:]
            
            if last_trick:
                # Display cards horizontally
                cards_to_display = []
                for player_id, card in last_trick:
                    cards_to_display.append(card)
                
                print_card(cards_to_display)
                
                # Display player information aligned with cards
                player_labels = []
                for player_id, _ in last_trick:
                    player_labels.append(player_positions[player_id])
                
                print("   ".join([f"   {label}    " for label in player_labels]))

        # Show game result
        print('\n===============     Result     ===============')
        print('Your team score: ', payoffs[0])
        print('Opponent team score: ', payoffs[1])
        if payoffs[0] > 0:
            print('You win!')
        elif payoffs[0] == 0:
            print('It is a tie.')
        else:
            print('You lose!')
        print('')

    input("Press any key to continue...")
