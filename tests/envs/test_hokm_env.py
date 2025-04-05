import unittest
import numpy as np

import rlcard
from rlcard.agents.random_agent import RandomAgent
from .determism_util import is_deterministic


class TestHokmEnv(unittest.TestCase):

    def test_reset_and_extract_state(self):
        env = rlcard.make('hokm')
        state, _ = env.reset()
        self.assertEqual(state['obs'].size, 260)  # 5 features x 52 cards

    # def test_is_deterministic(self):
    #     # Set random seed for deterministic behavior
    #     import random
    #     random.seed(42)
    #     np.random.seed(42)
    #     self.assertTrue(is_deterministic('hokm'))

    def test_get_legal_actions(self):
        env = rlcard.make('hokm')
        env.set_agents([RandomAgent(env.num_actions) for _ in range(env.num_players)])
        env.reset()
        legal_actions = env._get_legal_actions()
        for legal_action in legal_actions:
            self.assertLessEqual(legal_action, env.num_actions-1)

    def test_step(self):
        env = rlcard.make('hokm')
        state, _ = env.reset()
        action = np.random.choice(list(state['legal_actions']))
        _, player_id = env.step(action)
        self.assertLessEqual(player_id, env.num_players-1)

    def test_step_back(self):
        # Test with step_back enabled
        env = rlcard.make('hokm', config={'allow_step_back':True})
        state, player_id = env.reset()
        action = np.random.choice(list(state['legal_actions']))
        env.step(action)
        _, back_player_id = env.step_back()
        self.assertEqual(player_id, back_player_id)
        self.assertEqual(env.step_back(), False)

        # Test with step_back disabled
        env = rlcard.make('hokm')
        with self.assertRaises(Exception):
            env.step_back()

    def test_run(self):
        env = rlcard.make('hokm')
        env.set_agents([RandomAgent(env.num_actions) for _ in range(env.num_players)])
        trajectories, payoffs = env.run(is_training=False)
        self.assertEqual(len(trajectories), 4)  # 4 players
        total = 0
        for payoff in payoffs:
            total += payoff
        self.assertEqual(total, 0)  # Zero-sum game

    def test_get_perfect_information(self):
        env = rlcard.make('hokm')
        _, player_id = env.reset()
        self.assertEqual(player_id, env.get_perfect_information()['current_player'])

    def test_multiplayers(self):
        env = rlcard.make('hokm')
        num_players = env.game.get_num_players()
        self.assertEqual(num_players, 4)  # Hokm is always 4 players


    def test_card_validation(self):
        env = rlcard.make('hokm')
        state, _ = env.reset()
        
        # Test card encoding/decoding
        card = env.game.get_player_hand(0)[0]  # Get first card from player's hand
        card_idx = env._card_to_idx(card)
        decoded_card = env._decode_action(card_idx)
        self.assertEqual(card.suit, decoded_card.suit)
        self.assertEqual(card.rank, decoded_card.rank)

    def test_state_shape(self):
        env = rlcard.make('hokm')
        state, _ = env.reset()
        
        # Test observation shape
        self.assertEqual(len(state['obs'].shape), 2)
        self.assertEqual(state['obs'].shape[0], 5)  # 5 features
        self.assertEqual(state['obs'].shape[1], 52)  # 52 cards