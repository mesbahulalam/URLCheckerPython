import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import asyncio
import aiohttp

async def check_url(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return True
            else:
                return False
    except aiohttp.ClientError as e:
        print(f"Error: {e}")
        return False

async def check_urls():
    urls = url_text.get("1.0", tk.END).strip().split('\n')
    
    # Clear previous results
    for item in result_table.get_children():
        result_table.delete(item)
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(check_url(session, url))
        
        results = await asyncio.gather(*tasks)
        
        for url, result in zip(urls, results):
            status = "Success" if result else "Failed"
            tag = 'success' if status == "Success" else 'failed'
            result_table.insert("", "end", values=(url, status), tags=(tag,))
    
    # Stop the progress bar
    progress_bar.stop()
    
    # Enable the button again
    check_button.config(state=tk.NORMAL)

def on_check_button_click():
    # Disable the button to prevent multiple clicks
    check_button.config(state=tk.DISABLED)
    
    # Start the progress bar
    progress_bar.start()
    
    # Run the URL checking in an asynchronous manner
    asyncio.run(check_urls())

# Create the main window
root = tk.Tk()
root.title("URL Checker")

# Create and place the URL entry
url_label = tk.Label(root, text="Enter URLs (one per line):")
url_label.pack(pady=5)
url_text = tk.Text(root, height=10, width=50)
url_text.pack(pady=5)

# Create and place the Check button
check_button = tk.Button(root, text="Check", command=on_check_button_click)
check_button.pack(pady=20)

# Create and place the result table
result_table = ttk.Treeview(root, columns=("URL", "Status"), show="headings")
result_table.heading("URL", text="URL")
result_table.heading("Status", text="Status")
result_table.pack(pady=20)

# Configure tags for coloring
result_table.tag_configure('success', foreground='green')
result_table.tag_configure('failed', foreground='red')

# Create and place the progress bar
progress_bar = ttk.Progressbar(root, mode='indeterminate')
progress_bar.pack(pady=20)

# Run the application
root.mainloop()