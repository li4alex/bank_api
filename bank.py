from account import Account
import maskpass
import base64
import random

class Bank:
    """Manages a collection of Account objects using a dictionary."""
    def __init__(self):
        # Stores accounts using account_num as the key, and the Account object as the value
        self.accounts = {
            1: Account(1, "Alice Smith", "123 Maple St", "12345", 1000),
            2: Account(2, "Bob Johnson", "456 Oak St", "67890", 500),
            3: Account(3, "Charlie Brown", "789 Pine St", "54321", 750)
        }
        self.account_creds = {
            1: base64.b64encode("alicepass".encode("utf-8")),
            2: base64.b64encode("bobpass".encode("utf-8")), 
            3: base64.b64encode("charliepass".encode("utf-8"))
        }

    def _generate_unique_account_num(self):
        """Generates a unique 6-digit random account number string."""
        while True:
            # Generate a random 6-digit number as a string (e.g., "482910")
            account_num = str(random.randint(100000, 999999))
            
            # Check for previously used account numbers
            if account_num not in self.accounts:
                return account_num

    def add_account(self, account_num, name, street_name, zip_code, start_balance = 0.0):
        """Instantiates a new Account and adds it to the system if the number is unique."""
        if account_num not in self.accounts:
            self.accounts[account_num] = Account(account_num, name, street_name, zip_code, start_balance)
            # Prompt the user to set a password for the new account and mask the input.
            pwd = maskpass.askpass(prompt="Set a password for this account: ", mask="*")
            # Encode the password using base64 for basic obfuscation before storing it.
            hashed_password = base64.b64encode(pwd.encode("utf-8"))
            self.account_creds[account_num] = hashed_password
            print(f"Account for {name} added successfully with account number {account_num}.")
        else:
            print("Account number already exists.")

    def verify_password(self, account_num):
        """Verifies the password for a given account number."""
        if account_num in self.account_creds:
            pwd = maskpass.askpass(prompt="Enter password: ", mask="*")
            hashed_password = self.account_creds[account_num]
            if base64.b64encode(pwd.encode("utf-8")) == hashed_password:
                print("Password verified successfully.")
                return True
            else:
                print("Incorrect password.")
                return False
        else:
            print("Account number not found.")
            return False

    def delete_account(self, account_num):
        """Removes an account from the system if it exists."""
        if account_num in self.accounts:
            del self.accounts[account_num]
            print(f"Account {account_num} deleted successfully.")
        else:
            print("Account number not found.")
    
    def show_all_accounts(self):
        """Prints details for all accounts in the system."""
        if self.accounts:
            print("All Accounts:")
            for account in self.accounts.values():
                account.details()
        else:
            print("No accounts available.")

    def get_account(self, account_num):
        """Helper method to safely retrieve an Account object or return None if missing."""
        return self.accounts.get(account_num, None)

    def show_account_details(self, account_num):
        """Finds an account and calls its internal detail presentation method."""
        account = self.get_account(account_num)
        if account:
            account.details()
        else:
            print("Account not found.")

    def deposit_to_account(self, account_num, amount):
        """Finds an account and processes an incoming deposit."""
        account = self.get_account(account_num)
        if account:
            account.deposit(amount)
        else:
            print("Account not found.")

    def withdraw_from_account(self, account_num, amount):
        """Finds an account and processes an outgoing withdrawal."""
        account = self.get_account(account_num)
        if account:
            account.withdraw(amount)
        else:
            print("Account not found.")

    def transfer_funds(self, source_account_num, destination_account_num, amount):
        """Transfers funds from the first account to the destination account if both exist."""
        source_account = self.get_account(source_account_num)
        destination_account = self.get_account(destination_account_num)

        if source_account and destination_account:
            if 0 < amount <= float(source_account.balance):
                source_account.transfer_source(amount, destination_account_num)
                destination_account.transfer_destination(amount, source_account_num)
                print(f"Transferred ${amount:.2f} from account {source_account_num} to {destination_account_num}.")
            else:
                print("Invalid transfer amount.")
        elif destination_account is None:
            print("Destination account not found.")

    def show_transaction_history(self, account_num):
        """Finds an account and prints its transactions."""
        account = self.get_account(account_num)
        if account:
            account.get_transaction_history()
        else:
            print("Account not found.")