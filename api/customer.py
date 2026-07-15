from fastapi import APIRouter, status, Depends, HTTPException
from database import database, account_collection
from api.schemas import AccountModel, TransactionSchema, TransferSchema
from api.dependencies import verify_customer_access

router = APIRouter(prefix="/customer", tags=["Customer Menu"])

@router.get("/{account_num}/details", response_model=AccountModel)
async def view_account_details(account_num: int):
    account = await account_collection.find_one({"_id": account_num})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account

@router.post("/{account_num}/deposit")
async def process_deposit(payload: TransactionSchema, account_num: int):
    account = await account_collection.find_one({"_id": account_num})
    account["balance"] += payload.amount
    await account_collection.update_one({"_id": account_num}, {"$set": {"balance": account["balance"]}})
    return {"message": f"Deposit processed. Current balance: ${account['balance']}"}

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

    # Record the transaction
    await database.get_collection("transactions").insert_one({
        "account_id": account_num,
        "type": "WITHDRAWAL",
        "amount": payload.amount,
        "description": "ATM Withdrawal"
    })

    return {"message": f"Withdrawal complete. Current balance: ${updated_account['balance']:.2f}"}


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

    # 4. Write history logs for both accounts
    tx_log = database.get_collection("transactions")
    await tx_log.insert_many([
        {
            "account_id": account_num, 
            "type": "TRANSFER_OUT", 
            "amount": payload.amount, 
            "to": payload.dest_account_num
        },
        {
            "account_id": payload.dest_account_num, 
            "type": "TRANSFER_IN", 
            "amount": payload.amount, 
            "from": account_num
        }
    ])

    return {"message": f"Successfully transferred ${payload.amount:.2f} to Account {payload.dest_account_num}."}


@router.get("/{account_num}/transactions")
async def view_transaction_history(
    account_num: int,
):
    # Fetch history directly from the standalone transactions collection
    cursor = database.get_collection("transactions").find({"account_id": account_num})
    history = await cursor.to_list(length=100) # Retrieve the last 100 entries

    # Clean up the MongoDB default _id representation for cleaner client responses
    for item in history:
        item["_id"] = str(item["_id"])

    return {"account_number": account_num, "history": history}