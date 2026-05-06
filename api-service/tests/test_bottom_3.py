import pytest
from app.game import Game
from app.models import Card, Suit, Rank
from app.bidding import BidPhase

def test_perform_bottom_3_success():
    # Setup game with Bottom 3 enabled
    game = Game(["P1", "P2", "P3", "P4"], bottom_3_enabled=True)
    game.start_new_hand()
    
    # Current bidder (P1, seat 1 as dealer is P0)
    current_bidder_id = game.current_bidding.current_bidder
    player = game.players[current_bidder_id]
    
    # We need to make sure the player has three 9s/10s.
    # To keep the deck valid, we'll find three 9s/10s in the deck that are NOT in the kitty
    # and swap them into the player's hand.
    
    kitty_indices = [21, 22, 23]
    kitty_cards = [game.deck.cards[i] for i in kitty_indices]
    
    # We need cards that are 9/10, NOT in the kitty, AND NOT already in the player's hand
    nine_tens_in_deck = [
        c for c in game.deck.cards 
        if c.rank in [Rank.NINE, Rank.TEN] 
        and c not in kitty_cards 
        and c not in player.hand
    ]
    
    # Ensure player has 3 of these
    swap_cards = nine_tens_in_deck[:3]
    
    # Put these in player's hand, and move player's old cards back to where these were
    for i in range(3):
        target_card = swap_cards[i]
        deck_idx = game.deck.cards.index(target_card)
        old_hand_card = player.hand[i]
        
        player.hand[i] = target_card
        game.deck.cards[deck_idx] = old_hand_card

    # Now we have a valid deck with no duplicates, and player has 3 9s/10s
    kitty_before = list(game.deck.cards[21:24])
    cards_to_swap = list(player.hand[:3])
    
    game.perform_bottom_3(current_bidder_id, cards_to_swap)
    
    # Verify hand updated
    for kc in kitty_before:
        assert kc in player.hand
    
    # Check that each card in cards_to_swap is not in the hand,
    # UNLESS it was also in kitty_before (which we already ensured it wasn't).
    for sc in cards_to_swap:
        # Count how many times sc appears in player.hand
        count = sum(1 for c in player.hand if c == sc)
        # It should be 0 since we ensured swap_cards NOT in kitty_before
        assert count == 0, f"Card {sc} should not be in hand after swap"
        
    assert len(player.hand) == 5
    assert game.current_bidding.bottom_3_used is True

def test_perform_bottom_3_invalid_turn():
    game = Game(["P1", "P2", "P3", "P4"], bottom_3_enabled=True)
    game.start_new_hand()
    
    current_bidder_id = game.current_bidding.current_bidder
    wrong_player_id = (current_bidder_id + 1) % 4
    
    with pytest.raises(ValueError, match="You can only use Bottom 3 during your turn to bid"):
        game.perform_bottom_3(wrong_player_id, [])

def test_perform_bottom_3_invalid_rank():
    game = Game(["P1", "P2", "P3", "P4"], bottom_3_enabled=True)
    game.start_new_hand()
    
    current_bidder_id = game.current_bidding.current_bidder
    player = game.players[current_bidder_id]
    
    # Give player an Ace (invalid for swap)
    swap_cards = [
        Card(Suit.CLUBS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.TEN),
        Card(Suit.HEARTS, Rank.NINE)
    ]
    player.hand = swap_cards + player.hand[3:]
    
    with pytest.raises(ValueError, match="is not a 9 or 10"):
        game.perform_bottom_3(current_bidder_id, swap_cards)

def test_perform_bottom_3_already_used():
    game = Game(["P1", "P2", "P3", "P4"], bottom_3_enabled=True)
    game.start_new_hand()
    
    current_bidder_id = game.current_bidding.current_bidder
    player = game.players[current_bidder_id]
    
    swap_cards = [Card(Suit.CLUBS, Rank.NINE), Card(Suit.DIAMONDS, Rank.NINE), Card(Suit.HEARTS, Rank.NINE)]
    player.hand = swap_cards + player.hand[3:]
    
    # First time success
    game.perform_bottom_3(current_bidder_id, swap_cards)
    
    # Try again (even if they still have 9s/10s somehow)
    with pytest.raises(ValueError, match="Bottom 3 has already been used this hand"):
        game.perform_bottom_3(current_bidder_id, swap_cards)
