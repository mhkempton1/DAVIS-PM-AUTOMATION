import tkinter as tk
from tkinter import ttk, messagebox
from .base_frame import BaseModuleFrame
import datetime

class EstimateModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent, app, module_instance)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Estimate Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # Frame for creating a new estimate header
        header_frame = ttk.LabelFrame(self, text="Create Estimate Header", padding=(10, 5))
        header_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(header_frame, text="Estimate Number:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.estimate_number_entry = ttk.Entry(header_frame, width=40)
        self.estimate_number_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(header_frame, text="Project ID:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.project_id_entry = ttk.Entry(header_frame, width=40)
        self.project_id_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(header_frame, text="Customer Name:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.customer_name_entry_estimate = ttk.Entry(header_frame, width=40)
        self.customer_name_entry_estimate.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        create_header_button = ttk.Button(header_frame, text="Create Header", command=self.create_estimate_header)
        create_header_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Frame for adding line items
        line_item_frame = ttk.LabelFrame(self, text="Add Estimate Line Item", padding=(10, 5))
        line_item_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(line_item_frame, text="Estimate Number:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.line_item_estimate_number_entry = ttk.Entry(line_item_frame, width=40)
        self.line_item_estimate_number_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(line_item_frame, text="Line Number:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.line_number_entry = ttk.Entry(line_item_frame, width=40)
        self.line_number_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(line_item_frame, text="Description:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.description_entry = ttk.Entry(line_item_frame, width=40)
        self.description_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(line_item_frame, text="Quantity:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.quantity_entry = ttk.Entry(line_item_frame, width=40)
        self.quantity_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(line_item_frame, text="Unit of Measure:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.uom_entry = ttk.Entry(line_item_frame, width=40)
        self.uom_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(line_item_frame, text="Unit Price:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.unit_price_entry = ttk.Entry(line_item_frame, width=40)
        self.unit_price_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

        add_line_item_button = ttk.Button(line_item_frame, text="Add Line Item", command=self.add_estimate_line_item)
        add_line_item_button.grid(row=6, column=0, columnspan=2, pady=10)

    def create_estimate_header(self):
        estimate_number = self.estimate_number_entry.get()
        project_id = self.project_id_entry.get()
        customer_name = self.customer_name_entry_estimate.get()
        estimate_date = datetime.date.today().isoformat()

        if not all([estimate_number, project_id, customer_name]):
            messagebox.showerror("Error", "All fields are required.")
            return

        success, message = self.module_instance.create_estimate_header(estimate_number, project_id, customer_name, estimate_date)

        if success:
            messagebox.showinfo("Success", message)
            self.estimate_number_entry.delete(0, tk.END)
            self.project_id_entry.delete(0, tk.END)
            self.customer_name_entry_estimate.delete(0, tk.END)
        else:
            messagebox.showerror("Error", message)

    def add_estimate_line_item(self):
        estimate_number = self.line_item_estimate_number_entry.get()
        line_number = self.line_number_entry.get()
        description = self.description_entry.get()
        quantity = self.quantity_entry.get()
        uom = self.uom_entry.get()
        unit_price = self.unit_price_entry.get()

        if not all([estimate_number, line_number, description, quantity, uom, unit_price]):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            quantity = float(quantity)
            unit_price = float(unit_price)
        except ValueError:
            messagebox.showerror("Error", "Quantity and Unit Price must be numbers.")
            return

        success, message = self.module_instance.add_estimate_line_item(estimate_number, line_number, description, quantity, uom, unit_price)

        if success:
            messagebox.showinfo("Success", message)
            # Clear fields
            self.line_item_estimate_number_entry.delete(0, tk.END)
            self.line_number_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            self.quantity_entry.delete(0, tk.END)
            self.uom_entry.delete(0, tk.END)
            self.unit_price_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", message)
