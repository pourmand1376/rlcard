import unittest
from rlcard.games.hokm.judger import HokmJudger
from rlcard.games.base import Card

class TestHokmJudger(unittest.TestCase):
    def setUp(self):
        self.judger = HokmJudger()

    def test_get_winner_basic(self):
        # Test when hokm is Hearts
        hokm = 'H'
        
        # Test when all cards are same suit (not hokm)
        played_cards = [
            Card('S', 'A'),  # Player 0
            Card('S', 'K'),  # Player 1
            Card('S', 'Q'),  # Player 2
            Card('S', '2'),  # Player 3
        ]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 0, "Highest card of same suit should win")

        # Test when hokm is played
        played_cards = [
            Card('S', 'A'),  # Player 0 plays Ace of Spades
            Card('H', '2'),  # Player 1 plays 2 of Hearts (hokm)
            Card('S', 'K'),  # Player 2 plays King of Spades
            Card('S', 'Q'),  # Player 3 plays Queen of Spades
        ]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 1, "Hokm should win over other suits")

        # Test when multiple hokm cards are played
        played_cards = [
            Card('H', '2'),  # Player 0 plays 2 of Hearts
            Card('H', 'A'),  # Player 1 plays Ace of Hearts
            Card('H', 'K'),  # Player 2 plays King of Hearts
            Card('H', 'Q'),  # Player 3 plays Queen of Hearts
        ]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 1, "Highest hokm card should win")

    def test_get_winner_edge_cases(self):
        hokm = 'H'
        
        # Test with empty list
        self.assertIsNone(self.judger.get_winner([], hokm))
        
        # Test with single card
        played_cards = [Card('S', 'A')]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 0)

    def test_get_payoffs(self):
        class MockPlayer:
            def __init__(self, score):
                self.my_score = score

        # Test when first team wins (players 0 and 2)
        players = [
            MockPlayer(7),  # Player 0 has 7 points
            MockPlayer(6),  # Player 1 has 6 points
            MockPlayer(7),  # Player 2 has 7 points
            MockPlayer(6),  # Player 3 has 6 points
        ]
        payoffs = self.judger.get_payoffs(players)
        self.assertEqual(payoffs, [1, -1, 1, -1])

        # Test when second team wins (players 1 and 3)
        players = [
            MockPlayer(6),  # Player 0 has 6 points
            MockPlayer(7),  # Player 1 has 7 points
            MockPlayer(6),  # Player 2 has 6 points
            MockPlayer(7),  # Player 3 has 7 points
        ]
        payoffs = self.judger.get_payoffs(players)
        self.assertEqual(payoffs, [-1, 1, -1, 1])

    def test_get_legal_actions(self):
        class MockPlayer:
            def __init__(self, hand):
                self.hand = hand

        # Test when table is empty (all cards are legal)
        player = MockPlayer([Card('H', 'A'), Card('S', 'K'), Card('D', '2')])
        table = []
        legal_actions = self.judger.get_legal_actions(player, table)
        self.assertEqual(len(legal_actions), 3)
        self.assertEqual(set(legal_actions), set(player.hand))

        # Test when player has cards matching the round suit
        player = MockPlayer([Card('H', 'A'), Card('S', 'K'), Card('S', '2')])
        table = [Card('S', 'Q')]  # Round suit is Spades
        legal_actions = self.judger.get_legal_actions(player, table)
        self.assertEqual(len(legal_actions), 2)
        self.assertTrue(all(card.suit == 'S' for card in legal_actions))

        # Test when player has no cards matching the round suit
        player = MockPlayer([Card('H', 'A'), Card('H', 'K'), Card('D', '2')])
        table = [Card('S', 'Q')]  # Round suit is Spades
        legal_actions = self.judger.get_legal_actions(player, table)
        self.assertEqual(len(legal_actions), 3)
        self.assertEqual(set(legal_actions), set(player.hand))

if __name__ == '__main__':
    unittest.main() 