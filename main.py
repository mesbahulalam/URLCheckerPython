import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, simpledialog
import webbrowser
import threading
import multiprocessing
from url_checker import check_url, process_urls, stop_event
from export_import import export_to_csv, export_to_hosts, import_hosts_file, import_bookmarks_file
import csv

def start_checking():
    status_label.config(text="Checking URLs...", fg="blue")
    root.update_idletasks()
    
    input_text = text_area.get("1.0", tk.END).strip()
    urls = [line for line in input_text.split('\n') if line and not line.startswith('#')]
    batch_size = multiprocessing.cpu_count()
    
    result_table.delete(*result_table.get_children())
    
    # Run the URL checking process in a separate thread
    stop_event.clear()
    start_button.pack_forget()
    # stop_button.pack(pady=10)
    clear_button.pack_forget()
    threading.Thread(target=process_urls, args=(urls, batch_size, result_table, status_label, start_button, stop_button, clear_button)).start()

# def stop_checking():
#     stop_event.set()
#     status_label.config(text="Stopping...", fg="red")
#     stop_button.pack_forget()
#     start_button.pack(pady=10)

def clear_results():
    result_table.delete(*result_table.get_children())
    clear_button.pack_forget()

def on_url_click(event):
    item = result_table.selection()[0]
    url = result_table.item(item, "values")[1]
    webbrowser.open(url)

def show_export_window():
    export_window = tk.Toplevel(root)
    export_window.title("Select Columns to Export")

    columns = ["Favicon", "URL", "Status", "Title"]
    column_vars = {col: tk.BooleanVar(value=True) for col in columns}

    for col in columns:
        tk.Checkbutton(export_window, text=col, variable=column_vars[col]).pack(anchor='w')

    filter_var = tk.StringVar(value="All")
    tk.Label(export_window, text="Filter:").pack(anchor='w')
    filter_combobox = ttk.Combobox(export_window, textvariable=filter_var, values=["All", "Success", "Failure"], state="readonly")
    filter_combobox.pack(anchor='w')

    def export():
        selected_columns = [col for col in columns if column_vars[col].get()]
        export_to_csv(selected_columns, filter_var.get(), result_table, status_label)
        export_window.destroy()

    tk.Button(export_window, text="Export", command=export).pack(pady=10)

def show_export_hosts_dialog():
    export_window = tk.Toplevel(root)
    export_window.title("Export Hosts File")

    filter_var = tk.StringVar(value="All")
    tk.Label(export_window, text="Include:").pack(anchor='w')
    filter_combobox = ttk.Combobox(export_window, textvariable=filter_var, values=["All", "Success", "Failure"], state="readonly")
    filter_combobox.pack(anchor='w')

    def export():
        export_to_hosts(filter_var.get(), result_table, status_label)
        export_window.destroy()

    tk.Button(export_window, text="Export", command=export).pack(pady=10)

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, content)

def exit_app():
    root.quit()

def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)

# GUI setup
root = tk.Tk()
root.title("URL Checker")

# Create a menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Create a File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Import Text File", command=open_file)
file_menu.add_command(label="Import Hosts File", command=import_hosts_file)
file_menu.add_command(label="Import Bookmarks", command=import_bookmarks_file)
file_menu.add_command(label="Export to CSV", command=show_export_window)
file_menu.add_command(label="Export to Hosts File", command=show_export_hosts_dialog)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=exit_app)

frame = tk.Frame(root)
frame.pack(pady=10)

text_area = scrolledtext.ScrolledText(frame, width=50, height=10)
text_area.pack()

# Create a context menu for the text area
context_menu = tk.Menu(text_area, tearoff=0)
context_menu.add_command(label="Cut", command=lambda: text_area.event_generate("<<Cut>>"))
context_menu.add_command(label="Copy", command=lambda: text_area.event_generate("<<Copy>>"))
context_menu.add_command(label="Paste", command=lambda: text_area.event_generate("<<Paste>>"))
context_menu.add_command(label="Select All", command=lambda: text_area.event_generate("<<SelectAll>>"))

text_area.bind("<Button-3>", show_context_menu)

# Create a frame for the result table and scrollbar
result_frame = tk.Frame(frame)
result_frame.pack()

# Create the result table
columns = ["Favicon", "URL", "Status", "Title"]
result_table = ttk.Treeview(result_frame, columns=columns, show="headings")
for col in columns:
    result_table.heading(col, text=col)
result_table.pack(side=tk.LEFT)

# Create a vertical scrollbar for the result table
scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=result_table.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Configure the result table to use the scrollbar
result_table.configure(yscrollcommand=scrollbar.set)

result_table.bind("<Double-1>", on_url_click)

status_label = tk.Label(root, text="")
status_label.pack()

start_button = tk.Button(root, text="Start Checking", command=start_checking)
start_button.pack(pady=10)

# stop_button = tk.Button(root, text="Stop Checking", command=stop_checking)
# stop_button.pack_forget()

clear_button = tk.Button(root, text="Clear Results", command=clear_results)
clear_button.pack_forget()

root.mainloop()