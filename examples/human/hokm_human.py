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
while (True):
    print("\n>> Start a new game")
    
    trajectories, payoffs = env.run(is_training=False)
    final_state = trajectories[0][-1]
    
    # Print game result
    if len(trajectories[0]) != 0:
        # Show other players' actions
        action_record = final_state['action_record']
        state = final_state['raw_obs']
        _action_list = []
        for i in range(1, len(action_record)+1):
            if action_record[-i][0] == state['current_player']:
                break
            _action_list.insert(0, action_record[-i])
        for pair in _action_list:
            print('>> Player {} played:'.format(pair[0]))
            print_card(pair[1])

        # Show game result
        print('\n===============     Result     ===============')
        print('Your team payoff: ', payoffs[0])
        print('  Bot team payoff: ', payoffs[1])
        if payoffs[0] > 0:
            print('You win!')
        elif payoffs[0] == 0:
            print('It is a tie.')
        else:
            print('You lose!')
        print('')

    input("Press any key to continue...")
