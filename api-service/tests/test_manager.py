import pytest
import json
from unittest.mock import AsyncMock, patch
from app.manager import LobbyManager
from app.game import Game
from app.models import Suit, Card, Rank
from app.bidding import Bidding

@pytest.fixture
def lobby_manager():
    return LobbyManager()

@pytest.fixture
def game():
    player_names = ["Alice", "Bob", "Charlie", "David"]
    g = Game(player_names)
    g.start_new_hand()
    return g

@pytest.mark.anyio
async def test_get_game_state_json_filters_hand(lobby_manager, game):
    with patch("app.db.redis_client.client", new_callable=AsyncMock) as mock_redis:
        mock_redis.hgetall.return_value = {}
        # Check that Alice (seat 0) only sees her own cards
        state = await lobby_manager.get_game_state_json(game, 0)
        
        assert state["my_seat_id"] == 0
        assert len(state["hand"]) == 5
        # Alice's hand should match her actual hand
        alice_hand = [{"suit": c.suit.value, "rank": c.rank.name} for c in game.players[0].hand]
        assert state["hand"] == alice_hand

        # Check Bob (seat 1) sees his own cards
        state_bob = await lobby_manager.get_game_state_json(game, 1)
        assert state_bob["my_seat_id"] == 1
        bob_hand = [{"suit": c.suit.value, "rank": c.rank.name} for c in game.players[1].hand]
        assert state_bob["hand"] == bob_hand
        assert state_bob["hand"] != alice_hand

@pytest.mark.anyio
async def test_get_game_state_json_bidding_info(lobby_manager, game):
    with patch("app.db.redis_client.client", new_callable=AsyncMock) as mock_redis:
        mock_redis.hgetall.return_value = {}
        # In Round 1, bidding info should be present
        state = await lobby_manager.get_game_state_json(game, 0)
        assert state["current_bidder"] == 1  # Alice is dealer (0), so Bob (1) is first bidder
        assert state["bidding_phase"] == 1
        assert state["turned_up_card"] is not None
        assert state["trump_suit"] is None

        # After trump is set, bidding info should be gone
        game.set_trump(maker_id=0, suit=Suit.HEARTS)
        state_after = await lobby_manager.get_game_state_json(game, 0)
        assert state_after["current_bidder"] is None
        assert state_after["bidding_phase"] is None
        assert state_after["turned_up_card"] is None
        assert state_after["trump_suit"] == "HEARTS"

@pytest.mark.anyio
async def test_get_game_state_json_dealer_discard(lobby_manager, game):
    with patch("app.db.redis_client.client", new_callable=AsyncMock) as mock_redis:
        mock_redis.hgetall.return_value = {}
        # Force turned up card to be HEARTS
        game.current_bid_card = Card(Suit.HEARTS, Rank.NINE) # Need to set this properly
        game.current_bidding.turned_up_card = Card(Suit.HEARTS, Rank.NINE)
        # Alice is dealer (seat 0). Bob (seat 1) orders up hearts.
        game.current_bidding.call(1, Suit.HEARTS)
        
        # Check Alice's view (Dealer)
        state_alice = await lobby_manager.get_game_state_json(game, 0)
        assert state_alice["bidding_phase"] == 3 # DEALER_DISCARD
        assert len(state_alice["hand"]) == 6 # 5 original + 1 turned up
        
        # Check Charlie's view (Non-dealer)
        state_charlie = await lobby_manager.get_game_state_json(game, 2)
        assert state_charlie["bidding_phase"] == 3
        assert len(state_charlie["hand"]) == 5 # Still 5

@pytest.mark.anyio
async def test_get_game_state_json_current_turn(lobby_manager, game):
    with patch("app.db.redis_client.client", new_callable=AsyncMock) as mock_redis:
        mock_redis.hgetall.return_value = {}
        # Before trump is set, current_turn should be None
        state = await lobby_manager.get_game_state_json(game, 0)
        assert state["current_turn"] is None

        # Set trump and start first trick
        game.set_trump(maker_id=0, suit=Suit.HEARTS)
        game.current_hand.start_trick(1) # Bob leads
        
        state_trick = await lobby_manager.get_game_state_json(game, 0)
        assert state_trick["current_turn"] == 1
        assert state_trick["current_trick"] == []

        # Play a card
        card = game.players[1].hand[0]
        game.current_hand.tricks[-1].play_card(1, card, game.players[1].hand)
        
        state_after_play = await lobby_manager.get_game_state_json(game, 0)
        assert state_after_play["current_turn"] == 2 # Charlie's turn
        assert len(state_after_play["current_trick"]) == 1
        assert state_after_play["current_trick"][0]["player_id"] == 1

@pytest.mark.anyio
async def test_lobby_lifecycle():
    # Mock the internal client within the RedisClient instance
    with patch("app.db.redis_client.client", new_callable=AsyncMock) as mock_redis:
        # Since 'redis' property returns 'self.client', mock_redis will be returned
        mock_redis.exists.return_value = False
        mock_redis.lrange.side_effect = [
            [b"Alice"],
            [b"Alice", b"Bob"],
            [b"Alice", b"Bob", b"Charlie"],
            [b"Alice", b"Bob", b"Charlie", b"David"]
        ]
        
        manager = LobbyManager()
        
        # Mock hgetall to return settings
        mock_redis.hgetall.return_value = {
            "win_threshold": "2",
            "screw_the_dealer": "0",
            "no_trump_enabled": "0",
            "bottom_3_enabled": "0",
        }
        
        # First 3 players join
        res1 = await manager.join_lobby("test", "Alice")
        assert res1 is None
        res2 = await manager.join_lobby("test", "Bob")
        assert res2 is None
        res3 = await manager.join_lobby("test", "Charlie")
        assert res3 is None
        
        # 4th player joins, game starts
        res4 = await manager.join_lobby("test", "David")
        assert isinstance(res4, Game)
        assert len(res4.players) == 4
        assert res4.current_bidding is not None
        
        # Verify save_game was called (which calls redis.set)
        assert mock_redis.set.called
        # Verify pending_lobby was deleted
        assert mock_redis.delete.called

@pytest.mark.anyio
async def test_get_game_state_json_settings(lobby_manager, game):
    with patch("app.db.redis_client.client", new_callable=AsyncMock) as mock_redis:
        mock_redis.hgetall.return_value = {
            "win_threshold": "10",
            "screw_the_dealer": "1",
            "no_trump_enabled": "1",
            "bottom_3_enabled": "0"
        }
        game.screw_the_dealer = True
        game.win_threshold = 10
        state = await lobby_manager.get_game_state_json(game, 0)
        assert state["win_threshold"] == 10
        assert state["screw_the_dealer"] is True
        assert state["no_trump_enabled"] is True
        assert state["bottom_3_enabled"] is False

@pytest.mark.anyio
async def test_get_game_state_json_no_trump_no_crash(lobby_manager, game):
    with patch("app.db.redis_client.client", new_callable=AsyncMock) as mock_redis:
        mock_redis.hgetall.return_value = {"no_trump_enabled": "1"}
        # Alice (0) is dealer. Bob (1) is maker.
        # Set trump to None (No Trump)
        game.set_trump(maker_id=1, suit=None)
        
        state = await lobby_manager.get_game_state_json(game, 0)
        
        assert state["trump_suit"] is None
        assert state["is_no_trump"] is True
