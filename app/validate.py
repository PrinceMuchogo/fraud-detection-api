import requests
from datetime import datetime

def luhn_check(card_number: str) -> bool:
    """Implement Luhn's algorithm to validate the card number."""
    digits = [int(d) for d in card_number[::-1]]
    checksum = sum(digits[0::2]) + sum(sum(divmod(2 * d, 10)) for d in digits[1::2])
    return checksum % 10 == 0

def bin_lookup(card_number: str) -> dict:
    """Lookup card information using the BIN (first 6 digits)."""
    bin_number = card_number[:6]  # Get the first 6 digits
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Unable to fetch card info (Status code: {response.status_code})"}
    except Exception as e:
        return {"error": str(e)}

def expiry_check(exp_month: int, exp_year: int) -> bool:
    """Check if the card has expired."""
    current_date = datetime.now()
    if exp_year < current_date.year or (exp_year == current_date.year and exp_month < current_date.month):
        print("Card has expired.")
        return False
    return True

def validate_card(card_number: str, exp_month: int, exp_year: int, cvv: str) -> bool:
    # Check card number format using Luhn's algorithm
    if not luhn_check(card_number):
        print("Invalid card number format (Luhn check failed).")
        return False

    # Check card expiration date
    if not expiry_check(exp_month, exp_year):
        print("Card is expired.")
        return False

    # Perform BIN lookup for additional validation
    bin_info = bin_lookup(card_number)
    if "error" in bin_info:
        print(f"BIN lookup failed: {bin_info['error']}")
        return False

    # Check for known invalid BIN ranges or invalid data
    card_type = bin_info.get("type", "Unknown")
    card_scheme = bin_info.get("scheme", "Unknown")
    bank_name = bin_info.get("bank", {}).get("name", "Unknown")

    if card_type not in ["debit", "credit"]:
        print("Invalid card type or unknown BIN.")
        return False

    print(f"Card brand: {card_scheme}, Type: {card_type}, Bank: {bank_name}")
    print("Card is valid and active.")
    return True
