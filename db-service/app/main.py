from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from passlib.context import CryptContext

from app import models, schemas
from app.database import engine, get_db

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Database Service")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        if db_user.hashed_password:
            raise HTTPException(status_code=400, detail="Username already registered")
        else:
            db_user.hashed_password = pwd_context.hash(user.password)
            db.commit()
            db.refresh(db_user)
            return db_user
    
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users/verify")
def verify_user(user: schemas.UserVerify, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not db_user.hashed_password or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"message": "Success"}

@app.get("/users/{username}", response_model=schemas.User)
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/matches/", response_model=schemas.Match)
def create_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    db_match = models.MatchHistory(
        team_alpha_score=match.team_alpha_score,
        team_bravo_score=match.team_bravo_score,
        winning_team_players=json.dumps(match.winning_team_players),
        losing_team_players=json.dumps(match.losing_team_players)
    )
    db.add(db_match)
    
    # Process winners
    for username in match.winning_team_players:
        if username.startswith("Bot_"):
            continue
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            user.games_played += 1
            user.games_won += 1
            user.win_percentage = round((user.games_won / user.games_played) * 100.0, 2)

    # Process losers
    for username in match.losing_team_players:
        if username.startswith("Bot_"):
            continue
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            user.games_played += 1
            user.win_percentage = round((user.games_won / user.games_played) * 100.0, 2)

    db.commit()
    db.refresh(db_match)
    return db_match

@app.get("/leaderboard/", response_model=list[schemas.User])
def get_leaderboard(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.win_percentage.desc(), models.User.games_won.desc()).offset(skip).limit(limit).all()
    return users
