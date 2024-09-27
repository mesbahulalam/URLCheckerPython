import requests
import multiprocessing
import concurrent.futures
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
import webbrowser
from bs4 import BeautifulSoup
import threading
import csv

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
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        future_to_item = {}
        for url in urls:
            item = result_table.insert("", "end", values=("Fetching...", url, "Processing", "Fetching..."), tags=("Processing",))
            future = executor.submit(check_url, url)
            future_to_item[future] = item
        
        for future in concurrent.futures.as_completed(future_to_item):
            favicon, url, status, title = future.result()
            item = future_to_item[future]
            color = "green" if status == "Success" else "red"
            result_table.item(item, values=(favicon, url, status, title), tags=(status,))
            result_table.tag_configure(status, foreground=color)
            result_table.update_idletasks()

def start_checking():
    status_label.config(text="Checking URLs...", fg="blue")
    root.update_idletasks()
    
    input_text = text_area.get("1.0", tk.END).strip()
    urls = [line for line in input_text.split('\n') if line and not line.startswith('#')]
    batch_size = multiprocessing.cpu_count()
    
    result_table.delete(*result_table.get_children())
    
    # Run the URL checking process in a separate thread
    threading.Thread(target=process_urls, args=(urls, batch_size)).start()

def on_url_click(event):
    item = result_table.selection()[0]
    url = result_table.item(item, "values")[1]
    webbrowser.open(url)

def export_to_csv():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if file_path:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Favicon", "URL", "Status", "Title"])
            for row_id in result_table.get_children():
                row = result_table.item(row_id)['values']
                writer.writerow(row)
        status_label.config(text="Results exported successfully.", fg="green")

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
file_menu.add_command(label="Open File", command=open_file)
file_menu.add_command(label="Export to CSV", command=export_to_csv)
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
result_table = ttk.Treeview(result_frame, columns=("Favicon", "URL", "Status", "Title"), show="headings")
result_table.heading("Favicon", text="Favicon")
result_table.heading("URL", text="URL")
result_table.heading("Status", text="Status")
result_table.heading("Title", text="Title")
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

root.mainloop()