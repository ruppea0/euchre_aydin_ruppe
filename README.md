# Euchre Microservices

A real-time, microservices-based Euchre application featuring a Python (FastAPI) backend, a React (TypeScript) frontend, and a Redis-backed distributed state management system.

##  Features

- **Real-time Gameplay:** Low-latency trick-taking action powered by WebSockets.
- **Microservices Architecture:** Independently scalable services for API, Database, Bots, and Web frontend.
- **Distributed State:** Redis handles active game state, allowing for service resilience and fast lookups.
- **Automated Bots:** Add bots to fill empty seats or take over for disconnected players.
- **Persistent Stats:** Track your wins, games played, and climb the global leaderboard.
- **Advanced Rules:** Supports "Screw the Dealer", "No Trump", and "Bottom 3" variations.

##  Architecture

- **Web Service:** React SPA built with Vite and Tailwind CSS. Provides the "green felt" game table experience.
- **API Service:** FastAPI backend. The central authority for game logic, rule enforcement, and WebSocket orchestration.
- **Database Service:** Manages persistent user data, match history, and leaderboards using SQLAlchemy and SQLite (default).
- **Bot Service:** Standalone worker that listens for "add bot" requests and simulates automated players.
- **Redis:** The backbone for real-time state, inter-service messaging (Pub/Sub), and usage statistics.

---

##  Installation & Setup

### Option 1: Docker Compose (Recommended)

The easiest way to run the entire stack is using Docker Compose.

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd euchre-microservices
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Web Frontend: `http://localhost:80`
   - API Docs (Swagger): `http://localhost:8000/docs`
   - DB Service Docs: `http://localhost:8001/docs`

### Option 2: Manual Setup (Development)

If you wish to run services individually for development:

#### 1. Prerequisites
- **Node.js** (v18+)
- **Python** (3.13+)
- **Docker** (for Redis)

#### 2. Start Redis
```bash
docker run --name euchre-redis -p 6379:6379 -d redis:alpine
```

#### 3. Start Database Service
```bash
cd db-service
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

#### 4. Start API Service
```bash
cd api-service
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 5. Start Bot Service
```bash
cd bot-service
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### 6. Start Web Service
```bash
cd web-service
npm install
npm run dev
```

---

##  API Documentation

The API Service exposes REST endpoints for authentication and lobby management, and a WebSocket endpoint for live gameplay.

### REST Endpoints

#### Authentication
- **`POST /api/register`**: Register a new account.
  - Body: `{"username": "jdoe", "password": "securepassword"}`
- **`POST /api/token`**: Login and receive a JWT access token.
  - Body (Form Data): `username=jdoe&password=securepassword`
  - Returns: `{"access_token": "...", "token_type": "bearer"}`

#### Game & Social
- **`GET /api/leaderboard`**: Retrieve the top players by win percentage.
- **`POST /api/lobbies/{lobby_id}/add-bot`**: Request a bot to join a specific lobby.
- **`GET /api/admin/stats`**: (Admin) View usage statistics per endpoint.

### WebSocket Interface

**Endpoint:** `ws://localhost:8000/ws/{lobby_id}?token={JWT_TOKEN}`

#### Actions (Client -> Server)

- **Call Trump**
  ```json
  {
    "type": "call_trump",
    "suit": "Hearts",
    "alone": false,
    "is_no_trump": false
  }
  ```

- **Play Card**
  ```json
  {
    "type": "play_card",
    "suit": "Spades",
    "rank": "ACE"
  }
  ```

- **Dealer Discard** (After picking up the kitty)
  ```json
  {
    "type": "dealer_discard",
    "suit": "Diamonds",
    "rank": "NINE"
  }
  ```

---

##  How to Play

1. **Register/Login:** Create an account or use an existing one.
2. **Join Lobby:** Enter a Lobby ID to join a game room.
3. **Add Bots:** If you don't have 4 human players, use the "Add Bot" button.
4. **Gameplay:**
   - **Bidding:** Choose to "Order Up" the dealer or "Pass". In the second round, name any suit as trump.
   - **Tricks:** Play cards to win tricks. The highest trump card wins, or the highest card of the led suit if no trump is played.
   - **Winning:** The first team to 10 points wins the match.

##  Testing

Run unit tests for the game logic:
```bash
cd api-service
pytest
```
