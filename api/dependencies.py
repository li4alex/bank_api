from fastapi import Header, HTTPException, status
from bank import Bank

# Shared single instance of the Bank infrastructure across the whole API
bank_instance = Bank()

def verify_customer_access(x_account_number: str = Header(..., description="The account number accessing this resource")):
    account = bank_instance.get_account(x_account_number)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication failed: Invalid account number."
        )
    return x_account_number