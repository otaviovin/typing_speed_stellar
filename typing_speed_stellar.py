from tkinter import *
import tkinter as tk
import time
import threading
import random
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset

class TypeSpeedGUI:
    def __init__(self):
        # Creates the main window
        self.window = Tk()
        self.window.title("Learning English. Speed Writing")  # Sets the window title
        self.window.geometry("800x700")  # Sets the window size

        # Loads the texts from an external text file and splits by line
        self.texts = open('text.txt', 'r').read().split("\n")

        # Creates a frame widget to organize the other widgets
        self.frame = Frame(self.window)

        # Displays a randomly selected sample text for the user to type
        self.sample_label = Label(self.frame, text=random.choice(self.texts), font=("Helvetica", 18))
        self.sample_label.grid(row=0, column=0, columnspan=2, padx=2, pady=10)

        # Text entry widget where the user types their text
        self.input_entry = Entry(self.frame, width=40, font=("Helvetica", 24))
        self.input_entry.grid(row=1, column=0, columnspan=2, padx=2, pady=10)
        self.input_entry.bind("<KeyPress>", self.start)  # Binds the key press event to the `start` function

        # Label to display speed-related information (CPS, CPM, WPM, etc.)
        self.speed_label = Label(self.frame, text="Speed: \n0.00 CPS \n000 CPM \n0.00 WPM \n0.00 WPS \n0.00 sec", font=("Helvetica", 18))
        self.speed_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        # Button to reset the game state
        self.reset_button = Button(self.frame, text="Reset", command=self.reset, font=("Helvetica", 24))
        self.reset_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Field to input the Stellar address and validation button
        self.address_label = Label(self.frame, text="Enter Address:", font=("Helvetica", 18))
        self.address_label.grid(row=4, column=0, padx=5, pady=10)
        self.address_entry = Entry(self.frame, width=60, font=("Helvetica", 10))
        self.address_entry.grid(row=4, column=1, padx=5, pady=10)
        self.define_button = Button(self.frame, text="Define", command=self.define_address, font=("Helvetica", 18))
        self.define_button.grid(row=5, column=0, columnspan=2, padx=5, pady=10)

        # Label to show the validation status of the Stellar address
        self.address_status_label = Label(self.frame, text="", font=("Helvetica", 14), fg="red")
        self.address_status_label.grid(row=6, column=0, columnspan=2)

        # Label to show the current XLM balance of the defined address
        self.balance_label = Label(self.frame, text="Balance: 0 XLM", font=("Helvetica", 18))
        self.balance_label.grid(row=7, column=0, columnspan=2, padx=5, pady=10)

        # Label explaining the reward system based on time taken
        self.level_label = Label(self.frame, text="Reward: down 5s (3 XLM), 5s to 8s (2 XLM), 8s to 10 s (1 XLM)", font=("Helvetica", 18))
        self.level_label.grid(row=8, column=0, columnspan=2, pady=10)

        # Adds the frame to the window
        self.frame.pack()

        # Initialize control variables
        self.counter = 0  # Typing time counter
        self.running = False  # Flag to indicate if the game is running
        self.target_address = ""  # Stellar address to send XLM to
        self.server = Server("https://horizon-testnet.stellar.org")  # Connect to the Stellar Testnet server

        # Starts the Tkinter main event loop
        self.window.mainloop()

    def define_address(self):
        """Defines and validates the Stellar address entered by the user."""
        self.target_address = self.address_entry.get()
        try:
            # Verifies if the address exists on the Testnet
            account = self.server.accounts().account_id(self.target_address).call()
            self.address_status_label.config(text="Address exists!", fg="green")
            self.check_balance()  # Checks the balance of the address after validation
        except Exception:
            # If the address is invalid or does not exist
            self.address_status_label.config(text="Address does not exist on testnet.", fg="red")

    def check_balance(self):
        """Checks the XLM balance of the defined Stellar address."""
        if self.target_address:
            try:
                # Fetches the account's balance
                account = self.server.accounts().account_id(self.target_address).call()
                balance = next((item for item in account['balances'] if item['asset_type'] == 'native'), None)
                if balance:
                    # Updates the balance display with the correct value
                    self.balance_label.config(text=f"Balance: {balance['balance']} XLM")
                else:
                    self.balance_label.config(text="Balance: 0 XLM")
            except Exception:
                # If there's an error, display balance as zero
                self.balance_label.config(text="Balance: 0 XLM")

    def start(self, event):
        """Starts the typing speed game when a key is pressed."""
        if not self.target_address:
            # Prompts the user to define a valid address first
            self.address_status_label.config(text="Please define a valid address first.", fg="red")
            return

        if not self.running:
            # Starts the timer when the user starts typing, ignoring shift keys
            if not event.keycode in [16, 17, 18]:
                self.running = True
                t = threading.Thread(target=self.time_thread)  # Starts a timer in a separate thread
                t.start()

        # Verifies if the user's typed text matches the target text
        if not self.sample_label.cget('text').startswith(self.input_entry.get()):
            self.input_entry.config(fg='red')  # Changes text color to red for errors
        else:
            self.input_entry.config(fg='black')  # Resets to black for correct input

        # If the user finishes typing correctly, end the game
        if self.input_entry.get() == self.sample_label.cget('text')[:-1]:
            self.running = False
            self.input_entry.config(fg='green')  # Changes the text color to green when finished

            # Determine reward based on the time taken
            if self.counter < 50:
                self.level_var = 3  # Highest reward (3 XLM) for fastest typing
                threading.Thread(target=self.handle_win).start()  # Start the win process
            elif 50 <= self.counter < 80:
                self.level_var = 2  # Mid-range reward (2 XLM)
                threading.Thread(target=self.handle_win).start()
            elif 80 <= self.counter < 100:
                self.level_var = 1  # Lowest reward (1 XLM)
                threading.Thread(target=self.handle_win).start()
            else:
                # No reward for typing too slow
                self.address_status_label.config(text="You lost. You didn't get the XLM reward. Try faster!", fg="red")
            print(self.level_var)

    def handle_win(self):
        """Handles the post-win behavior by transferring the reward."""
        time.sleep(2)  # Delay before initiating the XLM transfer
        self.transfer_xlm(self.level_var)

    def transfer_xlm(self, level_var):
        """Transfers XLM based on the reward level."""
        source_address = "GDNKWPRX57FAJPHVS4CN7TWHPQ2MQYWNFPVOJV2TD2BTATDIQWP6GHY3"  # Source address for sending XLM
        source_secret = "SCBGRSEGKRMYTMTNYROQZNHD4PBP42VWXYGZROPISOHEPW7NE2LLG3NH"  # Secret key of the source address
        source_keypair = Keypair.from_secret(source_secret)  # Create a keypair from the secret

        # Select the reward based on the difficulty level
        if self.level_var == 1:
            reward = "1"  # 1 XLM for level 1
        elif self.level_var == 2:
            reward = "2"  # 2 XLM for level 2
        else:
            reward = "3"  # 3 XLM for level 3

        try:
            # Create a transaction and add a payment operation to transfer XLM
            source_account = self.server.load_account(source_address)
            transaction = (
                TransactionBuilder(
                    source_account=source_account,
                    network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                    base_fee=100,
                )
                .add_text_memo(f"Congrats. You won {reward} XLM!")  # Adds a memo for the transaction
                .append_payment_op(self.target_address, Asset.native(), reward)  # Payment operation
                .set_timeout(30)
                .build()
            )

            transaction.sign(source_keypair)  # Signs the transaction
            response = self.server.submit_transaction(transaction)  # Submits the transaction
            print(f"Transaction Successful: {response}")
        except Exception as e:
            # Handles any exceptions that occur during the transaction process
            print(f"Transaction failed: {e}")

    def time_thread(self):
        """Tracks the time taken for the typing test."""
        while self.running:
            time.sleep(1)
            self.counter += 1
            self.update_speed()

    def update_speed(self):
        """Updates the speed statistics (CPS, CPM, WPM)."""
        cps = self.counter / len(self.input_entry.get())  # Characters per second
        cpm = cps * 60  # Characters per minute
        wpm = cpm / 5  # Words per minute (assuming average word length of 5 characters)
        wps = cps / 5  # Words per second
        seconds = self.counter  # Time in seconds

        # Updates the speed label with the new values
        self.speed_label.config(
            text=f"Speed: \n{cps:.2f} CPS \n{cpm:.0f} CPM \n{wpm:.2f} WPM \n{wps:.2f} WPS \n{seconds:.2f} sec"
        )

    def reset(self):
        """Resets the game state for a new round."""
        self.running = False
        self.counter = 0
        self.sample_label.config(text=random.choice(self.texts))  # Change sample text
        self.input_entry.delete(0, END)  # Clears the input field
        self.input_entry.config(fg='black')  # Resets text color
        self.speed_label.config(text="Speed: \n0.00 CPS \n000 CPM \n0.00 WPM \n0.00 WPS \n0.00 sec")  # Reset speed

# Creates and runs the GUI instance
TypeSpeedGUI()
