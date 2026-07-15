from fastapi import APIRouter, status, Depends, HTTPException
from database import database, account_collection
from api.schemas import AccountModel, TransactionSchema, TransferSchema
from api.dependencies import verify_customer_access
from datetime import datetime, timezone

router = APIRouter(prefix="/customer", tags=["Customer Menu"])

@router.get("/{account_num}/details", response_model=AccountModel)
async def view_account_details(account_num: int):
    account = await account_collection.find_one({"_id": account_num})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account

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
                                        {"$set": {"balance": account["balance"]}})
    
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

    # Update Account Balance
    await database.get_collection("accounts").update_one(
        {"_id": account_num},
        {"$inc": {"balance": -payload.amount}}
    )

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