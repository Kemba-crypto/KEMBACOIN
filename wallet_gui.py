# © 2024 The Nation of Tamarikemba and Kembacoin Developers  
# © 2024 Ha Malak BN Adam Aman RA  

import os
import logging
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import qrcode
from wallet import Wallet

logging.basicConfig(level=logging.INFO)


class KembacoinWalletApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kembacoin Wallet")
        self.root.geometry("400x600")
        self.wallet = None
        self.blockchain_url = "http://127.0.0.1:5000"
        self.logo_path = os.path.abspath("kembacoin7/kembacoin Logo/sealfinalkemcoin.png")
        self.qr_code_path = "wallet_qr.png"  # Path to save the QR code

        # Create main UI
        self.create_main_screen()

    def create_main_screen(self):
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Logo
        if os.path.exists(self.logo_path):
            try:
                logo = tk.PhotoImage(file=self.logo_path)
                logo_label = tk.Label(self.root, image=logo)
                logo_label.image = logo  # Keep reference to prevent garbage collection
                logo_label.pack(pady=10)
            except Exception as e:
                logging.warning(f"Failed to load logo: {e}")

        # Password entry
        self.password_var = tk.StringVar()
        tk.Label(self.root, text="Enter Wallet Password:").pack(pady=5)
        password_entry = tk.Entry(self.root, textvariable=self.password_var, show="*")
        password_entry.pack(pady=5)

        # Buttons
        ttk.Button(self.root, text="Create Wallet", command=self.create_wallet).pack(pady=5)
        ttk.Button(self.root, text="Login", command=self.login_wallet).pack(pady=5)

        # Warning
        tk.Label(
            self.root,
            text="WARNING: Keep your password safe.\nLosing it will result in permanent wallet loss.",
            fg="red",
            wraplength=300,
        ).pack(pady=10)

    def create_wallet(self):
        password = self.password_var.get().strip()
        if not password:
            messagebox.showerror("Error", "Password cannot be empty!")
            return

        try:
            self.wallet = Wallet(password=password, blockchain_url=self.blockchain_url)
            self.wallet.create_new_wallet()
            logging.info("Wallet created successfully.")
            messagebox.showinfo("Success", f"Wallet created successfully!\nAddress: {self.wallet.address}")
            self.generate_qr_code(self.wallet.address)  # Generate QR code
            self.show_wallet_screen()
        except Exception as e:
            logging.error(f"Failed to create wallet: {e}")
            messagebox.showerror("Error", "Failed to create wallet. Please try again.")

    def login_wallet(self):
        password = self.password_var.get().strip()
        if not password:
            messagebox.showerror("Error", "Password cannot be empty!")
            return

        try:
            self.wallet = Wallet(password=password, blockchain_url=self.blockchain_url)
            self.wallet.load_wallet(password)
            logging.info("Wallet loaded successfully.")
            messagebox.showinfo("Success", f"Wallet loaded successfully!\nAddress: {self.wallet.address}")
            self.generate_qr_code(self.wallet.address)  # Generate QR code
            self.show_wallet_screen()
        except ValueError as e:
            logging.error(f"Failed to load wallet: {e}")
            messagebox.showerror("Error", f"Invalid password or corrupted wallet file: {e}")
        except Exception as e:
            logging.error(f"Unexpected error while loading wallet: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def show_wallet_screen(self):
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Wallet details
        tk.Label(self.root, text="Wallet Address:", font=("Arial", 12)).pack(pady=5)
        address_label = tk.Label(self.root, text=self.wallet.address, font=("Arial", 10), wraplength=350, fg="blue")
        address_label.pack(pady=5)

        tk.Label(self.root, text=f"Balance: {self.wallet.refresh_balance():.2f} KEM", font=("Arial", 12)).pack(pady=5)

        # QR Code
        if os.path.exists(self.qr_code_path):
            try:
                qr_image = Image.open(self.qr_code_path)
                qr_photo = ImageTk.PhotoImage(qr_image)
                qr_label = tk.Label(self.root, image=qr_photo)
                qr_label.image = qr_photo  # Keep reference to prevent garbage collection
                qr_label.pack(pady=10)
            except Exception as e:
                logging.error(f"Failed to display QR code: {e}")

        # Frame for Action Buttons
        action_frame = tk.Frame(self.root)
        action_frame.pack(pady=20)

        # Send KEM
        tk.Label(self.root, text="Recipient Address:").pack(pady=5)
        self.recipient_var = tk.StringVar()
        recipient_entry = tk.Entry(self.root, textvariable=self.recipient_var, width=40)
        recipient_entry.pack(pady=5)

        tk.Label(self.root, text="Amount:").pack(pady=5)
        self.amount_var = tk.StringVar()
        amount_entry = tk.Entry(self.root, textvariable=self.amount_var, width=20)
        amount_entry.pack(pady=5)

        ttk.Button(action_frame, text="Send KEM", command=self.send_kem).grid(row=0, column=0, padx=10)
        ttk.Button(action_frame, text="Export Wallet", command=self.export_wallet).grid(row=0, column=1, padx=10)
        ttk.Button(action_frame, text="Logout", command=self.create_main_screen).grid(row=0, column=2, padx=10)

    def generate_qr_code(self, data):
        """
        Generate a QR code for the wallet address and save it as an image.
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img.save(self.qr_code_path)
            logging.info(f"QR Code generated and saved to {self.qr_code_path}.")
        except Exception as e:
            logging.error(f"Failed to generate QR code: {e}")

    def send_kem(self):
        recipient = self.recipient_var.get().strip()
        amount = self.amount_var.get().strip()
        if not recipient or not amount:
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            response = self.wallet.send_transaction(recipient, float(amount))
            if "error" in response:
                raise Exception(response["error"])
            logging.info("Transaction successful.")
            messagebox.showinfo("Success", "Transaction sent successfully!")
            self.show_wallet_screen()
        except Exception as e:
            logging.error(f"Transaction failed: {e}")
            messagebox.showerror("Error", f"Transaction failed. Reason: {e}")

    def export_wallet(self):
        export_path = "wallet_export.json"
        try:
            self.wallet.export_wallet(export_path)
            logging.info(f"Wallet exported to {export_path}")
            messagebox.showinfo("Success", f"Wallet exported successfully to {export_path}.")
        except Exception as e:
            logging.error(f"Failed to export wallet: {e}")
            messagebox.showerror("Error", "Failed to export wallet. Please try again.")


if __name__ == "__main__":
    root = tk.Tk()
    app = KembacoinWalletApp(root)
    root.mainloop()

