import json
from app.models import Card, Suit, Rank
from app.bidding import Bidding, BidPhase
from app.game import Game


def test_card_serialization():
    card = Card(Suit.HEARTS, Rank.ACE)
    data = card.to_dict()
    assert data == {"suit": "HEARTS", "rank": 14}

    new_card = Card.from_dict(data)
    assert new_card == card


def test_bidding_serialization():
    turned_up = Card(Suit.SPADES, Rank.JACK)
    bidding = Bidding(dealer_id=3, turned_up_card=turned_up)
    bidding.call(0, None)  # Pass

    data = bidding.to_dict()
    new_bidding = Bidding.from_dict(data)

    assert new_bidding.dealer_id == 3
    assert new_bidding.phase == BidPhase.ROUND_1
    assert new_bidding.current_bidder == 1
    assert new_bidding.turned_up_card == turned_up


def test_game_serialization():
    player_names = ["Alice", "Bob", "Charlie", "David"]
    game = Game(player_names)
    game.start_new_hand()
    game.set_trump(maker_id=0, suit=Suit.HEARTS)

    data = game.to_dict()
    # Simulate JSON roundtrip
    json_data = json.loads(json.dumps(data))

    new_game = Game.from_dict(json_data)

    assert new_game.win_threshold == 2

    assert len(new_game.players) == 4
    assert new_game.players[0].name == "Alice"
    assert new_game.current_hand is not None
    assert new_game.current_hand.trump_suit == Suit.HEARTS
    assert new_game.current_hand.maker_id == 0
    assert len(new_game.deck.cards) == 24
