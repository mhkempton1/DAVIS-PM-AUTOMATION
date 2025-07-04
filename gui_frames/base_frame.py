import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

class BaseModuleFrame(tk.Frame):
    def __init__(self, parent, app, module_instance=None):
        super().__init__(parent)
        self.app = app
        self.module_instance = module_instance
        self.configure(bg=self.app.colors['bg_secondary']) # Apply consistent styling

    def on_active_project_changed(self):
        """
        A placeholder method intended to be overridden by subclasses.

        This method is called by the main application when the globally active
        project changes. Subclasses should implement this method if they need
        to refresh their displayed data or state based on the new active project.
        """
        logger.debug(
            f"{self.__class__.__name__}: Active project changed signal received. "
            "Subclass can override this method to implement specific refresh logic."
        )
        # Default implementation does nothing; subclasses should provide specifics.
        pass

    def show_message(self, title, message, is_error=False):
        """
        Displays a message box to the user.
        :param title: The title of the message box.
        :param message: The message to display.
        :param is_error: If True, displays an error message box; otherwise, an info message box.
        """
        if is_error:
            messagebox.showerror(title, message, parent=self)
        else:
            messagebox.showinfo(title, message, parent=self)

    def display_dataframe(self, df, title="Data View"):
        """
        Displays a pandas DataFrame in a new Toplevel window with a Treeview widget.
        :param df: The pandas DataFrame to display.
        :param title: The title of the new window.
        """
        if df.empty:
            self.show_message(title, "No data to display.")
            return

        top = tk.Toplevel(self.app)
        top.title(title)
        top.geometry("800x600")

        frame = ttk.Frame(top, padding="10")
        frame.pack(expand=True, fill='both')

        tree = ttk.Treeview(frame)
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"

        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='w', width=120)

        for index, row in df.iterrows():
            tree.insert("", "end", values=list(row))

        # Add scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        tree.pack(side='left', fill='both', expand=True)

        top.transient(self.app)
        top.grab_set()