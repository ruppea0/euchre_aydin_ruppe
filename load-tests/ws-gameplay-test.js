import http from 'k6/http';
import ws from 'k6/ws';
import { check } from 'k6';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp up to 20 VUs
    { duration: '1m', target: 20 },  // Hold at 20 VUs (5 lobbies of 4)
    { duration: '30s', target: 0 },  // Ramp down
  ],
  thresholds: {
    'ws_connecting': ['p(95)<500'], // Session setup time
    'ws_msgs_sent': ['count>100'], // Ensure we are actually sending messages
  }
};

const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = __ENV.WS_BASE_URL || 'ws://localhost:8000';

export default function () {
  // 1. Setup Phase: Register and Login
  const uniqueId = `ws_user_${__VU}_${__ITER}_${Date.now()}`;
  const password = 'password123';
  
  const registerPayload = JSON.stringify({ username: uniqueId, password: password });
  const registerHeaders = { 'Content-Type': 'application/json' };
  
  // Register (ignore 400 if it somehow already exists)
  http.post(`${API_BASE_URL}/api/register`, registerPayload, { headers: registerHeaders });

  // Login
  const loginPayload = { username: uniqueId, password: password };
  const loginRes = http.post(`${API_BASE_URL}/api/token`, loginPayload);
  
  check(loginRes, { 'logged in successfully': (r) => r.status === 200 });
  
  let token;
  try {
    token = loginRes.json('access_token');
  } catch (e) {
    console.error("Failed to parse token response");
    return; // Exit iteration if login fails
  }

  // 2. Determine Lobby ID (group every 4 VUs into one lobby)
  const lobbyId = `load_test_lobby_${Math.ceil(__VU / 4)}`;

  // 3. Connect to WebSocket
  const url = `${WS_BASE_URL}/ws/${lobbyId}?token=${token}`;
  
  const suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades'];
  const ranks = ['NINE', 'TEN', 'JACK', 'QUEEN', 'KING', 'ACE'];

  const res = ws.connect(url, function (socket) {
    socket.on('open', () => {
      // Successfully connected
    });

    socket.on('message', (msg) => {
      // For load testing the backend, we don't strictly parse the state.
      // We just ensure we're receiving state updates and responding with load.
    });

    socket.on('close', () => {
      // Connection closed
    });

    socket.on('error', (e) => {
      if (e.error() != "websocket: close sent") {
        console.error('An unexpected error occurred: ', e.error());
      }
    });

    // Send a message every 1-3 seconds to simulate game actions
    socket.setInterval(function timeout() {
        const actionType = randomItem(['call_trump', 'play_card', 'pass']);
        
        let payload = {};
        if (actionType === 'call_trump') {
            payload = {
                type: 'call_trump',
                suit: randomItem(suits),
                alone: false,
                is_no_trump: false
            };
        } else if (actionType === 'play_card') {
            payload = {
                type: 'play_card',
                suit: randomItem(suits),
                rank: randomItem(ranks)
            };
        } else {
            payload = { type: 'pass' };
        }

        socket.send(JSON.stringify(payload));
    }, Math.random() * 2000 + 1000); // Random interval between 1s and 3s

    // Close the connection after a set time to simulate leaving the lobby or game end
    socket.setTimeout(function () {
        socket.close();
    }, 45000); // Close after 45 seconds of active play
  });
  
  check(res, { 'status is 101': (r) => r && r.status === 101 });
}
