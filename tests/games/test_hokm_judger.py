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
            def __init__(self, score, is_hakem=False):
                self.my_team_score = score
                self._is_hakem = is_hakem
                
            def is_hakem_team(self):
                return self._is_hakem

        # Test regular win (not 7-0) for hakem team
        players = [
            MockPlayer(5, True),   # Player 0: hakem team
            MockPlayer(2, False),  # Player 1
            MockPlayer(5, True),   # Player 2: hakem team
            MockPlayer(2, False),  # Player 3
        ]
        payoffs = self.judger.get_payoffs(players)
        self.assertEqual(payoffs, [1, -1, 1, -1], "Regular win should have 1x multiplier")

        # Test 7-0 win for hakem team (2x multiplier)
        players = [
            MockPlayer(7, True),   # Player 0: hakem team
            MockPlayer(0, False),  # Player 1
            MockPlayer(7, True),   # Player 2: hakem team
            MockPlayer(0, False),  # Player 3
        ]
        payoffs = self.judger.get_payoffs(players)
        self.assertEqual(payoffs, [2, -2, 2, -2], "7-0 win by hakem team should give 2x payoff")

        # Test 7-0 win for non-hakem team (3x multiplier)
        players = [
            MockPlayer(0, True),   # Player 0: hakem team
            MockPlayer(7, False),  # Player 1
            MockPlayer(0, True),   # Player 2: hakem team
            MockPlayer(7, False),  # Player 3
        ]
        payoffs = self.judger.get_payoffs(players)
        self.assertEqual(payoffs, [-3, 3, -3, 3], "7-0 win by non-hakem team should give 3x payoff")

        # Test regular win (not 7-0) for non-hakem team
        players = [
            MockPlayer(3, True),   # Player 0: hakem team
            MockPlayer(4, False),  # Player 1
            MockPlayer(3, True),   # Player 2: hakem team
            MockPlayer(4, False),  # Player 3
        ]
        payoffs = self.judger.get_payoffs(players)
        self.assertEqual(payoffs, [-1, 1, -1, 1], "Regular win should have 1x multiplier")

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
        
        # Test with only one card in hand
        player = MockPlayer([Card('H', 'A')])
        table = [Card('S', 'Q')]  # Round suit is Spades, doesn't match player's card
        legal_actions = self.judger.get_legal_actions(player, table)
        self.assertEqual(len(legal_actions), 1)
        self.assertEqual(legal_actions[0], Card('H', 'A'))
        
        # Test with empty hand
        player = MockPlayer([])
        table = [Card('S', 'Q')]
        legal_actions = self.judger.get_legal_actions(player, table)
        self.assertEqual(len(legal_actions), 0)

    def test_get_winner_detailed(self):
        # Test when hokm is Hearts
        hokm = 'H'
        
        # Test when round suit is followed and no hokm is played
        played_cards = [
            Card('S', 'A'),  # Player 0
            Card('S', '2'),  # Player 1
            Card('S', 'K'),  # Player 2
            Card('S', 'Q'),  # Player 3
        ]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 0, "Highest card of round suit should win")
        
        # Test when hokm beats round suit
        played_cards = [
            Card('S', 'A'),  # Player 0
            Card('H', '2'),  # Player 1 - Hokm
            Card('S', 'K'),  # Player 2
            Card('H', '3'),  # Player 3 - Hokm but played later
        ]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 3, "Highest hokm card should win")
        
        # Test when multiple hokm cards are played with different values
        played_cards = [
            Card('S', 'A'),  # Player 0
            Card('H', '2'),  # Player 1 - Hokm low
            Card('S', 'K'),  # Player 2
            Card('H', 'A'),  # Player 3 - Hokm high
        ]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 3, "Highest hokm card should win")
        
        # Test when round suit is hokm
        played_cards = [
            Card('H', '2'),  # Player 0
            Card('H', 'K'),  # Player 1
            Card('H', 'A'),  # Player 2
            Card('H', 'Q'),  # Player 3
        ]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 2, "Highest card of hokm suit should win")
        
        # Test with only one card
        played_cards = [Card('S', 'A')]
        winner = self.judger.get_winner(played_cards, hokm)
        self.assertEqual(winner, 0, "Single card should win")

if __name__ == '__main__':
    unittest.main()