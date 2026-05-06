from typing import List, Optional, Dict
from pydantic import BaseModel
from app.models import Suit, Rank


class CardSchema(BaseModel):
    suit: Suit
    rank: Rank


class JoinLobbyAction(BaseModel):
    player_name: str


class CallTrumpAction(BaseModel):
    suit: Optional[Suit]
    alone: bool = False


class PlayCardAction(BaseModel):
    suit: Suit
    rank: Rank


class GameStateUpdate(BaseModel):
    type: str = "game_state"
    my_seat_id: int
    dealer_id: int
    current_bidder: Optional[int]
    trump_suit: Optional[Suit]
    maker_id: Optional[int]
    alone: bool
    team_scores: Dict[int, int]
    hand: List[CardSchema]
    tricks_won: Dict[int, int]
    current_trick: List[Dict]  # List of {player_id: int, card: CardSchema}
    current_turn: Optional[int]
    is_over: bool


class LobbyUpdate(BaseModel):
    type: str = "lobby_update"
    lobby_id: str
    players: List[str]
    is_full: bool


class ErrorMessage(BaseModel):
    type: str = "error"
    message: str
