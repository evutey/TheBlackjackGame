import random
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional
import sqlite3
from datetime import datetime


class CardSuit(Enum):
    """Represents card suits."""
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'


class Card:
    """Advanced card representation."""
    def __init__(self, rank: int, suit: CardSuit):
        if rank < 1 or rank > 13:
            raise ValueError("Card rank must be between 1 and 13")
        
        self.rank = rank
        self.suit = suit

    @property
    def value(self) -> int:
        """Calculate card value for Blackjack."""
        if self.rank > 10:
            return 10
        elif self.rank == 1:  # Ace
            return 11
        return self.rank

    def __repr__(self):
        rank_names = {
            1: 'A', 11: 'J', 12: 'Q', 13: 'K'
        }
        rank_str = rank_names.get(self.rank, str(self.rank))
        return f"{rank_str}{self.suit.value}"


class Deck:
    """Sophisticated deck with multiple deck support."""
    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.reset()

    def reset(self):
        """Recreate the deck with full cards."""
        self.cards = [
            Card(rank, suit) 
            for suit in CardSuit 
            for rank in range(1, 14) 
            for _ in range(self.num_decks)
        ]
        random.shuffle(self.cards)

    def draw_card(self) -> Card:
        """Draw a card, reshuffling if empty."""
        if not self.cards:
            self.reset()
        return self.cards.pop()


class Hand:
    """Represents a player's hand in Blackjack."""
    def __init__(self):
        self.cards: List[Card] = []

    def add_card(self, card: Card):
        """Add a card to the hand."""
        self.cards.append(card)

    def calculate_score(self) -> int:
        """Calculate hand score with Ace handling."""
        # Separate aces and non-aces
        non_aces = [card for card in self.cards if card.rank != 1]
        aces = [card for card in self.cards if card.rank == 1]

        # Calculate base score
        score = sum(card.value for card in non_aces)

        # Handle aces
        for ace in aces:
            if score + 11 <= 21:
                score += 11
            else:
                score += 1

        return score

    def is_blackjack(self) -> bool:
        """Check if hand is a Blackjack."""
        return len(self.cards) == 2 and self.calculate_score() == 21

    def __str__(self):
        return ', '.join(str(card) for card in self.cards)


class Player:
    """Represents a player in the Blackjack game."""
    def __init__(self, name: str, balance: float = 1000.0):
        self.name = name
        self.balance = balance
        self.hand = Hand()

    def bet(self, amount: float) -> bool:
        """Place a bet if sufficient balance."""
        if amount > self.balance:
            return False
        self.balance -= amount
        return True

    def add_card(self, card: Card):
        """Add a card to the player's hand."""
        self.hand.add_card(card)


class BlackjackGame:
    """Main Blackjack game logic."""
    def __init__(self, player: Player):
        self.deck = Deck()
        self.player = player
        self.dealer = Player("Dealer")
        self.logger = logging.getLogger(__name__)

    def play_round(self, bet_amount: float) -> str:
        """Play a complete round of Blackjack."""
        # Reset hands
        self.player.hand = Hand()
        self.dealer.hand = Hand()

        # Initial bet
        if not self.player.bet(bet_amount):
            return "Insufficient funds"

        # Initial deal
        for _ in range(2):
            self.player.add_card(self.deck.draw_card())
            self.dealer.add_card(self.deck.draw_card())

        # Check for immediate Blackjacks
        if self.player.hand.is_blackjack():
            if not self.dealer.hand.is_blackjack():
                self._pay_winnings(bet_amount, 2.5)
                return "Win"
            return "Push"

        # Player's turn
        player_result = self._player_turn()
        if player_result == "Bust":
            return "Lose"

        # Dealer's turn
        dealer_result = self._dealer_turn()
        if dealer_result == "Bust":
            self._pay_winnings(bet_amount, 2)
            return "Win"

        # Compare hands
        return self._compare_hands(bet_amount)

    def _player_turn(self) -> str:
        """Handle player's turn."""
        while True:
            self._display_game_state(hide_dealer_card=True)
            
            # Prevent further hits if already at 21
            if self.player.hand.calculate_score() == 21:
                return "Stand"

            # Prompt for action
            action = input("Do you want to (H)it or (S)tand? ").lower()
            
            if action in ['h', 'hit']:
                self.player.add_card(self.deck.draw_card())
                
                # Check for bust
                if self.player.hand.calculate_score() > 21:
                    self._display_game_state()
                    print(f"{self.player.name} busted!")
                    return "Bust"
            elif action in ['s', 'stand']:
                return "Stand"
            else:
                print("Invalid input. Please enter 'H' to hit or 'S' to stand.")

    def _dealer_turn(self) -> str:
        """Handle dealer's turn."""
        while self.dealer.hand.calculate_score() < 17:
            self.dealer.add_card(self.deck.draw_card())
        
        if self.dealer.hand.calculate_score() > 21:
            return "Bust"
        return "Stand"

    def _compare_hands(self, bet_amount: float) -> str:
        """Compare player and dealer hands."""
        player_score = self.player.hand.calculate_score()
        dealer_score = self.dealer.hand.calculate_score()

        # Display final hands
        print("\nFinal Hands:")
        print(f"{self.player.name}: {self.player.hand} (Score: {player_score})")
        print(f"Dealer: {self.dealer.hand} (Score: {dealer_score})")

        # Determine winner
        if player_score > dealer_score:
            self._pay_winnings(bet_amount, 2)
            return "Win"
        elif player_score < dealer_score:
            return "Lose"
        else:
            # Push (tie) - return bet
            self.player.balance += bet_amount
            return "Push"

    def _pay_winnings(self, bet_amount: float, multiplier: float):
        """Pay winnings to the player."""
        winnings = bet_amount * multiplier
        self.player.balance += winnings
        print(f"You won ${winnings:.2f}!")

    def _display_game_state(self, hide_dealer_card: bool = False):
        """Display current game state."""
        print("\nCurrent Game State:")
        print(f"{self.player.name}'s Hand: {self.player.hand} (Score: {self.player.hand.calculate_score()})")
        
        if hide_dealer_card:
            print(f"Dealer's Hand: {self.dealer.hand.cards[0]} <hidden card>")
        else:
            print(f"Dealer's Hand: {self.dealer.hand} (Score: {self.dealer.hand.calculate_score()})")


def main():
    """Game runner."""
    logging.basicConfig(level=logging.INFO)

    # Setup player
    name = input("Enter your name: ")
    player = Player(name)

    while True:
        # Display current balance
        print(f"\nCurrent Balance: ${player.balance:.2f}")

        # Get bet amount
        try:
            bet = float(input("Enter bet amount (or 0 to quit): "))
            
            # Exit condition
            if bet == 0:
                break

            # Validate bet
            if bet <= 0 or bet > player.balance:
                print("Invalid bet amount. Please try again.")
                continue

            # Play game
            game = BlackjackGame(player)
            result = game.play_round(bet)

            # Display result
            print(f"\nGame Result: {result}")
            print(f"New Balance: ${player.balance:.2f}")

        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"An error occurred: {e}")

    print("Thanks for playing!")


if __name__ == "__main__":
    main()
