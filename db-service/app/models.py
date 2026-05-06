from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base
import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    win_percentage = Column(Float, default=0.0)

class MatchHistory(Base):
    __tablename__ = "match_history"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    team_alpha_score = Column(Integer)
    team_bravo_score = Column(Integer)
    winning_team_players = Column(String) # JSON encoded list of usernames
    losing_team_players = Column(String) # JSON encoded list of usernames
