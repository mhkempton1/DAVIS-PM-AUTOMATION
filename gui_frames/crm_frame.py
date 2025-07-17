import tkinter as tk
from tkinter import ttk, messagebox
from .base_frame import BaseModuleFrame

class CrmModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="CRM Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # Frame for adding a new customer
        add_customer_frame = ttk.LabelFrame(self, text="Add New Customer", padding=(10, 5))
        add_customer_frame.pack(pady=10, padx=10, fill="x")

        # Customer Name
        ttk.Label(add_customer_frame, text="Customer Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.customer_name_entry = ttk.Entry(add_customer_frame, width=40)
        self.customer_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Customer Type
        ttk.Label(add_customer_frame, text="Customer Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.customer_type_combo = ttk.Combobox(add_customer_frame, values=["Commercial", "Residential", "General Contractor", "Industrial"])
        self.customer_type_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Billing Address
        ttk.Label(add_customer_frame, text="Billing Address:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.billing_address_entry = ttk.Entry(add_customer_frame, width=40)
        self.billing_address_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        # Add Customer Button
        add_button = ttk.Button(add_customer_frame, text="Add Customer", command=self.add_customer)
        add_button.grid(row=3, column=0, columnspan=2, pady=10)

    def add_customer(self):
        customer_name = self.customer_name_entry.get()
        customer_type = self.customer_type_combo.get()
        billing_address = self.billing_address_entry.get()

        if not all([customer_name, customer_type, billing_address]):
            messagebox.showerror("Error", "All fields are required.")
            return

        success, message = self.module_instance.add_customer(customer_name, customer_type, billing_address)

        if success:
            messagebox.showinfo("Success", message)
            self.customer_name_entry.delete(0, tk.END)
            self.customer_type_combo.set('')
            self.billing_address_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", message)
