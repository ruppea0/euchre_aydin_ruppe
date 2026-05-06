import json
import httpx
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import HTTPConnection
from app.websocket import manager
from app.manager import lobby_manager
from app.models import Suit, Card, Rank
from app.game import Game
from app.bidding import BidPhase
import os
from app.db import redis_client

DB_SERVICE_URL = os.getenv("DB_SERVICE_URL", "http://localhost:8001")
SECRET_KEY = "super-secret-euchre-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class UserRegister(BaseModel):
    username: str
    password: str


async def submit_match_results(game: Game) -> None:
    alpha_score = game.team_scores[0]
    bravo_score = game.team_scores[1]

    alpha_players = [game.players[0].name, game.players[2].name]
    bravo_players = [game.players[1].name, game.players[3].name]

    if alpha_score >= game.win_threshold:
        winning_team = alpha_players
        losing_team = bravo_players
    else:
        winning_team = bravo_players
        losing_team = alpha_players

    payload = {
        "team_alpha_score": alpha_score,
        "team_bravo_score": bravo_score,
        "winning_team_players": winning_team,
        "losing_team_players": losing_team,
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{DB_SERVICE_URL}/matches/", json=payload)
    except Exception as e:
        print(f"Failed to submit match results to db-service: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: Connect to Redis
    await redis_client.connect()
    yield
    # Shutdown: Disconnect from Redis
    await redis_client.disconnect()


app = FastAPI(title="Euchre API", lifespan=lifespan)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def record_usage_stats(request: Request, call_next):
    # Determine the route pattern to use as a key
    route_path = "unknown"
    
    for route in app.routes:
        match, _ = route.matches(request.scope)
        if match.name == "MATCH":
            route_path = getattr(route, "path", "unknown")
            break

    # If it's still unknown, use the raw path but group common ones
    if route_path == "unknown":
        raw_path = request.url.path
        # Very basic heuristic for grouping
        if raw_path.startswith("/api/lobbies/") and "/add-bot" in raw_path:
            route_path = "/api/lobbies/{lobby_id}/add-bot"
        else:
            route_path = raw_path

    # Increment counter in Redis
    try:
        await redis_client.redis.incr(f"usage_stats:{route_path}")
    except Exception as e:
        print(f"Failed to record usage stats: {e}")

    response = await call_next(request)
    return response


@app.get("/api/admin/stats")
async def get_admin_stats():
    try:
        keys = await redis_client.redis.keys("usage_stats:*")
        stats = {}
        for key in keys:
            count = await redis_client.redis.get(key)
            # Remove "usage_stats:" prefix for the response
            endpoint = key.replace("usage_stats:", "")
            stats[endpoint] = int(count) if count else 0
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {e}")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.post("/api/register")
async def register(user: UserRegister):
    payload = {"username": user.username, "password": user.password}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{DB_SERVICE_URL}/users/", json=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Username already registered")
        return {"msg": "User created"}


@app.post("/api/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    payload = {"username": form_data.username, "password": form_data.password}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{DB_SERVICE_URL}/users/verify", json=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": form_data.username,
    }


@app.get("/api/leaderboard")
async def get_leaderboard():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{DB_SERVICE_URL}/leaderboard/")
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Could not fetch leaderboard"
            )
        return response.json()


@app.post("/api/lobbies/{lobby_id}/add-bot")
async def add_bot(lobby_id: str) -> dict:
    await redis_client.redis.publish("bot_requests", lobby_id)  # type: ignore
    return {"status": "bot requested"}


async def broadcast_game_state(lobby_id: str, game: Game) -> None:
    """Helper to send customized game state to every player based on their seat."""
    if lobby_id in manager.lobby_connections:
        # We iterate over the players defined in the game to find their connections
        for seat_id, player in enumerate(game.players):
            ws = manager.lobby_connections[lobby_id].get(player.name)
            if ws:
                state = await lobby_manager.get_game_state_json(game, seat_id)
                await ws.send_json(state)


