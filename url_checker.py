import requests
import concurrent.futures
from bs4 import BeautifulSoup
import threading

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

def process_urls(urls, batch_size, result_table, status_label, start_button, stop_button, clear_button):
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
    stop_button.pack_forget()
    clear_button.pack(pady=10)
    status_label.config(text=f"Finished checking URLs. Total: {total_count}, Live: {live_count}, Dead: {dead_count}", fg="green")