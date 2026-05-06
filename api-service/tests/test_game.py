from app.models import Suit, Card
from app.game import Game


def test_game_initialization():
    player_names = ["Alice", "Bob", "Charlie", "David"]
    game = Game(player_names)

    assert len(game.players) == 4
    assert game.players[0].name == "Alice"
    assert game.team_scores == {0: 0, 1: 0}
    assert game.dealer_id == 0


def test_game_start_hand():
    player_names = ["Alice", "Bob", "Charlie", "David"]
    game = Game(player_names)

    hands, turned_up = game.start_new_hand()

    assert len(hands) == 4
    assert len(game.players[0].hand) == 5
    assert isinstance(turned_up, Card)
    assert game.current_bidding is not None


def test_game_full_hand_flow():
    player_names = ["Alice", "Bob", "Charlie", "David"]
    game = Game(player_names, win_threshold=5)

    # Hand 1
    game.start_new_hand()
    game.set_trump(maker_id=0, suit=Suit.HEARTS)

    # Simulate winning 5 tricks for team 0
    for _ in range(5):
        game.current_hand.record_trick_winner(0)

    hand_points = game.finish_hand()
    assert hand_points[0] == 2
    assert game.team_scores[0] == 2
    assert game.dealer_id == 1
    assert game.is_over is False

    # Hand 2 - P1 is dealer
    game.start_new_hand()
    game.set_trump(maker_id=1, suit=Suit.SPADES, alone=True)

    # P1 wins all 5
    for _ in range(5):
        game.current_hand.record_trick_winner(1)

    game.finish_hand()
    assert game.team_scores[1] == 4
    assert game.dealer_id == 2
    assert game.is_over is False

    # Hand 3 - P2 is dealer
    game.start_new_hand()
    game.set_trump(maker_id=2, suit=Suit.DIAMONDS)
    for _ in range(5):
        game.current_hand.record_trick_winner(2)

    game.finish_hand()
    assert game.team_scores[0] == 2 + 2  # 4
    assert game.is_over is False

    # Hand 4 - P3 is dealer, Team 0 wins game
    game.start_new_hand()
    game.set_trump(maker_id=0, suit=Suit.CLUBS)
    for _ in range(5):
        game.current_hand.record_trick_winner(0)

    game.finish_hand()
    assert game.team_scores[0] == 6
    assert game.is_over is True
