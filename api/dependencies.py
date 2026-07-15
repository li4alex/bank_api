from fastapi import Header, HTTPException, status
from database import account_collection

async def verify_customer_access(x_account_number: str = Header(..., description="The account number accessing this resource")):
    try:
        # Check database using integer key conversion matching our model standard
        account = await account_collection.find_one({"_id": int(x_account_number)})
    except ValueError:
        account = None

    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authentication failed: Invalid account number."
        )
    return int(x_account_number)