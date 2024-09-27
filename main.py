import requests
import multiprocessing
import concurrent.futures
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import webbrowser

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return url, 'Success' if response.status_code == 200 else 'Failure'
    except requests.RequestException:
        return url, 'Failure'

def process_urls(urls, batch_size):
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url, status = future.result()
            color = "green" if status == "Success" else "red"
            result_table.insert("", "end", values=(url, status), tags=(status,))
            result_table.tag_configure(status, foreground=color)
            result_table.update_idletasks()

def start_checking():
    status_label.config(text="Checking URLs...", fg="blue")
    root.update_idletasks()
    
    input_text = text_area.get("1.0", tk.END).strip()
    urls = [line for line in input_text.split('\n') if line and not line.startswith('#')]
    batch_size = multiprocessing.cpu_count()
    
    result_table.delete(*result_table.get_children())
    process_urls(urls, batch_size)
    
    status_label.config(text="Finished checking URLs.", fg="green")

def on_url_click(event):
    item = result_table.selection()[0]
    url = result_table.item(item, "values")[0]
    webbrowser.open(url)

# GUI setup
root = tk.Tk()
root.title("URL Checker")

frame = tk.Frame(root)
frame.pack(pady=10)

text_area = scrolledtext.ScrolledText(frame, width=50, height=10)
text_area.pack()

result_table = ttk.Treeview(frame, columns=("URL", "Status"), show="headings")
result_table.heading("URL", text="URL")
result_table.heading("Status", text="Status")
result_table.pack()

result_table.bind("<Double-1>", on_url_click)

status_label = tk.Label(root, text="")
status_label.pack()

start_button = tk.Button(root, text="Start Checking", command=start_checking)
start_button.pack(pady=10)

root.mainloop()