import pytest
from app.models import Card, Suit, Rank
from app.bidding import Bidding, BidPhase


def test_bidding_round_1_order_up():
    turned_up = Card(Suit.HEARTS, Rank.NINE)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up)

    # P0 (left of dealer) orders it up
    assert bidding.call(0, Suit.HEARTS) is True
    assert bidding.trump_suit == Suit.HEARTS
    assert bidding.maker_id == 0
    assert bidding.phase == BidPhase.DEALER_DISCARD
    assert bidding.current_bidder == 3 # Dealer's turn to discard


def test_bidding_round_1_pass_to_round_2():
    turned_up = Card(Suit.HEARTS, Rank.NINE)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up)

    # All pass round 1
    assert bidding.call(0, None) is False
    assert bidding.call(1, None) is False
    assert bidding.call(2, None) is False
    assert bidding.call(3, None) is False

    assert bidding.phase == BidPhase.ROUND_2
    assert bidding.current_bidder == 0


def test_bidding_round_1_no_trump_fails():
    turned_up = Card(Suit.HEARTS, Rank.NINE)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up)

    # Cannot call No Trump in Round 1
    with pytest.raises(ValueError, match="No Trump can only be called in Round 2"):
        bidding.call(0, None, is_no_trump=True)


def test_bidding_round_2_no_trump():
    turned_up = Card(Suit.HEARTS, Rank.NINE)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up)

    # Pass round 1
    for i in range(4):
        bidding.call((3 + 1 + i) % 4, None)

    # P0 calls No Trump
    assert bidding.call(0, None, is_no_trump=True) is True
    assert bidding.is_no_trump is True
    assert bidding.trump_suit is None
    assert bidding.maker_id == 0
    assert bidding.phase == BidPhase.COMPLETED


def test_bidding_round_2_call_suit():
    turned_up = Card(Suit.HEARTS, Rank.NINE)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up)

    # Pass round 1
    for i in range(4):
        bidding.call((3 + 1 + i) % 4, None)

    # P0 passes round 2
    bidding.call(0, None)

    # P1 calls Spades
    assert bidding.call(1, Suit.SPADES) is True
    assert bidding.trump_suit == Suit.SPADES
    assert bidding.maker_id == 1


def test_bidding_round_2_invalid_suit():
    turned_up = Card(Suit.HEARTS, Rank.NINE)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up)

    # Pass round 1
    for i in range(4):
        bidding.call((3 + 1 + i) % 4, None)

    # P0 tries to call Hearts (which was turned down)
    with pytest.raises(ValueError):
        bidding.call(0, Suit.HEARTS)


def test_screw_the_dealer():
    turned_up = Card(Suit.HEARTS, Rank.NINE)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up, screw_the_dealer=True)

    # Pass round 1
    for i in range(4):
        bidding.call((3 + 1 + i) % 4, None)

    # P0, P1, P2 pass round 2
    bidding.call(0, None)
    bidding.call(1, None)
    bidding.call(2, None)

    # P3 (dealer) tries to pass, but MUST call
    with pytest.raises(ValueError):
        bidding.call(3, None)

    assert bidding.call(3, Suit.CLUBS) is True
    assert bidding.trump_suit == Suit.CLUBS
