import json
from typing import List, Optional
from app.game import Game
from app.bidding import BidPhase
from app.db import redis_client


class LobbyManager:
    def __init__(self) -> None:
        # We'll use these prefixes for Redis keys
        self.LOBBY_PREFIX = "lobby:"
        self.PENDING_PREFIX = "pending_lobby:"

    async def create_lobby(self, lobby_id: str, player_name: str) -> None:
        key = f"{self.PENDING_PREFIX}{lobby_id}"
        await redis_client.redis.rpush(key, player_name)  # type: ignore
        # Set a TTL for pending lobbies (e.g., 1 hour)
        await redis_client.redis.expire(key, 3600)  # type: ignore

    async def get_pending_players(self, lobby_id: str) -> List[str]:
        key = f"{self.PENDING_PREFIX}{lobby_id}"
        # Mypy needs help knowing lrange returns a list of strings
        players = await redis_client.redis.lrange(key, 0, -1)  # type: ignore
        return [str(p) for p in players]

    async def join_lobby(
        self,
        lobby_id: str,
        player_name: str,
        win_threshold: int = 2,
        screw_the_dealer: bool = False,
        no_trump_enabled: bool = False,
        bottom_3_enabled: bool = False,
    ) -> Optional[Game]:
        lobby_key = f"{self.LOBBY_PREFIX}{lobby_id}"
        pending_key = f"{self.PENDING_PREFIX}{lobby_id}"
        settings_key = f"settings:{lobby_id}"

        # Check if game already started
        if await redis_client.redis.exists(lobby_key):  # type: ignore
            return None

        # Add player to pending list
        await redis_client.redis.rpush(pending_key, player_name)  # type: ignore
        await redis_client.redis.expire(pending_key, 3600)  # type: ignore

        # Store settings if this is the first player
        players_raw = await redis_client.redis.lrange(pending_key, 0, -1)  # type: ignore
        if len(players_raw) == 1:
            settings = {
                "win_threshold": win_threshold,
                "screw_the_dealer": int(screw_the_dealer),
                "no_trump_enabled": int(no_trump_enabled),
                "bottom_3_enabled": int(bottom_3_enabled),
            }
            await redis_client.redis.hmset(settings_key, settings)  # type: ignore
            await redis_client.redis.expire(settings_key, 3600)  # type: ignore

        players = [str(p) for p in players_raw]

        if len(players) == 4:
            # Retrieve settings
            s = await redis_client.redis.hgetall(settings_key)  # type: ignore
            game = Game(
                players,
                win_threshold=int(s.get("win_threshold", 2)),
                screw_the_dealer=bool(int(s.get("screw_the_dealer", 0))),
                bottom_3_enabled=bool(int(s.get("bottom_3_enabled", 0))),
                lobby_id=lobby_id,
            )
            # Add no_trump_enabled to game if needed
            game.start_new_hand()
            await self.save_game(lobby_id, game)
            await redis_client.redis.delete(pending_key)  # type: ignore
            return game
        return None

    async def get_game(self, lobby_id: str) -> Optional[Game]:
        lobby_key = f"{self.LOBBY_PREFIX}{lobby_id}"
        data = await redis_client.redis.get(lobby_key)  # type: ignore
        if data:
            return Game.from_dict(json.loads(str(data)))
        return None

    async def save_game(self, lobby_id: str, game: Game) -> None:
        lobby_key = f"{self.LOBBY_PREFIX}{lobby_id}"
        await redis_client.redis.set(  # type: ignore
            lobby_key, json.dumps(game.to_dict())
        )
        # Set a TTL for active games (e.g., 1 hour)
        await redis_client.redis.expire(lobby_key, 3600)  # type: ignore

    async def delete_game(self, lobby_id: str) -> None:
        lobby_key = f"{self.LOBBY_PREFIX}{lobby_id}"
        await redis_client.redis.delete(lobby_key)  # type: ignore

    async def get_game_state_json(self, game: Game, seat_id: int) -> dict:
        player = game.players[seat_id]

        current_trick = []
        current_turn = None

        if game.current_hand:
            if game.current_hand.tricks:
                last_trick = game.current_hand.tricks[-1]
                # Include cards even if the trick is full (so they show during the pause)
                current_trick = [
                    {
                        "player_id": p_id,
                        "card": {"suit": c.suit.value, "rank": c.rank.name},
                    }
                    for p_id, c in last_trick.cards_played
                ]

                if len(last_trick.cards_played) < len(last_trick.active_seats):
                    current_turn = (
                        last_trick.leader_id + len(last_trick.cards_played)
                    ) % 4
                    while current_turn not in last_trick.active_seats:
                        current_turn = (current_turn + 1) % 4
                else:
                    # Trick is full, but hasn't been cleared yet (waiting for pause)
                    current_turn = None

        hand = [{"suit": c.suit.value, "rank": c.rank.name} for c in player.hand]

        # If it's the discard phase and I'm the dealer, show the 6th card
        if (
            game.current_bidding
            and game.current_bidding.phase == BidPhase.DEALER_DISCARD
            and seat_id == game.dealer_id
        ):
            hand.append(
                {
                    "suit": game.current_bidding.turned_up_card.suit.value,
                    "rank": game.current_bidding.turned_up_card.rank.name,
                }
            )

        # Fetch settings from Redis
        settings = await redis_client.redis.hgetall(f"settings:{game.lobby_id}")  # type: ignore

        return {
            "type": "game_state",
            "my_seat_id": seat_id,
            "dealer_id": game.dealer_id,
            "current_bidder": (
                game.current_bidding.current_bidder if game.current_bidding else None
            ),
            "bidding_phase": (
                game.current_bidding.phase.value if game.current_bidding else None
            ),
            "turned_up_card": (
                {
                    "suit": game.current_bidding.turned_up_card.suit.value,
                    "rank": game.current_bidding.turned_up_card.rank.name,
                }
                if game.current_bidding
                else None
            ),
            "trump_suit": (
                game.current_hand.trump_suit.value
                if game.current_hand and game.current_hand.trump_suit
                else None
            ),
            "maker_id": game.current_hand.maker_id if game.current_hand else None,
            "alone": game.current_hand.alone if game.current_hand else False,
            "is_no_trump": (
                game.current_hand.trump_suit is None if game.current_hand else False
            ),
            "team_scores": game.team_scores,
            "hand": hand,
            "tricks_won": (
                game.current_hand.scores if game.current_hand else {0: 0, 1: 0}
            ),
            "current_trick": current_trick,
            "current_turn": current_turn if game.current_hand else None,
            "is_over": game.is_over,
            "win_threshold": game.win_threshold,
            "screw_the_dealer": game.screw_the_dealer,
            "no_trump_enabled": bool(int(settings.get("no_trump_enabled", 0))),
            "bottom_3_enabled": bool(int(settings.get("bottom_3_enabled", 0))),
            "bottom_3_used": game.current_bidding.bottom_3_used if game.current_bidding else False,
        }


lobby_manager = LobbyManager()
