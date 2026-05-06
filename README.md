# Euchre Microservices

A real-time, microservices-based Euchre application featuring a Python (FastAPI) backend, a React (TypeScript) frontend, and a Redis-backed distributed state management system.

## 🏗 Architecture

- **API Service:** FastAPI backend that handles game logic, WebSocket orchestration, and JWT-based authentication.
- **Database Service:** Persistent datastore microservice managing User profiles, Match History, and Leaderboards via SQLAlchemy.
- **Bot Service:** Standalone Python microservice that listens for "add bot" requests via Redis and simulates automated players.
- **Web Service:** React SPA built with Vite and Tailwind CSS v4, providing a "green felt" game table experience.
- **Redis:** Distributed data store for managing active lobbies, real-time state, and inter-service communication.

## 🚀 Getting Started Locally

### Prerequisites
- **Node.js** (v18+)
- **Python** (3.13+)
- **Docker** (for running Redis)

---

### 1. Start Redis
The easiest way to get Redis running is via Docker:
```powershell
docker run --name euchre-redis -p 6379:6379 -d redis
```

### 2. Start the Database Service
1. Open a new terminal and navigate to the directory:
   ```powershell
   cd db-service
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install fastapi uvicorn sqlalchemy pydantic passlib bcrypt
   ```
4. Run the server:
   ```powershell
   uvicorn app.main:app --reload --port 8001
   ```

### 3. Start the API Service
1. Open a new terminal and navigate to the directory:
   ```powershell
   cd api-service
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   pip install "python-jose[cryptography]" "passlib[bcrypt]" python-multipart
   ```
4. Run the server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

### 4. Start the Bot Service
1. Open a new terminal and navigate to the directory:
   ```powershell
   cd bot-service
   ```
2. Create and activate a virtual environment (if not already done):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install websockets redis anyio
   ```
4. Run the bot worker:
   ```powershell
   python main.py
   ```

### 5. Start the Web Service
1. Open a new terminal and navigate to the directory:
   ```powershell
   cd web-service
   ```
2. Install dependencies:
   ```powershell
   npm install
   ```
3. Run the development server:
   ```powershell
   npm run dev
   ```
4. Open your browser to the URL provided (usually `http://localhost:5173`).

---

## 🎮 How to Play
1. Open the Web Service.
2. **Register or Log In** with a username and password.
3. Once logged in, enter a **Lobby ID** to join or create a room.
4. Once in the lobby, you can either wait for other human players to join OR click the **"Add Bot"** button to fill empty seats.
5. Once 4 players (human or bot) are in the lobby, the game starts automatically.
6. Follow the "Set Trump" and "Your Turn" indicators to play!
7. Final match results are persisted to the database and affect the global leaderboard.

## 🧪 Running Tests
To verify the core game logic and serialization:
```powershell
cd api-service
.\venv\Scripts\activate
pytest
```
