# gui/tree_views.py
import tkinter as tk
from tkinter import ttk

def create_treeview(parent, columns, headings, column_widths, scroll_x=True, scroll_y=True):
    """
    Creates and returns a treeview widget with the specified columns, headings, and widths.
    Optionally adds vertical and horizontal scrollbars.
    """
    tree = ttk.Treeview(parent, columns=columns, show='headings', selectmode='browse')
    for col, heading, width in zip(columns, headings, column_widths):
        tree.heading(col, text=heading, anchor='w')
        tree.column(col, width=width, anchor='w')
    
    if scroll_y:
        scrollbar_y = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side='right', fill='y')
    if scroll_x:
        scrollbar_x = ttk.Scrollbar(parent, orient='horizontal', command=tree.xview)
        tree.configure(xscrollcommand=scrollbar_x.set)
        scrollbar_x.pack(side='bottom', fill='x')
    
    tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
    return tree

def update_treeview_data(tree, rows, clear_first=True):
    """
    Helper function to update a treeview's rows.
    If clear_first is True, clears all existing entries.
    """
    if clear_first:
        for item in tree.get_children():
            tree.delete(item)
    for row in rows:
        tree.insert('', 'end', values=row)

def format_exclusions(exclusions):
    """
    Helper function to format exclusions (a list of dictionaries)
    into a readable string for display in a treeview cell.
    """
    if not exclusions:
        return "None"
    formatted = "; ".join(
        f"{excl['Leave Start'].strftime('%Y-%m-%d') if hasattr(excl['Leave Start'], 'strftime') else excl['Leave Start']} - "
        f"{excl['Leave End'].strftime('%Y-%m-%d') if hasattr(excl['Leave End'], 'strftime') else excl['Leave End']} "
        f"({excl['Reason']})"
        for excl in exclusions
    )
    return formatted
