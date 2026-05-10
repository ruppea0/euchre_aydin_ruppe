import http from 'k6/http';
import { check, sleep } from 'k6';

// Define the ramping load profile (stress test)
export const options = {
  stages: [
    { duration: '1m', target: 50 },  // Ramp up to 50 VUs over 1 minute
    { duration: '2m', target: 50 },  // Hold at 50 VUs for 2 minutes
    { duration: '30s', target: 0 },  // Ramp down to 0 VUs over 30 seconds
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
  },
};

const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

export default function () {
  // Scenario 1: Health Check
  const healthRes = http.get(`${API_BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  // Scenario 1: Leaderboard
  const leaderboardRes = http.get(`${API_BASE_URL}/api/leaderboard`);
  check(leaderboardRes, {
    'leaderboard status is 200': (r) => r.status === 200,
  });

  // Scenario 2: Auth Flow
  // Generate a unique username based on the VU ID, iteration, and timestamp
  const uniqueId = `user_${__VU}_${__ITER}_${Date.now()}`;
  const payload = JSON.stringify({
    username: uniqueId,
    password: 'password123',
  });
  
  const headers = { 'Content-Type': 'application/json' };
  
  const registerRes = http.post(`${API_BASE_URL}/api/register`, payload, { headers });
  check(registerRes, {
    'register status is 200 (or 400 if exists)': (r) => r.status === 200 || r.status === 400,
  });

  // Now login to get a token
  // The token endpoint expects form data, so we don't JSON.stringify the payload here
  // k6 automatically URL-encodes an object passed to http.post
  const loginPayload = {
    username: uniqueId,
    password: 'password123',
  };
  
  const loginRes = http.post(`${API_BASE_URL}/api/token`, loginPayload);
  check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'has access_token': (r) => {
        try {
            return r.json('access_token') !== undefined;
        } catch (e) {
            return false;
        }
    }
  });

  // Sleep for a short duration to simulate user think time and prevent overwhelming immediately
  sleep(1);
}
