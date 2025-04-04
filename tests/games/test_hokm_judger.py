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
                self.my_score = score
                self._is_hakem = is_hakem
                self.hokm = 'H'
                
            def is_hakem_team(self):
                return self._is_hakem

        # Test when first team wins (players 0 and 2) - normal case
        players = [
            MockPlayer(7, True),  # Player 0 has 7 points, hakem team
            MockPlayer(6, False),  # Player 1 has 6 points
            MockPlayer(7, True),  # Player 2 has 7 points, hakem team
            MockPlayer(6, False),  # Player 3 has 6 points
        ]
        cards_history = []
        payoffs = self.judger.get_payoffs(players, cards_history)
        self.assertEqual(payoffs, [1, -1, 1, -1], "Normal win should give 1/-1 payoffs")

        # Test when second team wins (players 1 and 3) - normal case
        players = [
            MockPlayer(6, False),  # Player 0 has 6 points
            MockPlayer(7, True),   # Player 1 has 7 points, hakem team
            MockPlayer(6, False),  # Player 2 has 6 points
            MockPlayer(7, True),   # Player 3 has 7 points, hakem team
        ]
        cards_history = []
        payoffs = self.judger.get_payoffs(players, cards_history)
        self.assertEqual(payoffs, [-1, 1, -1, 1], "Normal win should give 1/-1 payoffs")
        
        # Test traditional scoring
        players = [
            MockPlayer(7, True),  # Player 0 has 7 points
            MockPlayer(6, False), # Player 1 has 6 points
            MockPlayer(7, True),  # Player 2 has 7 points
            MockPlayer(6, False), # Player 3 has 6 points
        ]
        cards_history = []
        payoffs = self.judger.get_payoffs(players, cards_history, use_traditional_scoring=True)
        self.assertEqual(payoffs, [1, 0, 1, 0], "Traditional scoring should give winners points, losers 0")

        # Test first 7 consecutive hands as hakem (2x multiplier)
        players = [
            MockPlayer(7, True),   # Player 0 has 7 points, hakem team
            MockPlayer(6, False),  # Player 1 has 6 points
            MockPlayer(7, True),   # Player 2 has 7 points, hakem team
            MockPlayer(6, False),  # Player 3 has 6 points
        ]
        # Create history where team 0,2 wins first 7 hands
        cards_history = [
            [Card('H', 'A'), Card('S', '2'), Card('D', '3'), Card('C', '4')],  # Player 0 wins with hokm
            [Card('S', 'A'), Card('S', '2'), Card('S', '3'), Card('S', '4')],  # Player 0 wins with high card
            [Card('D', 'K'), Card('D', '2'), Card('D', 'A'), Card('D', '4')],  # Player 2 wins with high card
            [Card('H', '2'), Card('S', '5'), Card('D', '7'), Card('C', '9')],  # Player 0 wins with hokm
            [Card('S', 'K'), Card('S', '2'), Card('S', 'Q'), Card('S', '4')],  # Player 0 wins with high card
            [Card('C', 'A'), Card('C', '2'), Card('C', '3'), Card('C', '4')],  # Player 0 wins with high card
            [Card('H', '5'), Card('S', '2'), Card('D', '3'), Card('C', '4')],  # Player 0 wins with hokm
        ]
        payoffs = self.judger.get_payoffs(players, cards_history)
        self.assertEqual(payoffs, [2, -2, 2, -2], "First 7 consecutive hands as hakem should give 2x payoffs")

        # Test first 7 consecutive hands as non-hakem (3x multiplier)
        players = [
            MockPlayer(6, True),  # Player 0 has 6 points
            MockPlayer(7, False),   # Player 1 has 7 points, hakem team
            MockPlayer(6, True),  # Player 2 has 6 points
            MockPlayer(7, False),   # Player 3 has 7 points, hakem team
        ]
        # Create history where team 1,3 wins first 7 hands but they are not hakem
        cards_history = [
            [Card('S', '2'), Card('H', 'A'), Card('D', '3'), Card('C', '4')],  # Player 1 wins with hokm
            [Card('S', '2'), Card('S', 'A'), Card('S', '3'), Card('S', '4')],  # Player 1 wins with high card
            [Card('D', '2'), Card('D', 'K'), Card('D', '3'), Card('D', 'A')],  # Player 3 wins with high card
            [Card('S', '5'), Card('H', '2'), Card('D', '7'), Card('C', '9')],  # Player 1 wins with hokm
            [Card('S', '2'), Card('S', 'K'), Card('S', 'Q'), Card('S', '4')],  # Player 1 wins with high card
            [Card('C', '2'), Card('C', 'A'), Card('C', '3'), Card('C', '4')],  # Player 1 wins with high card
            [Card('S', '2'), Card('H', '5'), Card('D', '3'), Card('C', '4')],  # Player 1 wins with hokm
        ]
        payoffs = self.judger.get_payoffs(players, cards_history)
        self.assertEqual(payoffs, [-3, 3, -3, 3], "First 7 consecutive hands should give 2x payoffs")
        
        # Test when no team has first 7 consecutive hands
        players = [
            MockPlayer(7, True),   # Player 0 has 7 points
            MockPlayer(6, False),  # Player 1 has 6 points
            MockPlayer(7, True),   # Player 2 has 7 points
            MockPlayer(6, False),  # Player 3 has 6 points
        ]
        # Create history where teams alternate winning hands
        cards_history = [
            [Card('H', 'A'), Card('S', '2'), Card('D', '3'), Card('C', '4')],  # Player 0 wins
            [Card('S', '2'), Card('S', 'A'), Card('S', '3'), Card('S', '4')],  # Player 1 wins
            [Card('D', 'K'), Card('D', '2'), Card('D', 'A'), Card('D', '4')],  # Player 2 wins
            [Card('S', '2'), Card('H', '2'), Card('D', '7'), Card('C', '9')],  # Player 1 wins
            [Card('S', 'K'), Card('S', '2'), Card('S', 'Q'), Card('S', '4')],  # Player 0 wins
            [Card('C', '2'), Card('C', 'A'), Card('C', '3'), Card('C', '4')],  # Player 1 wins
            [Card('H', '5'), Card('S', '2'), Card('D', '3'), Card('C', '4')],  # Player 0 wins
        ]
        payoffs = self.judger.get_payoffs(players, cards_history)
        self.assertEqual(payoffs, [1, -1, 1, -1], "Without 7 consecutive wins, normal payoffs apply")

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