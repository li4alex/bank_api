from fastapi import APIRouter, status, Depends, HTTPException
from database import database, account_collection
from api.schemas import AccountModel, TokenResponse, TransactionSchema, TransferSchema, LoginRequest
from datetime import datetime, timezone
from security import get_current_account, verify_password, create_access_token
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/customer", tags=["Customer Menu"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    """Authenticate the customer and return a JWT access token."""
    # Retrieve the account and verify hashed password
    account_num = int(credentials.username)
    account = await account_collection.find_one({"_id": account_num})
    if not account or not verify_password(credentials.password, account["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Generate JWT token
    access_token = create_access_token(data={"sub": str(account_num)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/{account_num}/details", response_model=AccountModel)
async def view_account_details(account_num: int):
    account = await account_collection.find_one({"_id": account_num})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account

@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_account)):
    """
    A protected route that only logged-in users can access.
    Automatically retrieves the user profile based on the JWT bearer token.
    """
    return {
        "account_number": current_user["_id"],
        "name": current_user["name"],
        "street_name": current_user["street_name"],
        "zip_code": current_user["zip_code"],
        "current_balance": current_user["balance"]
    }

@router.post("/{account_num}/deposit")
async def process_deposit(payload: TransactionSchema, account_num: int):
    # 1. Verify Account exists
    account = await account_collection.find_one({"_id": account_num})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # 2. Generate Server Timestamp
    server_timestamp = datetime.now(timezone.utc)

    # 3. Create the Transaction Document
    transaction_doc = {
        "account_id": account_num,
        "type": "DEPOSIT",
        "amount": payload.amount,
        "timestamp": server_timestamp,  # Saved as native BSON Date
        "description": "Deposit via Web Portal"
    }
    tx_result = await database.transactions.insert_one(transaction_doc)

    # 4. Update Account Balance
    await account_collection.update_one({"_id": account_num},
                                        {"$set": {"balance": account["balance"] + payload.amount}})
    
    return {
        "message": f"Successfully deposited ${payload.amount:.2f}",
        "transaction_id": str(tx_result.inserted_id),
        "timestamp": server_timestamp.isoformat()
    }

@router.post("/{account_num}/withdraw")
async def process_withdrawal(
    payload: TransactionSchema, 
    account_num: int
):
    # Atomically find and update the balance *only if* there are sufficient funds
    updated_account = await account_collection.find_one_and_update(
        {
            "_id": account_num,
            "balance": {"$gte": payload.amount}  # Safety check: Balance must be >= withdrawal amount
        },
        {
            "$inc": {"balance": -payload.amount}  # Atomically subtract the balance
        },
        return_document=True  # Returns the updated document
    )

    if not updated_account:
        # Either the account doesn't exist, or it failed the balance condition ($gte)
        existing = await account_collection.find_one({"_id": account_num})
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds.")

    # Generate Server Timestamp
    server_timestamp = datetime.now(timezone.utc)

    # Create Transaction Record
    transaction_doc = {
        "account_id": account_num,
        "type": "WITHDRAW",
        "amount": payload.amount,
        "timestamp": server_timestamp,
        "description": "Withdrawal via Web Portal"
    }
    tx_result = await database.get_collection("transactions").insert_one(transaction_doc)

    return {
        "message": f"Successfully withdrew ${payload.amount:.2f}",
        "transaction_id": str(tx_result.inserted_id),
        "timestamp": server_timestamp.isoformat()
    }


@router.post("/{account_num}/transfer")
async def process_funds_transfer(
    payload: TransferSchema, 
    account_num: int
):

    # 1. Verify destination account exists
    dest_exists = await account_collection.find_one({"_id": payload.dest_account_num})
    if not dest_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination account not found.")

    # 2. Perform the transfer across two steps using a simulated database transaction.
    # Note: For production, wrap this sequence in a formal client session if using a MongoDB Replica Set.
    source_update = await account_collection.find_one_and_update(
        {"_id": account_num, "balance": {"$gte": payload.amount}},
        {"$inc": {"balance": -payload.amount}},
        return_document=True
    )

    if not source_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds in source account.")

    # 3. Add funds to the destination account
    await account_collection.update_one(
        {"_id": payload.dest_account_num},
        {"$inc": {"balance": payload.amount}}
    )

    server_timestamp = datetime.now(timezone.utc)

    # Sender Transaction Doc
    sender_tx = {
        "account_id": account_num,
        "type": "TRANSFER_OUT",
        "amount": payload.amount,
        "timestamp": server_timestamp,
        "to": payload.dest_account_num,
        "description": f"Transferred to Account #{payload.dest_account_num}"
    }
    await database.get_collection("transactions").insert_one(sender_tx)

    # Receiver Transaction Doc
    receiver_tx = {
        "account_id": payload.dest_account_num,
        "type": "TRANSFER_IN",
        "amount": payload.amount,
        "timestamp": server_timestamp,
        "from": account_num,
        "description": f"Received transfer from Account #{account_num}"
    }
    await database.get_collection("transactions").insert_one(receiver_tx)

    return {"message": f"Successfully transferred ${payload.amount:.2f} to Account #{payload.dest_account_num}.",
             "timestamp": server_timestamp.isoformat()
    }

@router.get("/{account_num}/transactions")
async def view_transaction_history(account_num: int):
    # Find all transactions linked to this account, sorted newest first
    cursor = database.get_collection("transactions").find({"account_id": account_num}).sort("timestamp", -1)
    history = await cursor.to_list(length=100) # Retrieve the last 100 entries

    # Clean up the MongoDB default _id representation for cleaner client responses
    for item in history:
        item["_id"] = str(item["_id"])

    return {"account_number": account_num, "history": history}