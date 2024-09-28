import requests
import multiprocessing
import concurrent.futures
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
from tkinter import simpledialog
import webbrowser
from bs4 import BeautifulSoup
import threading
import csv

stop_event = threading.Event()

def check_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else 'No Title'
            favicon = None
            icon_link = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
            if icon_link and icon_link.get('href'):
                favicon = icon_link['href']
                if not favicon.startswith(('http://', 'https://')):
                    favicon = url + favicon
            return favicon, url, 'Success', title
        else:
            return None, url, 'Failure', 'N/A'
    except requests.RequestException:
        return None, url, 'Failure', 'N/A'

def process_urls(urls, batch_size):
    total_count = len(urls)
    live_count = 0
    dead_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        future_to_item = {}
        for url in urls:
            if stop_event.is_set():
                break
            item = result_table.insert("", "end", values=("Fetching...", url, "Processing", "Fetching..."), tags=("Processing",))
            future = executor.submit(check_url, url)
            future_to_item[future] = item
        
        for future in concurrent.futures.as_completed(future_to_item):
            if stop_event.is_set():
                break
            favicon, url, status, title = future.result()
            item = future_to_item[future]
            color = "green" if status == "Success" else "red"
            result_table.item(item, values=(favicon, url, status, title), tags=(status,))
            result_table.tag_configure(status, foreground=color)
            result_table.update_idletasks()

            if status == "Success":
                live_count += 1
            else:
                dead_count += 1
    
    stop_event.clear()
    start_button.pack(pady=10)
    # stop_button.pack_forget()
    clear_button.pack(pady=10)
    status_label.config(text=f"Finished checking URLs. Total: {total_count}, Live: {live_count}, Dead: {dead_count}", fg="green")

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
    threading.Thread(target=process_urls, args=(urls, batch_size)).start()

def stop_checking():
    stop_event.set()
    status_label.config(text="Stopping...", fg="red")
    stop_button.pack_forget()
    start_button.pack(pady=10)
    status_label.config(text="Stopped.", fg="red")

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
        export_to_csv(selected_columns, filter_var.get())
        export_window.destroy()

    tk.Button(export_window, text="Export", command=export).pack(pady=10)

def export_to_csv(selected_columns, filter_value):
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if file_path:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(selected_columns)
            for row_id in result_table.get_children():
                row = result_table.item(row_id)['values']
                if filter_value == "All" or row[2] == filter_value:
                    writer.writerow([row[columns.index(col)] for col in selected_columns])
        status_label.config(text="Results exported successfully.", fg="green")

def show_export_hosts_dialog():
    export_window = tk.Toplevel(root)
    export_window.title("Export Hosts File")

    filter_var = tk.StringVar(value="All")
    tk.Label(export_window, text="Include:").pack(anchor='w')
    filter_combobox = ttk.Combobox(export_window, textvariable=filter_var, values=["All", "Success", "Failure"], state="readonly")
    filter_combobox.pack(anchor='w')

    def export():
        export_to_hosts(filter_var.get())
        export_window.destroy()

    tk.Button(export_window, text="Export", command=export).pack(pady=10)

def export_to_hosts(filter_value):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, mode='w', encoding='utf-8') as file:
            for row_id in result_table.get_children():
                row = result_table.item(row_id)['values']
                if filter_value == "All" or row[2] == filter_value:
                    file.write(f"127.0.0.1 {row[1]}\n")
        status_label.config(text="Hosts file exported successfully.", fg="green")

def import_hosts_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            urls = [line.split()[1] for line in lines if line.startswith("127.0.0.1")]
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, "\n".join(urls))

def import_bookmarks_file():
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            urls = [a['href'] for a in soup.find_all('a', href=True)]
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, "\n".join(urls))

def export_to_bookmarks(filter_value):
    file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
            file.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
            file.write('<TITLE>Bookmarks</TITLE>\n')
            file.write('<H1>Bookmarks</H1>\n')
            file.write('<DL><p>\n')
            for row_id in result_table.get_children():
                row = result_table.item(row_id)['values']
                if filter_value == "All" or row[2] == filter_value:
                    file.write(f'<DT><A HREF="{row[1]}">{row[3]}</A>\n')
            file.write('</DL><p>\n')
        status_label.config(text="Bookmarks exported successfully.", fg="green")

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


def show_export_filter_dialog():
    filter_window = tk.Toplevel(root)
    filter_window.title("Export Filter")

    filter_var = tk.StringVar(value="All")
    tk.Label(filter_window, text="Include:").pack(anchor='w')
    filter_combobox = ttk.Combobox(filter_window, textvariable=filter_var, values=["All", "Success", "Failure"], state="readonly")
    filter_combobox.pack(anchor='w')

    def apply_filter():
        selected_filter = filter_var.get()
        filter_window.destroy()
        show_export_progress(selected_filter)

    tk.Button(filter_window, text="Apply", command=apply_filter).pack(pady=10)

def show_export_progress(filter_value):
    progress_window = tk.Toplevel(root)
    progress_window.title("Exporting Bookmarks")
    progress_label = tk.Label(progress_window, text="Exporting bookmarks, please wait...")
    progress_label.pack(pady=20)
    progress_bar = ttk.Progressbar(progress_window, mode='determinate', maximum=100)
    progress_bar.pack(pady=10, padx=20)

    def update_progress(value):
        progress_bar['value'] = value
        progress_window.update_idletasks()

    def close_progress_window():
        progress_window.destroy()

    def export_with_progress():
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
                file.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
                file.write('<TITLE>Bookmarks</TITLE>\n')
                file.write('<H1>Bookmarks</H1>\n')
                file.write('<DL><p>\n')
                
                rows = result_table.get_children()
                total_steps = len(rows)
                
                for step, row_id in enumerate(rows):
                    if stop_event.is_set():
                        break
                    row = result_table.item(row_id)['values']
                    if filter_value == "All" or row[2] == filter_value:
                        file.write(f'<DT><A HREF="{row[1]}">{row[3]}</A>\n')
                    update_progress((step + 1) / total_steps * 100)
                
                file.write('</DL><p>\n')
            status_label.config(text="Bookmarks exported successfully.", fg="green")
        close_progress_window()

    threading.Thread(target=export_with_progress).start()

# GUI setup
root = tk.Tk()
root.title("URL Checker")

# Create a menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Create a File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Open File", command=open_file)
file_menu.add_command(label="Import Hosts File", command=import_hosts_file)
file_menu.add_command(label="Import Bookmarks File", command=import_bookmarks_file)
file_menu.add_command(label="Export to CSV", command=show_export_window)
file_menu.add_command(label="Export to Hosts File", command=show_export_hosts_dialog)
file_menu.add_command(label="Export to Bookmarks", command=show_export_filter_dialog)
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