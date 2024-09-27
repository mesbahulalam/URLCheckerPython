import requests
import multiprocessing
import concurrent.futures
import tkinter as tk
from tkinter import scrolledtext

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return url, 'Success' if response.status_code == 200 else 'Failure'
    except requests.RequestException:
        return url, 'Failure'

def process_urls(urls, batch_size):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        future_to_url = {executor.submit(check_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url, status = future.result()
            results.append((url, status))
            # Update the result area immediately
            color = "green" if status == "Success" else "red"
            result_area.insert(tk.INSERT, f"{url} - {status}\n", status)
            result_area.tag_config(status, foreground=color)
            result_area.update_idletasks()
    return results

def start_checking():
    status_label.config(text="Checking URLs...", fg="blue")
    root.update_idletasks()
    
    input_text = text_area.get("1.0", tk.END).strip()
    urls = [line for line in input_text.split('\n') if line and not line.startswith('#')]
    batch_size = multiprocessing.cpu_count()
    results = process_urls(urls, batch_size)
    
    result_area.config(state=tk.NORMAL)
    result_area.delete("1.0", tk.END)
    
    for url, status in results:
        color = "green" if status == "Success" else "red"
        result_area.insert(tk.INSERT, f"{url} - {status}\n", status)
        result_area.tag_config(status, foreground=color)
    
    result_area.config(state=tk.DISABLED)
    status_label.config(text="Finished checking URLs.", fg="green")

# GUI setup
root = tk.Tk()
root.title("URL Checker")

frame = tk.Frame(root)
frame.pack(pady=10)

text_area = scrolledtext.ScrolledText(frame, width=50, height=10)
text_area.pack()

result_area = scrolledtext.ScrolledText(frame, width=50, height=10)
result_area.pack()

status_label = tk.Label(root, text="")
status_label.pack()

start_button = tk.Button(root, text="Start Checking", command=start_checking)
start_button.pack(pady=10)

root.mainloop()