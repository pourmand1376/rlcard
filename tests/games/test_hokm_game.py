import unittest
import numpy as np
from rlcard.games.hokm.game import HokmGame
from rlcard.games.base import Card

class TestHokmGame(unittest.TestCase):

    def setUp(self):
        self.game = HokmGame()
        self.game.init_game()

    def test_init_game(self):
        """Test game initialization"""
        self.assertEqual(len(self.game.players), 4)
        
        # Check each player has 13 cards
        for player in self.game.players:
            self.assertEqual(len(player.get_hand()), 13)
        
        # Check all cards are unique
        all_cards = []
        for player in self.game.players:
            all_cards.extend(player.get_hand())
        self.assertEqual(len(all_cards), 52)
        self.assertEqual(len(set([(c.suit, c.rank) for c in all_cards])), 52)

    def test_hakem_selection(self):
        """Test hakem selection and initial state"""
        state = self.game.init_game()
        hakem = state['hakem']
        
        self.assertIsNotNone(hakem)
        self.assertTrue(0 <= hakem < 4)
        self.assertEqual(self.game.current_player, hakem)

    def test_step(self):
        """Test game step"""
        state = self.game.init_game()
        current_player = state['current_player']
        
        # Take a legal action
        legal_actions = self.game.get_legal_actions()
        action = legal_actions[0]
        
        next_state, next_player, round_over, _ = self.game.step(action)
        
        # Verify the card was played
        self.assertEqual(len(self.game.table), 1)
        self.assertEqual(next_player, (current_player + 1) % 4)
        self.assertFalse(round_over)

    def test_complete_round(self):
        """Test completing a full round"""
        self.game.init_game()
        self.game.hokm = 'H'  # Set hokm for testing
        
        # Play 4 cards
        for _ in range(4):
            legal_actions = self.game.get_legal_actions()
            action = legal_actions[0]
            _, _, round_over, _ = self.game.step(action)
        
        # Verify round completion
        self.assertTrue(round_over)
        self.assertEqual(len(self.game.table), 0)  # Table should be cleared
        self.assertEqual(len(self.game.round_history), 1)  # One round in history

    def test_scoring(self):
        """Test score updates"""
        state = self.game.init_game()
        current_player = state['current_player']
        initial_scores = [p.my_team_score for p in self.game.players]
        
        # Get actual cards from player's hand
        hand = self.game.players[current_player].get_hand()
        # Play first card from hand
        action = hand[0]
        self.game.step(action)
        
        # Complete the round with legal cards from other players
        for i in range(3):
            next_player = (current_player + i + 1) % 4
            legal_actions = self.game.get_legal_actions()
            self.game.step(legal_actions[0])
            
        # Check score updates
        final_scores = [p.my_team_score for p in self.game.players]
        self.assertNotEqual(final_scores, initial_scores)  # Scores should change

    def test_game_over(self):
        """Test game over condition"""
        self.game.init_game()
        
        # Set a player's score to 7 (winning score)
        self.game.players[0].my_team_score = 7
        
        self.assertTrue(self.game.is_over())

    def test_deal_cards(self):
        """Test card dealing functionality"""
        state = self.game.init_game()
        
        # Test initial deal
        for player in self.game.players:
            # Each player should have 13 cards
            self.assertEqual(len(player.get_hand()), 13)
            
        # Test no duplicate cards
        all_cards = []
        for player in self.game.players:
            hand = player.get_hand()
            for card in hand:
                card_tuple = (card.suit, card.rank)
                self.assertNotIn(card_tuple, all_cards)
                all_cards.append(card_tuple)

    def test_hokm_selection(self):
        """Test hokm suit selection"""
        state = self.game.init_game()
        hakem = state['hakem']
        
        # Test hokm selection
        test_hokm = 'H'
        self.game.set_hokm(test_hokm)
        
        # Verify hokm is set correctly
        self.assertEqual(self.game.hokm, test_hokm)
        for player in self.game.players:
            self.assertEqual(player.hokm, test_hokm)

    def test_legal_actions(self):
        """Test legal actions in different scenarios"""
        state = self.game.init_game()
        
        # Test initial play (all cards should be legal)
        initial_legal_actions = self.game.get_legal_actions()
        self.assertEqual(len(initial_legal_actions), len(self.game.players[self.game.current_player].get_hand()))
        
        # Test following suit requirement
        self.game.table = [Card('S', 'A')]  # First card is Ace of Spades
        current_player = self.game.current_player
        hand = self.game.players[current_player].get_hand()
        
        # Find cards of spades in hand
        spades_in_hand = [card for card in hand if card.suit == 'S']
        if spades_in_hand:
            legal_actions = self.game.get_legal_actions()
            self.assertEqual(len(legal_actions), len(spades_in_hand))
            for action in legal_actions:
                self.assertEqual(action.suit, 'S')

    def test_trick_winner(self):
        """Test trick winner determination with different scenarios"""
        state = self.game.init_game()
        self.game.hokm = 'H'  # Set Hearts as hokm
        
        # Play a round with actual cards from players' hands
        current_player = state['current_player']
        # Play first card from current player's hand
        action = self.game.players[current_player].get_hand()[0]
        self.game.step(action)
        
        # Complete the round with legal cards
        for i in range(3):
            legal_actions = self.game.get_legal_actions()
            self.game.step(legal_actions[0])
        
        # Check round is properly completed
        self.assertEqual(len(self.game.table), 0)  # Table should be cleared
        self.assertEqual(len(self.game.round_history), 1)  # One round in history

    def test_game_scoring(self):
        """Test game scoring system"""
        self.game.init_game()
        
        # Remember who hakem is and ensure proper team scoring
        winner_id = self.game.hakem
        partner_id = (winner_id + 2) % 4

        # Simulate 7-0 win for hakem team
        self.game.players[winner_id].my_team_score = 7
        self.game.players[partner_id].my_team_score = 7
        self.game.players[(winner_id + 1) % 4].my_team_score = 0
        self.game.players[(winner_id + 3) % 4].my_team_score = 0

        # Test payoffs should be 2x for hakem team winning 7-0
        payoffs = self.game.get_payoffs()
        self.assertEqual(payoffs[winner_id], 2)
        self.assertEqual(payoffs[partner_id], 2)
        self.assertEqual(payoffs[(winner_id + 1) % 4], -2)
        self.assertEqual(payoffs[(winner_id + 3) % 4], -2)

    def test_team_scoring_scenarios(self):
        """Test various team scoring scenarios"""
        self.game.init_game()
        hakem_id = self.game.hakem

        # Test scenario 1: Regular win (not 7-0)
        self.game.players[0].my_team_score = 5
        self.game.players[2].my_team_score = 5
        self.game.players[1].my_team_score = 2
        self.game.players[3].my_team_score = 2

        payoffs = self.game.get_payoffs()
        self.assertEqual(payoffs, [1, -1, 1, -1], "Regular win should give 1x payoff")

        # Test scenario 2: 7-0 win
        self.game.init_game()  # Reset game state
        
        # Set scores for 7-0 win by team 0
        self.game.players[0].my_team_score = 7
        self.game.players[2].my_team_score = 7
        self.game.players[1].my_team_score = 0
        self.game.players[3].my_team_score = 0

        payoffs = self.game.get_payoffs()
        multiplier = 2 if 0 == hakem_id or 2 == hakem_id else 3
        self.assertEqual(payoffs, [multiplier, -multiplier, multiplier, -multiplier])

    def test_step_back(self):
        """Test step back functionality"""
        self.game = HokmGame(allow_step_back=True)
        state = self.game.init_game()
        
        # Get an actual card from player's hand
        current_player = state['current_player']
        initial_hand = self.game.players[current_player].get_hand().copy()
        action = initial_hand[0]
        
        # Take a step
        self.game.step(action)
        
        # Step back
        self.assertTrue(self.game.step_back())
        
        # Verify state is restored
        current_hand = self.game.players[current_player].get_hand()
        self.assertEqual(len(current_hand), len(initial_hand))
        self.assertEqual(sorted([(c.suit, c.rank) for c in current_hand]), 
                        sorted([(c.suit, c.rank) for c in initial_hand]))

    def test_round_completion(self):
        """Test full round completion and history tracking"""
        self.game.init_game()
        initial_round_count = len(self.game.round_history)
        
        # Play a complete round
        for _ in range(4):
            legal_actions = self.game.get_legal_actions()
            _, _, round_over, _ = self.game.step(legal_actions[0])
        
        # Verify round was recorded
        self.assertEqual(len(self.game.round_history), initial_round_count + 1)
        self.assertEqual(len(self.game.table), 0)  # Table should be cleared

    def test_complex_trick_scenarios(self):
        """Test more complex trick winning scenarios"""
        self.game.init_game()
        self.game.hokm = 'H'  # Set Hearts as hokm

        # Test case 1: Hokm beats high card
        self.game.table = [
            Card('S', 'A'),  # High non-hokm
            Card('H', '2'),  # Low hokm
            Card('S', 'K'),
            Card('S', 'Q')
        ]
        winner = self.game.judger.get_winner(self.game.table, self.game.hokm)
        self.assertEqual(winner, 1)  # Low hokm should win

        # Test case 2: Highest hokm wins among multiple hokm
        self.game.table = [
            Card('H', '7'),
            Card('H', 'K'),
            Card('H', '2'),
            Card('H', 'A')
        ]
        winner = self.game.judger.get_winner(self.game.table, self.game.hokm)
        self.assertEqual(winner, 3)  # Ace of hokm should win

    def test_team_scoring_scenarios(self):
        """Test various team scoring scenarios"""
        self.game.init_game()
        
        # Test scenario 1: Team 0 wins all tricks
        for _ in range(7):
            self.game.players[0].update_score(True)
            self.game.players[2].update_score(True)
        
        # Check team scores
        self.assertEqual(self.game.players[0].my_team_score, 7)
        self.assertEqual(self.game.players[2].my_team_score, 7)
        self.assertEqual(self.game.players[1].my_team_score, 0)
        self.assertEqual(self.game.players[3].my_team_score, 0)

        # Test payoffs in this scenario
        payoffs = self.game.get_payoffs()
        self.assertEqual(payoffs, [1, -1, 1, -1])

    def test_invalid_moves(self):
        """Test handling of invalid moves"""
        state = self.game.init_game()
        current_player = state['current_player']
        
        # Set up a scenario where player must follow suit
        first_player_hand = self.game.players[current_player].hand
        spade_card = next(card for card in first_player_hand if card.suit == 'S')
        self.game.table = [spade_card]
        
        # Get cards of other suits from player's hand
        other_suit_cards = [card for card in first_player_hand if card.suit != 'S']
        
        # Verify only spades are legal when having spades
        legal_actions = self.game.get_legal_actions()
        for action in legal_actions:
            self.assertEqual(action.suit, 'S')

    def test_full_game_simulation(self):
        """Simulate a full game and verify game mechanics"""
        self.game.init_game()
        rounds_played = 0
        tricks_won = {0: 0, 1: 0, 2: 0, 3: 0}
        max_rounds = 13  # Maximum possible rounds in a game
        
        while not self.game.is_over() and rounds_played < max_rounds:
            current_player = self.game.current_player
            legal_actions = self.game.get_legal_actions()
            
            # Break if no legal actions or player has no cards
            if not legal_actions or not self.game.players[current_player].hand:
                break
                
            action = legal_actions[0]
            _, next_player, round_over, info = self.game.step(action)
            
            if round_over:
                rounds_played += 1
                if info and 'winner' in info:
                    tricks_won[info['winner']] += 1
        
        # Verify reasonable game completion
        self.assertGreater(rounds_played, 0)
        self.assertLessEqual(rounds_played, max_rounds)
        total_tricks = sum(tricks_won.values())
        self.assertLessEqual(total_tricks, max_rounds)

    def test_hokm_selection_strategy(self):
        """Test the hokm selection strategy"""
        for _ in range(5):  # Test multiple games
            state = self.game.init_game()
            hakem = state['hakem']
            
            # Verify hakem's hand has at least 5 cards when selecting hokm
            hakem_hand = self.game.players[hakem].get_hand()
            self.assertGreaterEqual(len(hakem_hand), 5)
            
            # Verify selected hokm is valid
            self.assertIn(self.game.hokm, ['S', 'H', 'D', 'C'])
            
            # Verify all players know the hokm
            for player in self.game.players:
                self.assertEqual(player.hokm, self.game.hokm)

if __name__ == '__main__':
    unittest.main()
