from pydantic import BaseModel, ConfigDict
from typing import List
import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserVerify(UserBase):
    password: str

class User(UserBase):
    id: str
    games_played: int
    games_won: int
    win_percentage: float

    model_config = ConfigDict(from_attributes=True)

class MatchCreate(BaseModel):
    team_alpha_score: int
    team_bravo_score: int
    winning_team_players: List[str]
    losing_team_players: List[str]

class Match(BaseModel):
    id: str
    date: datetime.datetime
    team_alpha_score: int
    team_bravo_score: int
    winning_team_players: str
    losing_team_players: str

    model_config = ConfigDict(from_attributes=True)
