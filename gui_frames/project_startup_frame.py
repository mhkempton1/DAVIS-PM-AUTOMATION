import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import os
# from datetime import datetime # No longer needed here, backend handles it
from .base_frame import BaseModuleFrame
from configuration import Config # For Config.get_data_dir()
# from database_manager import db_manager # No longer needed for direct calls here
from tkPDFViewer import tkPDFViewer # For PDF viewing

# Logger setup
import logging
logger = logging.getLogger(__name__)

class ProjectStartupModuleFrame(BaseModuleFrame):
    def __init__(self, parent, app, module_instance=None):
        # Initialize attributes that are configured in on_active_project_changed or create_widgets
        self.execute_dna_button = None
        self.add_drawing_button = None
        self.view_drawing_button = None
        self.drawings_tree = None
        self.adhoc_project_id_entry = None
        self.wbs_id_entry = None
        self.wbs_entries = {}
        # self.project_tree = None # This seems to be part of the main app's sidebar now

        super().__init__(parent, app, module_instance)
        self.create_widgets() # Call after super and attribute initialization

    def create_widgets(self):
        tk.Label(self, text="Project Startup Module", font=("Arial", 14, "bold")).pack(pady=10, padx=10)

        # Project Creation UI has been moved to IntegrationDataProcessingModuleFrame
        # A note can be placed here if desired, or just omit this section.
        # tk.Label(self, text="Project creation is now handled in 'Integration & Data Processing' module.").pack(pady=5)

        # Frame for "Execute Data DNA" and other active project actions
        active_project_actions_frame = ttk.LabelFrame(self, text="Active Project Actions")
        active_project_actions_frame.pack(pady=10, padx=20, fill="x")
        active_project_actions_frame.columnconfigure(0, weight=1)

        self.execute_dna_button = ttk.Button(active_project_actions_frame, text="Execute Data DNA (Link Estimates & Plan)", command=self.execute_data_dna_action)
        self.execute_dna_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        common_id_frame = ttk.LabelFrame(self, text="Ad-hoc Actions (Specify Project ID)")
        common_id_frame.pack(pady=10, padx=20, fill="x")
        common_id_frame.columnconfigure(1, weight=1)
        tk.Label(common_id_frame, text="Project ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.adhoc_project_id_entry = tk.Entry(common_id_frame)
        self.adhoc_project_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(common_id_frame, text="Generate WBS (Ad-hoc)", command=self.generate_wbs_action).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(common_id_frame, text="Generate Budget (Ad-hoc)", command=self.generate_budget_action).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(common_id_frame, text="Allocate Resources (Ad-hoc)", command=self.allocate_resources_action).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        wbs_manage_frame = ttk.LabelFrame(self, text="Manage WBS Element")
        wbs_manage_frame.pack(pady=10, padx=20, fill="x")
        wbs_manage_frame.columnconfigure(1, weight=1)

        tk.Label(wbs_manage_frame, text="WBS Element ID:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.wbs_id_entry = tk.Entry(wbs_manage_frame)
        self.wbs_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(wbs_manage_frame, text="Load Details", command=self.load_wbs_details_action).grid(row=0, column=2, padx=5, pady=2)

        wbs_fields = [
            ("Description:", "wbs_description_entry", 1),
            ("Estimated Cost:", "wbs_est_cost_entry", 2),
            ("Status:", "wbs_status_entry", 3),
            ("Start Date (YYYY-MM-DD):", "wbs_start_date_entry", 4),
            ("End Date (YYYY-MM-DD):", "wbs_end_date_entry", 5)
        ]
        self.wbs_entries = {} # Ensure it's initialized
        for label_text, entry_attr_name, row_num in wbs_fields:
            tk.Label(wbs_manage_frame, text=label_text).grid(row=row_num, column=0, padx=5, pady=2, sticky="w")
            entry = tk.Entry(wbs_manage_frame)
            entry.grid(row=row_num, column=1, columnspan=2, padx=5, pady=2, sticky="ew")
            self.wbs_entries[entry_attr_name] = entry

        ttk.Button(wbs_manage_frame, text="Update WBS Element", command=self.update_wbs_action).grid(row=len(wbs_fields) + 1, column=0, columnspan=3, pady=10)

        drawings_frame = ttk.LabelFrame(self, text="Design Drawings")
        drawings_frame.pack(pady=10, padx=20, fill="both", expand=True)

        import_data_frame = ttk.LabelFrame(self, text="Import Project Data (e.g. Turnover File)")
        import_data_frame.pack(pady=10, padx=20, fill="x")
        import_data_button = ttk.Button(import_data_frame, text="Import From CSV", command=self.import_data_action)
        import_data_button.pack(pady=10)

        self.add_drawing_button = ttk.Button(drawings_frame, text="Add Design Drawing", command=self.add_drawing_action)
        self.add_drawing_button.pack(side="left", padx=5, pady=5)

        self.view_drawing_button = ttk.Button(drawings_frame, text="View Selected Drawing", command=self.view_drawing_action)
        self.view_drawing_button.pack(side="left", padx=5, pady=5)

        self.drawings_tree = ttk.Treeview(drawings_frame, selectmode="browse")
        self.drawings_tree["columns"] = ("Name", "FilePath", "UploadDate", "Description")
        self.drawings_tree.column("#0", width=0, stretch=tk.NO) # Hide the first default column
        self.drawings_tree.column("Name", anchor=tk.W, width=200)
        self.drawings_tree.column("FilePath", anchor=tk.W, width=300)
        self.drawings_tree.column("UploadDate", anchor=tk.W, width=150)
        self.drawings_tree.column("Description", anchor=tk.W, width=250)

        self.drawings_tree.heading("Name", text="Drawing Name", anchor=tk.W)
        self.drawings_tree.heading("FilePath", text="File Path", anchor=tk.W)
        self.drawings_tree.heading("UploadDate", text="Upload Date", anchor=tk.W)
        self.drawings_tree.heading("Description", text="Description", anchor=tk.W)

        drawings_scrollbar = ttk.Scrollbar(drawings_frame, orient="vertical", command=self.drawings_tree.yview)
        self.drawings_tree.configure(yscrollcommand=drawings_scrollbar.set)

        # Pack scrollbar first, then treeview to ensure proper layout
        drawings_scrollbar.pack(side="right", fill="y")
        self.drawings_tree.pack(side="left", fill="both", expand=True)

        self.on_active_project_changed() # Set initial button states and load drawings if project active

    # load_project_list method was for a treeview within this frame,
    # but project list is now in the main app's sidebar. So, this method is likely obsolete here.
    # def load_project_list(self): ...

    def load_wbs_details_action(self):
        wbs_id_str = self.wbs_id_entry.get().strip()
        if not wbs_id_str:
            self.show_message("Input Error", "Please enter a WBS Element ID.", True)
            return
        try:
            wbs_id = int(wbs_id_str)
        except ValueError:
            self.show_message("Input Error", "WBS Element ID must be a number.", True)
            return

        if self.module and hasattr(self.module, 'get_wbs_element_details'):
            details = self.module.get_wbs_element_details(wbs_id)
            if details:
                self.wbs_entries['wbs_description_entry'].delete(0, tk.END)
                self.wbs_entries['wbs_description_entry'].insert(0, details.get('Description', ''))
                self.wbs_entries['wbs_est_cost_entry'].delete(0, tk.END)
                self.wbs_entries['wbs_est_cost_entry'].insert(0, str(details.get('EstimatedCost', '0.0')))
                self.wbs_entries['wbs_status_entry'].delete(0, tk.END)
                self.wbs_entries['wbs_status_entry'].insert(0, details.get('Status', ''))
                self.wbs_entries['wbs_start_date_entry'].delete(0, tk.END)
                self.wbs_entries['wbs_start_date_entry'].insert(0, details.get('StartDate', ''))
                self.wbs_entries['wbs_end_date_entry'].delete(0, tk.END)
                self.wbs_entries['wbs_end_date_entry'].insert(0, details.get('EndDate', ''))
                self.show_message("WBS Details", f"Details for WBS ID {wbs_id} loaded.")
            else:
                self.show_message("Not Found", f"WBS Element with ID {wbs_id} not found.", True)
                for entry in self.wbs_entries.values(): entry.delete(0, tk.END)
        else:
            self.show_message("Error", "Project Startup module or get_wbs_element_details method not available.", True)

    def update_wbs_action(self):
        wbs_id_str = self.wbs_id_entry.get().strip()
        if not wbs_id_str:
            self.show_message("Input Error", "Please enter a WBS Element ID to update.", True)
            return
        try:
            wbs_id = int(wbs_id_str)
        except ValueError:
            self.show_message("Input Error", "WBS Element ID must be a number.", True)
            return

        updates = {}
        # Populate updates from entry fields
        if self.wbs_entries['wbs_description_entry'].get().strip():
            updates['Description'] = self.wbs_entries['wbs_description_entry'].get().strip()
        if self.wbs_entries['wbs_est_cost_entry'].get().strip():
            try:
                updates['EstimatedCost'] = float(self.wbs_entries['wbs_est_cost_entry'].get().strip())
            except ValueError:
                self.show_message("Input Error", "Estimated Cost must be a valid number.", True)
                return
        if self.wbs_entries['wbs_status_entry'].get().strip():
            updates['Status'] = self.wbs_entries['wbs_status_entry'].get().strip()
        if self.wbs_entries['wbs_start_date_entry'].get().strip():
            updates['StartDate'] = self.wbs_entries['wbs_start_date_entry'].get().strip() # Add date validation
        if self.wbs_entries['wbs_end_date_entry'].get().strip():
            updates['EndDate'] = self.wbs_entries['wbs_end_date_entry'].get().strip() # Add date validation

        if not updates:
            self.show_message("No Changes", "No new values provided to update.")
            return

        if self.module and hasattr(self.module, 'update_wbs_element'):
            success, message = self.module.update_wbs_element(wbs_id, updates)
            self.show_message("Update WBS", message, not success)
            if success:
                self.load_wbs_details_action() # Refresh details
        else:
            self.show_message("Error", "Project Startup module or update_wbs_element method not available.", True)

    def on_active_project_changed(self):
        is_project_active = bool(self.app.active_project_id)
        button_state = "normal" if is_project_active else "disabled"

        if self.execute_dna_button: self.execute_dna_button.config(state=button_state)
        if self.add_drawing_button: self.add_drawing_button.config(state=button_state)
        # View drawing button should be enabled if a drawing is selected, and project is active.
        # This might need more nuanced logic, e.g., bind to tree selection.
        if self.view_drawing_button: self.view_drawing_button.config(state="disabled") # Default to disabled

        if self.drawings_tree:
            if is_project_active:
                self.load_design_drawings()
            else:
                for item in self.drawings_tree.get_children():
                    self.drawings_tree.delete(item)

    def _update_view_drawing_button_state(self, event=None):
        """ Enable view button if a drawing is selected and project active """
        if self.app.active_project_id and self.drawings_tree.focus():
            self.view_drawing_button.config(state="normal")
        else:
            self.view_drawing_button.config(state="disabled")


    def import_data_action(self):
        file_path = filedialog.askopenfilename(
            title="Select Data File (e.g., Turnover CSV)",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            parent=self
        )
        if file_path:
            if not self.app.active_project_id:
                self.show_message("Error", "Please select an active project before importing data.", True)
                return

            # Assuming data_processing module has the method to process this specific file type
            data_processing_module = self.app.modules.get('data_processing')
            if data_processing_module and hasattr(data_processing_module, 'process_turnover_file'):
                success, message = data_processing_module.process_turnover_file(file_path, self.app.active_project_id)
                self.show_message("Import Result", message, not success)
            else:
                self.show_message("Error", "Data Processing module or 'process_turnover_file' method not available.", True)

    def add_drawing_action(self):
        if not self.app.active_project_id:
            self.show_message("Error", "No active project. Cannot add drawing.", True)
            return

        file_path = filedialog.askopenfilename(
            title="Select Design Drawing PDF",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
            parent=self
        )
        if not file_path: return

        description = simpledialog.askstring("Input", "Enter description for the drawing (optional):", parent=self)
        document_name = os.path.basename(file_path)

        user_details = self.app.user_manager.get_user_details_by_username(self.app.current_username)
        employee_db_id = user_details.get('employee_db_id') if user_details else None

        if not employee_db_id:
            self.show_message("Error", "Could not identify linked Employee ID for the current user. Please ensure your app user is linked to an employee record in User Management.", True)
            logger.warning(f"No linked EmployeeID for app user {self.app.current_username} for drawing upload.")
            return # Cannot proceed without a valid EmployeeID

        if self.module and hasattr(self.module, 'add_design_drawing'):
            document_id, message = self.module.add_design_drawing(
                self.app.active_project_id, document_name, file_path,
                employee_db_id, description # Pass the actual EmployeeID
            )
            self.show_message("Add Design Drawing", message, is_error=not bool(document_id))
            if document_id:
                self.load_design_drawings()
        else:
            self.show_message("Error", "Project Startup module or add_design_drawing method not available.", True)

    def view_drawing_action(self):
        selected_item_iid = self.drawings_tree.focus()
        if not selected_item_iid:
            self.show_message("Info", "Please select a drawing from the list to view.")
            return

        item_details = self.drawings_tree.item(selected_item_iid)
        # Values are ("Name", "FilePath", "UploadDate", "Description")
        # FilePath is at index 1
        file_path = item_details['values'][1] if item_details['values'] and len(item_details['values']) > 1 else None

        # The iid of the tree item IS the ProjectDocumentID (set during load_design_drawings)
        document_id_str = selected_item_iid
        try:
            document_id = int(document_id_str)
        except ValueError:
            self.show_message("Error", "Invalid document ID selected.", True)
            return

        if not file_path or file_path == 'N/A':
            self.show_message("Error", "File path is not available for the selected drawing.", True)
            return
        if not os.path.exists(file_path):
            self.show_message("Error", f"File not found: {file_path}", True)
            return

        try:
            pdf_window = tk.Toplevel(self.app)
            pdf_window.title(f"Viewing: {os.path.basename(file_path)}")
            pdf_window.geometry("1200x900") # Increased height for notes
            pdf_window.transient(self.app) # Make it a child of the main app
            # pdf_window.grab_set() # Make it modal - consider if this is best UX

            main_pane = ttk.PanedWindow(pdf_window, orient=tk.HORIZONTAL)
            main_pane.pack(fill='both', expand=True, padx=5, pady=5)

            pdf_frame = ttk.Frame(main_pane, width=800) # Initial width for PDF part
            main_pane.add(pdf_frame, weight=3) # PDF viewer takes more space initially

            pdf_viewer_instance = tkPDFViewer.ShowPdf()
            # Ensure add_comp returns the widget to pack
            pdf_display_widget = pdf_viewer_instance.add_comp(pdf_frame) # Removed width/height, let it fill
            pdf_display_widget.pack(fill='both', expand=True)

            # Critical: img_object_li must be initialized for display_pdf to work
            pdf_viewer_instance.img_object_li = []
            pdf_viewer_instance.display_pdf(file_path) # Load the PDF

            notes_panel_frame = ttk.LabelFrame(main_pane, text="Document Notes", width=400) # Initial width for notes
            main_pane.add(notes_panel_frame, weight=1)

            notes_display_text = tk.Text(notes_panel_frame, wrap='word', height=15, state='disabled') # Start disabled
            notes_display_text.pack(pady=5, padx=5, fill='both', expand=True)

            controls_frame = ttk.Frame(notes_panel_frame)
            controls_frame.pack(fill='x', padx=5, pady=5)

            ttk.Label(controls_frame, text="Page:").pack(side='left', padx=(0,2))
            page_count = self._get_pdf_page_count(file_path)
            self.page_number_spinbox = tk.Spinbox(controls_frame, from_=1, to=max(1, page_count), width=5) # Ensure 'to' is at least 1
            self.page_number_spinbox.pack(side='left', padx=(0,5))

            note_entry_text = tk.Text(notes_panel_frame, wrap='word', height=5)
            note_entry_text.pack(pady=5, padx=5, fill='x')

            add_note_button = ttk.Button(notes_panel_frame, text="Add Note to Current Page",
                                         command=lambda: self._add_document_note_action(
                                             document_id, self.page_number_spinbox,
                                             note_entry_text, notes_display_text
                                         ))
            add_note_button.pack(pady=5)

            self._load_document_notes_action(document_id, notes_display_text)

        except Exception as e:
            self.show_message("PDF Viewer Error", f"Could not open PDF: {e}", True)
            logger.error(f"Error opening PDF '{file_path}': {e}", exc_info=True)

    def load_design_drawings(self):
        for item in self.drawings_tree.get_children():
            self.drawings_tree.delete(item)

        if not self.app.active_project_id: return

        if self.module and hasattr(self.module, 'get_design_drawings_for_project'):
            drawings = self.module.get_design_drawings_for_project(self.app.active_project_id)
            if drawings:
                for drawing in drawings:
                    # Ensure ProjectDocumentID is used as iid for selection mapping
                    self.drawings_tree.insert("", tk.END, iid=drawing.get('ProjectDocumentID'), values=(
                        drawing.get('DocumentName', 'N/A'),
                        drawing.get('FilePath', 'N/A'),
                        drawing.get('UploadDate', 'N/A'),
                        drawing.get('Description', '')
                    ))
            # Bind selection event to update button state AFTER loading
            self.drawings_tree.bind("<<TreeviewSelect>>", self._update_view_drawing_button_state)
            self._update_view_drawing_button_state() # Update once after load

        else:
            self.show_message("Error", "Could not load drawings. Module or method missing.", is_error=True)

    def _get_pdf_page_count(self, file_path):
        try:
            # PyPDF2 is already imported by main.py, but good practice to ensure it's available
            # FortkPDFViewer uses PyMuPDF (fitz) internally for rendering, not PyPDF2 for page count.
            # tkPDFViewer.ShowPdf().get_page_count(file_path) might be a method if library provides it.
            # If not, we use PyPDF2 or PyMuPDF directly.
            # Let's assume PyPDF2 is available as it's a listed dependency.
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f) # Updated for PyPDF2 3.0.0+
                return len(reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count for {file_path} using PyPDF2: {e}")
            # Fallback or default
            return 1

    def _add_document_note_action(self, document_id, page_spinbox, entry_widget, display_widget):
        note_text = entry_widget.get("1.0", tk.END).strip()
        if not note_text:
            self.show_message("Empty Note", "Cannot add an empty note.", True)
            return

        try:
            page_number = int(page_spinbox.get())
        except ValueError:
            self.show_message("Invalid Page", "Page number is invalid.", True)
            return

        user_details = self.app.user_manager.get_user_details_by_username(self.app.current_username)
        employee_db_id = user_details.get('employee_db_id') if user_details else None

        if not employee_db_id:
            self.show_message("Error", "Could not identify linked Employee ID for the current user. Notes cannot be saved.", True)
            logger.warning(f"No linked EmployeeID for app user {self.app.current_username} for adding document note.")
            return

        # Call backend to add note
        if self.module and hasattr(self.module, 'add_document_note'):
            success, message = self.module.add_document_note(
                document_id, page_number, employee_db_id, note_text # Use employee_db_id
            )
            self.show_message("Add Note", message, is_error=not success)
            if success:
                entry_widget.delete("1.0", tk.END)
                self._load_document_notes_action(document_id, display_widget) # Refresh display
        else:
            self.show_message("Error", "Document notes backend functionality not available.", True)
            logger.error("ProjectStartup module or add_document_note method not available in frame.")

    def _load_document_notes_action(self, document_id, display_widget):
        display_widget.config(state='normal') # Enable for modification
        display_widget.delete("1.0", tk.END)

        if self.module and hasattr(self.module, 'get_document_notes'):
            notes = self.module.get_document_notes(document_id)
            if notes:
                for note in notes:
                    # Backend now returns dicts with 'FirstName', 'LastName' etc.
                    note_str = (f"Page {note['page_number']} | "
                                f"{note['FirstName']} {note['LastName']} ({note['created_at']}):\n"
                                f"{note['note_text']}\n{'-'*30}\n")
                    display_widget.insert(tk.END, note_str)
            else:
                display_widget.insert(tk.END, "No notes for this document yet or failed to load.")
        else:
            display_widget.insert(tk.END, "Error: Could not load notes. Backend functionality missing.")
            logger.error("ProjectStartup module or get_document_notes method not available in frame.")

        display_widget.config(state='disabled') # Make read-only again


    def execute_data_dna_action(self):
        if not self.app.active_project_id:
            self.show_message("Error", "No active project. Please create or select one first.", True)
            return

        project_id = self.app.active_project_id
        project_name = self.app.active_project_name
        logger.info(f"Starting 'Execute Data DNA' for project: {project_name} (ID: {project_id})")

        if not self.module or not all(hasattr(self.module, m) for m in ['generate_wbs_from_estimates', 'generate_project_budget', 'allocate_resources']):
            self.show_message("Error", "Project Startup module or one of its core methods is not available.", True)
            return

        # Confirmatory dialog
        if not messagebox.askyesno("Confirm Data DNA",
                                   f"This will link estimates, generate WBS, Budget, and Resources for '{project_name}'.\n"
                                   "This may overwrite existing planning data for this project. Continue?", parent=self):
            self.show_message("Cancelled", "Execute Data DNA cancelled by user.")
            return

        # Step 1: Generate WBS (which now includes linking estimates)
        # The backend method generate_wbs_from_estimates handles the core logic.
        wbs_success, wbs_msg = self.module.generate_wbs_from_estimates(project_id)
        self.show_message("WBS Generation", f"Project '{project_name}' - WBS Status: {wbs_msg}", is_error=not wbs_success)
        if not wbs_success:
            logger.error(f"Execute Data DNA for {project_name} (ID: {project_id}) failed or had issues at WBS generation step.")
            # Decide if we should stop or continue if WBS generation wasn't fully successful but didn't hard fail
            # For now, let's return if wbs_success is False (indicating a definitive failure)
            return

        # Step 2: Generate Budget (relies on WBS being present)
        budget_success, budget_msg = self.module.generate_project_budget(project_id)
        self.show_message("Budget Generation", f"Project '{project_name}' - Budget Status: {budget_msg}", is_error=not budget_success)
        if not budget_success:
            logger.error(f"Execute Data DNA for {project_name} (ID: {project_id}) failed or had issues at Budget generation step.")
            # Potentially return, or just log and continue to resource allocation

        # Step 3: Allocate Resources (relies on WBS/Estimates)
        resources_success, resources_msg = self.module.allocate_resources(project_id) # This method also needs to exist in backend
        self.show_message("Resource Allocation", f"Project '{project_name}' - Resource Status: {resources_msg}", is_error=not resources_success)
        if not resources_success:
            logger.error(f"Execute Data DNA for {project_name} (ID: {project_id}) failed or had issues at Resource allocation step.")

        # Final message
        if wbs_success and budget_success and resources_success:
            self.show_message("Execute Data DNA", f"'Execute Data DNA' process completed successfully for project '{project_name}'.")
        else:
            self.show_message("Execute Data DNA", f"'Execute Data DNA' process completed for project '{project_name}' with some issues. Please check logs and messages.", is_error=True)

        logger.info(f"'Execute Data DNA' process finished for project: {project_name} (ID: {project_id}).")

        if hasattr(self.app, 'load_project_list_data'):
            self.app.load_project_list_data() # Refresh project list in sidebar


    def _get_valid_project_id_from_entry(self, entry_widget=None):
        entry_widget = entry_widget or self.adhoc_project_id_entry
        proj_id_str = entry_widget.get().strip()
        if not proj_id_str:
            self.show_message("Input Error", "Please enter a Project ID for ad-hoc action.", True)
            return None
        try:
            return int(proj_id_str)
        except ValueError:
            self.show_message("Input Error", "Invalid Project ID. Must be a number.", True)
            return None

    def generate_wbs_action(self):
        proj_id = self._get_valid_project_id_from_entry()
        if proj_id is None: return
        if self.module and hasattr(self.module, 'generate_wbs_from_estimates'):
            if not messagebox.askyesno("Confirm Ad-hoc WBS", f"Generate/Re-generate WBS for Project ID {proj_id} using available estimates? This will clear existing WBS elements for this project.", parent=self):
                return
            success, msg = self.module.generate_wbs_from_estimates(proj_id) # This now returns (bool, str)
            self.show_message("Ad-hoc WBS Generation", msg, is_error=not success) # Pass is_error correctly
        else:
            self.show_message("Error", "Project Startup module or WBS method not available.", True)

    def generate_budget_action(self):
        proj_id = self._get_valid_project_id_from_entry()
        if proj_id is None: return
        if self.module and hasattr(self.module, 'generate_project_budget'):
            if not messagebox.askyesno("Confirm Ad-hoc Budget", f"Generate budget for Project ID {proj_id} from its WBS? This is an ad-hoc operation.", parent=self):
                return
            success, msg = self.module.generate_project_budget(proj_id)
            self.show_message("Ad-hoc Budget Generation", msg, not success)
        else:
            self.show_message("Error", "Project Startup module or budget method not available.", True)

    def allocate_resources_action(self):
        proj_id = self._get_valid_project_id_from_entry()
        if proj_id is None: return
        if self.module and hasattr(self.module, 'allocate_resources'):
            if not messagebox.askyesno("Confirm Ad-hoc Resources", f"Allocate resources for Project ID {proj_id} from its WBS/estimates? This is an ad-hoc operation.", parent=self):
                return
            success, msg = self.module.allocate_resources(proj_id)
            self.show_message("Ad-hoc Resource Allocation", msg, not success)
        else:
            self.show_message("Error", "Project Startup module or resource allocation method not available.", True)
