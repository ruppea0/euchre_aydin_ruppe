import websockets
import json
import anyio
import random
import traceback

import os
API_URL = os.getenv("API_URL", "ws://localhost:8000/ws")

class BotPlayer:
    def __init__(self, lobby_id: str, name: str):
        self.lobby_id = lobby_id
        self.name = name
        self.ws_url = f"{API_URL}/{lobby_id}?token={name}"

    async def run(self):
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print(f"[{self.name}] Connected to {self.ws_url}")
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if data.get("type") == "game_state":
                        if data.get("is_over"):
                            print(f"[{self.name}] Game is over. Disconnecting.")
                            break
                        await self.handle_game_state(data, websocket)
                    elif data.get("type") == "error":
                        print(f"[{self.name}] Error from server: {data.get('message')}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.name}] Disconnected.")
        except Exception as e:
            print(f"[{self.name}] Exception: {e}")
            traceback.print_exc()

    async def handle_game_state(self, state: dict, websocket):
        my_seat_id = state.get("my_seat_id")
        current_turn = state.get("current_turn")
        current_bidder = state.get("current_bidder")
        bidding_phase = state.get("bidding_phase")
        is_over = state.get("is_over")
        
        if is_over:
            return

        if bidding_phase is not None:
            # We are in bidding phase
            if current_bidder == my_seat_id:
                await anyio.sleep(1.5) # realism
                await self.make_bid(state, websocket)
        else:
            # We are in play phase
            if current_turn == my_seat_id:
                await anyio.sleep(1.5) # realism
                await self.play_card(state, websocket)

    async def make_bid(self, state: dict, websocket):
        bidding_phase = state.get("bidding_phase")
        turned_up_card = state.get("turned_up_card")
        my_seat_id = state.get("my_seat_id")
        
        try:
            if bidding_phase == 1: # ROUND_1
                # Randomly pass or order up
                if random.random() < 0.3:
                    action = {
                        "type": "call_trump",
                        "suit": turned_up_card["suit"]
                    }
                else:
                    action = {
                        "type": "call_trump",
                        "suit": None
                    }
                await websocket.send(json.dumps(action))
                
            elif bidding_phase == 2: # ROUND_2
                # Pick a random suit that is not turned_up
                suits = ["HEARTS", "DIAMONDS", "CLUBS", "SPADES"]
                if turned_up_card:
                    suits.remove(turned_up_card["suit"])
                
                screw_the_dealer = state.get("screw_the_dealer", False)
                dealer_id = state.get("dealer_id")
                
                # If Screw the Dealer is on and we are the dealer, we MUST call a suit
                if screw_the_dealer and my_seat_id == dealer_id:
                    action = {
                        "type": "call_trump",
                        "suit": random.choice(suits)
                    }
                elif random.random() < 0.3:
                    action = {
                        "type": "call_trump",
                        "suit": random.choice(suits)
                    }
                else:
                    action = {
                        "type": "call_trump",
                        "suit": None
                    }
                await websocket.send(json.dumps(action))
                
            elif bidding_phase == 3: # DEALER_DISCARD
                # Just discard the lowest non-trump card if possible
                hand = state.get("hand", [])
                card_to_discard = hand[0]
                action = {
                    "type": "dealer_discard",
                    "suit": card_to_discard["suit"],
                    "rank": card_to_discard["rank"]
                }
                await websocket.send(json.dumps(action))
        except Exception as e:
             print(f"[{self.name}] Error making bid: {e}")

    async def play_card(self, state: dict, websocket):
        hand = state.get("hand", [])
        current_trick = state.get("current_trick", [])
        trump_suit = state.get("trump_suit")
        
        legal_cards = hand # Simplification: assume all are legal for now, but we MUST follow suit
        
        try:
            if current_trick:
                lead_card = current_trick[0]["card"]
                
                def get_effective_suit(card):
                    if card["rank"] == "JACK":
                        is_left = False
                        if trump_suit == "HEARTS" and card["suit"] == "DIAMONDS": is_left = True
                        if trump_suit == "DIAMONDS" and card["suit"] == "HEARTS": is_left = True
                        if trump_suit == "SPADES" and card["suit"] == "CLUBS": is_left = True
                        if trump_suit == "CLUBS" and card["suit"] == "SPADES": is_left = True
                        if is_left:
                            return trump_suit
                    return card["suit"]

                eff_lead_suit = get_effective_suit(lead_card)
                
                following_cards = [c for c in hand if get_effective_suit(c) == eff_lead_suit]
                if following_cards:
                    legal_cards = following_cards

            card_to_play = random.choice(legal_cards)
            
            action = {
                "type": "play_card",
                "suit": card_to_play["suit"],
                "rank": card_to_play["rank"]
            }
            await websocket.send(json.dumps(action))
        except Exception as e:
            print(f"[{self.name}] Error playing card: {e}")
