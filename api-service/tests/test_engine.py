import pytest
from app.models import Card, Suit, Rank
from app.engine import Deck, Player, Trick, Hand


def test_deck_generation():
    deck = Deck()
    assert len(deck.cards) == 24
    # Check for 9s
    nines = [c for c in deck.cards if c.rank == Rank.NINE]
    assert len(nines) == 4


def test_deal():
    deck = Deck()
    hands = deck.deal()
    assert len(hands) == 4
    for hand in hands:
        assert len(hand) == 5


def test_trick_legal_moves():
    trump = Suit.HEARTS
    active_seats = [0, 1, 2, 3]
    trick = Trick(leader_id=0, trump_suit=trump, active_seats=active_seats)

    # Player 0 leads 9 of Diamonds
    player0_hand = [Card(Suit.DIAMONDS, Rank.NINE)]
    trick.play_card(0, player0_hand[0], player0_hand)

    assert trick.lead_suit == Suit.DIAMONDS

    # Player 1 has a Diamond and must play it
    player1_hand = [Card(Suit.DIAMONDS, Rank.ACE), Card(Suit.SPADES, Rank.TEN)]
    with pytest.raises(ValueError):
        trick.play_card(1, Card(Suit.SPADES, Rank.TEN), player1_hand)

    trick.play_card(1, Card(Suit.DIAMONDS, Rank.ACE), player1_hand)


def test_left_bower_legal_move():
    trump = Suit.HEARTS
    active_seats = [0, 1, 2, 3]
    trick = Trick(leader_id=0, trump_suit=trump, active_seats=active_seats)

    # Player 0 leads King of Hearts (Trump)
    player0_hand = [Card(Suit.HEARTS, Rank.KING)]
    trick.play_card(0, player0_hand[0], player0_hand)

    assert trick.lead_suit == Suit.HEARTS

    # Player 1 has Jack of Diamonds (Left Bower)
    # They MUST play it if it's their only trump
    player1_hand = [Card(Suit.DIAMONDS, Rank.JACK), Card(Suit.SPADES, Rank.TEN)]

    with pytest.raises(ValueError):
        trick.play_card(1, Card(Suit.SPADES, Rank.TEN), player1_hand)

    trick.play_card(1, Card(Suit.DIAMONDS, Rank.JACK), player1_hand)


def test_trick_winner():
    trump = Suit.HEARTS
    active_seats = [0, 1, 2, 3]
    trick = Trick(leader_id=0, trump_suit=trump, active_seats=active_seats)

    # P0 leads 9 of Hearts
    # P1 plays Ace of Hearts
    # P2 plays Jack of Diamonds (Left Bower)
    # P3 plays Jack of Hearts (Right Bower)

    trick.play_card(0, Card(Suit.HEARTS, Rank.NINE), [])
    trick.play_card(1, Card(Suit.HEARTS, Rank.ACE), [])
    trick.play_card(2, Card(Suit.DIAMONDS, Rank.JACK), [])
    trick.play_card(3, Card(Suit.HEARTS, Rank.JACK), [])

    assert trick.get_winner() == 3


def test_no_trump_trick_winner():
    # No trump suit
    trump = None
    active_seats = [0, 1, 2, 3]
    trick = Trick(leader_id=0, trump_suit=trump, active_seats=active_seats)

    # P0 leads 10 of Clubs
    # P1 plays Ace of Clubs
    # P2 plays Jack of Spades (Not a bower in No Trump!)
    # P3 plays 9 of Clubs

    trick.play_card(0, Card(Suit.CLUBS, Rank.TEN), [])
    trick.play_card(1, Card(Suit.CLUBS, Rank.ACE), [])
    trick.play_card(2, Card(Suit.SPADES, Rank.JACK), [])
    trick.play_card(3, Card(Suit.CLUBS, Rank.NINE), [])

    # Ace of Clubs should win. Jack of Spades is off-suit and not trump.
    assert trick.get_winner() == 1


def test_no_trump_lead_suit_matters():
    trump = None
    active_seats = [0, 1, 2, 3]
    trick = Trick(leader_id=0, trump_suit=trump, active_seats=active_seats)

    # P0 leads 9 of Diamonds
    # P1 plays Ace of Hearts
    # P2 plays Ace of Spades
    # P3 plays 10 of Diamonds

    trick.play_card(0, Card(Suit.DIAMONDS, Rank.NINE), [])
    trick.play_card(1, Card(Suit.HEARTS, Rank.ACE), [])
    trick.play_card(2, Card(Suit.SPADES, Rank.ACE), [])
    trick.play_card(3, Card(Suit.DIAMONDS, Rank.TEN), [])

    # 10 of Diamonds should win because it's the highest lead suit card
    assert trick.get_winner() == 3


def test_hand_alone_mode():
    players = [Player(f"P{i}", i) for i in range(4)]
    # P0 goes alone. Partner is P2.
    hand = Hand(players, dealer_id=3, trump_suit=Suit.HEARTS, maker_id=0, alone=True)

    assert hand.active_seats == [0, 1, 3]

    trick = hand.start_trick(leader_id=1)
    assert trick.active_seats == [0, 1, 3]

    # Try to play for P2 (partner)
    with pytest.raises(ValueError):
        trick.play_card(2, Card(Suit.HEARTS, Rank.ACE), [])

    # Valid plays
    trick.play_card(1, Card(Suit.CLUBS, Rank.NINE), [])
    trick.play_card(3, Card(Suit.CLUBS, Rank.TEN), [])
    trick.play_card(0, Card(Suit.CLUBS, Rank.ACE), [])

    assert trick.get_winner() == 0

    # Test scoring for alone march
    for _ in range(5):
        hand.record_trick_winner(0)

    scores = hand.get_hand_score()
    assert scores[0] == 4
    assert scores[1] == 0


def test_hand_scoring():
    players = [Player(f"P{i}", i) for i in range(4)]
    hand = Hand(players, dealer_id=3, trump_suit=Suit.HEARTS, maker_id=0)

    # Maker team (0) wins 3 tricks
    hand.record_trick_winner(0)
    hand.record_trick_winner(2)
    hand.record_trick_winner(0)
    # Defending team (1) wins 2 tricks
    hand.record_trick_winner(1)
    hand.record_trick_winner(3)

    scores = hand.get_hand_score()
    assert scores[0] == 1
    assert scores[1] == 0


def test_hand_scoring_march():
    players = [Player(f"P{i}", i) for i in range(4)]
    hand = Hand(players, dealer_id=3, trump_suit=Suit.HEARTS, maker_id=0)

    # Maker team wins all 5
    for _ in range(5):
        hand.record_trick_winner(0)

    scores = hand.get_hand_score()
    assert scores[0] == 2
    assert scores[1] == 0


def test_hand_scoring_euchred():
    players = [Player(f"P{i}", i) for i in range(4)]
    hand = Hand(players, dealer_id=3, trump_suit=Suit.HEARTS, maker_id=0)

    # Defending team (1) wins 3 tricks
    hand.record_trick_winner(1)
    hand.record_trick_winner(3)
    hand.record_trick_winner(1)
    # Maker team (0) wins 2
    hand.record_trick_winner(0)
    hand.record_trick_winner(2)

    scores = hand.get_hand_score()
    assert scores[0] == 0
    assert scores[1] == 2
