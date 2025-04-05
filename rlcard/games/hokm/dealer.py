from rlcard.games.base import Card

class HokmDealer:
    ''' Dealer class for Hokm
    '''
    def __init__(self, np_random):
        ''' Initialize a Hokm dealer

        Args:
            np_random: numpy random state
        '''
        self.np_random = np_random
        self.deck = []
        self.reset()

    def reset(self):
        ''' Reset the deck
        '''
        self.deck = []
        for suit in ['S', 'H', 'D', 'C']:
            for rank in ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']:
                self.deck.append(Card(suit, rank))
        self.shuffle()

    def shuffle(self):
        ''' Shuffle the deck
        '''
        self.np_random.shuffle(self.deck)

    def deal_cards(self, num):
        ''' Deal cards to players

        Args:
            num (int): Number of cards to deal

        Returns:
            list: List of dealt cards
        '''
        dealt_cards = []
        for _ in range(num):
            dealt_cards.append(self.deck.pop())
        return dealt_cards

    def deal_initial_cards(self):
        ''' Deal 13 cards to each player
        
        Returns:
            dict: Dictionary with cards for each player {player_id: [cards]}
        '''
        dealt_cards = {}
        for player_id in range(4):
            dealt_cards[player_id] = self.deal_cards(13)
        return dealt_cards

    def get_deck(self):
        ''' Get the current deck

        Returns:
            list: List of cards in the deck
        '''
        return self.deck