from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
from fastapi import Depends, HTTPException, status
from database import account_collection
from api.schemas import CustomerInDB

SECRET_KEY = "f56b1f98ae876ed668bd95e2fc777ef4c8564565cf1926ee259d869ab1d69e9c"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/customer/login")

DUMMY_HASH = password_hash.hash("dummypassword")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_account(database, account_num: int):
    if account_num in database:
        user_dict = database[account_num]
        return CustomerInDB(**user_dict)
    
def authenticate_user(database, account_num: int, password: str):
    account = get_account(database, account_num)
    if not account:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, account.hashed_password):
        return False
    return account

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_account(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency that extracts the JWT token, validates it, 
    and retrieves the corresponding account from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT token using pyjwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub_value = payload.get("sub")
        
        if sub_value is None:
            raise credentials_exception
        account_number = int(sub_value)
    
    except InvalidTokenError as e:
        raise credentials_exception
    except ValueError as e:
        raise credentials_exception

    # Query the database for the account linked to the token
    account = await account_collection.find_one({"_id": account_number})
    if account is None:
        raise credentials_exception
    return account