@app.websocket("/ws/{lobby_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    lobby_id: str,
    token: str,
    win_threshold: int = 10,
    screw_the_dealer: bool = False,
    no_trump_enabled: bool = False,
    bottom_3_enabled: bool = False,
) -> None:
    if token.startswith("Bot_"):
        player_name = token
    else:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            player_name = payload.get("sub")
            if player_name is None:
                await websocket.close(code=1008)
                return
        except JWTError:
            await websocket.close(code=1008)
            return

    await manager.accept_connection(websocket)
    manager.register_connection(lobby_id, player_name, websocket)

    # Store the player's seat_id for this connection
    seat_id = -1

    try:
        # Join lobby with settings
        game = await lobby_manager.join_lobby(
            lobby_id,
            player_name,
            win_threshold=win_threshold,
            screw_the_dealer=screw_the_dealer,
            no_trump_enabled=no_trump_enabled,
            bottom_3_enabled=bottom_3_enabled,
        )

        # If the game just started (4th player joined), game will not be None
        if not game:
            game = await lobby_manager.get_game(lobby_id)
            if not game:
                # Still waiting for players
                players = await lobby_manager.get_pending_players(lobby_id)
                await manager.broadcast_lobby_update(
                    lobby_id,
                    {
                        "type": "lobby_update",
                        "lobby_id": lobby_id,
                        "players": players,
                        "is_full": False,
                    },
                )
            else:
                # Game is active, resolve seat_id
                for i, p in enumerate(game.players):
                    if p.name == player_name:
                        seat_id = i
                        break
        else:
            # Game just started
            for i, p in enumerate(game.players):
                if p.name == player_name:
                    seat_id = i
                    break

        # If game is active, broadcast the personalized state to everyone
        if game:
            await broadcast_game_state(lobby_id, game)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action_type = message.get("type")

            game = await lobby_manager.get_game(lobby_id)
            if not game:
                continue

            # If we don't have a seat_id yet, try to find it
            if seat_id == -1:
                for i, p in enumerate(game.players):
                    if p.name == player_name:
                        seat_id = i
                        break

            if seat_id == -1:
                continue

            try:
                if action_type == "call_trump":
                    suit_val = message.get("suit")
                    suit = Suit(suit_val) if suit_val else None
                    alone = message.get("alone", False)
                    is_no_trump = message.get("is_no_trump", False)
                    
                    # Check if No Trump is even allowed for this lobby
                    if is_no_trump:
                        settings = await redis_client.redis.hgetall(f"settings:{lobby_id}") # type: ignore
                        if not bool(int(settings.get("no_trump_enabled", 0))):
                             raise ValueError("No Trump rule is not enabled in this lobby.")

                    if game.current_bidding:
                        if game.current_bidding.call(seat_id, suit, alone, is_no_trump):
                            # Trump was set
                            if game.current_bidding.phase == BidPhase.DEALER_DISCARD:
                                # Wait for dealer to discard
                                pass
                            elif game.current_bidding.maker_id is not None and (
                                game.current_bidding.trump_suit is not None
                                or game.current_bidding.is_no_trump
                            ):
                                # Round 2 call (no discard needed)
                                game.set_trump(
                                    game.current_bidding.maker_id,
                                    game.current_bidding.trump_suit,
                                    game.current_bidding.alone,
                                )
                                # Start first trick
                                if game.current_hand:
                                    game.current_hand.start_trick(
                                        (game.dealer_id + 1) % 4
                                    )
                        elif game.current_bidding.phase == BidPhase.COMPLETED:
                            # Everyone passed both rounds
                            game.dealer_id = (game.dealer_id + 1) % 4
                            game.start_new_hand()

                        # Save updated state to Redis
                        await lobby_manager.save_game(lobby_id, game)
                        # BROADCAST personalized state
                        await broadcast_game_state(lobby_id, game)

                elif action_type == "dealer_discard":
                    suit_val = message.get("suit")
                    rank_name = message.get("rank")
                    if not suit_val or not rank_name:
                        raise ValueError("Card suit and rank are required for discard.")

                    suit = Suit(suit_val)
                    rank = Rank[rank_name]
                    card = Card(suit, rank)

                    game.apply_dealer_discard(seat_id, card)

                    # After discard, start first trick
                    if game.current_hand:
                        game.current_hand.start_trick((game.dealer_id + 1) % 4)

                    # Save updated state to Redis
                    await lobby_manager.save_game(lobby_id, game)
                    # BROADCAST personalized state
                    await broadcast_game_state(lobby_id, game)

                elif action_type == "bottom_3":
                    cards_data = message.get("cards", [])
                    if not cards_data or len(cards_data) != 3:
                        raise ValueError("Exactly 3 cards are required for Bottom 3.")

                    cards_to_swap = [
                        Card(Suit(c["suit"]), Rank[c["rank"]]) for c in cards_data
                    ]

                    game.perform_bottom_3(seat_id, cards_to_swap)

                    # Save and broadcast
                    await lobby_manager.save_game(lobby_id, game)
                    await broadcast_game_state(lobby_id, game)

                elif action_type == "play_card":
                    suit_val = message.get("suit")
                    rank_name = message.get("rank")
                    if not suit_val or not rank_name:
                        raise ValueError("Card suit and rank are required.")

                    suit = Suit(suit_val)
                    rank = Rank[rank_name]
                    card = Card(suit, rank)

                    if game.current_hand:
                        trick = game.current_hand.tricks[-1]
                        trick.play_card(seat_id, card, game.players[seat_id].hand)
                        game.players[seat_id].hand.remove(card)

                        # Check if trick is over
                        if len(trick.cards_played) == len(trick.active_seats):
                            # Save and broadcast immediately so players see the 4th card
                            await lobby_manager.save_game(lobby_id, game)
                            await broadcast_game_state(lobby_id, game)

                            # Subtle pause for visibility
                            await asyncio.sleep(2)

                            winner_id = trick.get_winner()
                            game.current_hand.record_trick_winner(winner_id)

                            if len(game.current_hand.tricks) < 5:
                                game.current_hand.start_trick(winner_id)
                            else:
                                # Hand over
                                game.finish_hand()
                                if not game.is_over:
                                    game.start_new_hand()
                                else:
                                    await submit_match_results(game)

                        # Save updated state (either 1-3 cards played OR board cleared after pause)
                        await lobby_manager.save_game(lobby_id, game)
                        await broadcast_game_state(lobby_id, game)

            except ValueError as e:
                await manager.send_personal_message(
                    {"type": "error", "message": str(e)}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(lobby_id, player_name)

        # If the game is over and this was the last human, clean up Redis
        game = await lobby_manager.get_game(lobby_id)
        if game and game.is_over:
            remaining_conns = manager.lobby_connections.get(lobby_id, {})
            # If only bots left or no one left
            human_left = any(
                not name.startswith("Bot_") for name in remaining_conns.keys()
            )
            if not human_left:
                await lobby_manager.delete_game(lobby_id)
                # Also clear pending players just in case
                await redis_client.redis.delete(f"lobby:{lobby_id}:players")
