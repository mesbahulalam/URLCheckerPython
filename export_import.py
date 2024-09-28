from tkinter import filedialog
import csv
from bs4 import BeautifulSoup  # Make sure to install BeautifulSoup4 with `pip install beautifulsoup4`

def export_to_csv(selected_columns, filter_value, result_table, status_label):
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

def export_to_hosts(filter_value, result_table, status_label):
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, mode='w', encoding='utf-8') as file:
            for row_id in result_table.get_children():
                row = result_table.item(row_id)['values']
                if filter_value == "All" or row[2] == filter_value:
                    file.write(f"127.0.0.1 {row[1]}\n")
        status_label.config(text="Hosts file exported successfully.", fg="green")

def show_export_bookmarks_dialog():
    export_window = tk.Toplevel(root)
    export_window.title("Export Bookmarks File")

    embed_favicons_var = tk.StringVar(value="No")
    tk.Label(export_window, text="Embed Favicons:").pack(anchor='w')
    embed_favicons_combobox = ttk.Combobox(export_window, textvariable=embed_favicons_var, values=["Yes", "No"], state="readonly")
    embed_favicons_combobox.pack(anchor='w')

    def export():
        export_to_bookmarks(embed_favicons_var.get() == "Yes")
        export_window.destroy()

    tk.Button(export_window, text="Export", command=export).pack(pady=10)

def export_to_bookmarks(embed_favicons):
    file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html"), ("All files", "*.*")])
    if file_path:
        with open(file_path, mode='w', encoding='utf-8') as file:
            file.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n")
            file.write("<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">\n")
            file.write("<TITLE>Bookmarks</TITLE>\n")
            file.write("<H1>Bookmarks</H1>\n")
            file.write("<DL><p>\n")
            for row_id in result_table.get_children():
                row = result_table.item(row_id)['values']
                if row[2] == "Success":
                    favicon = row[0]
                    if embed_favicons and favicon:
                        try:
                            response = requests.get(favicon)
                            if response.status_code == 200:
                                favicon_data = base64.b64encode(response.content).decode('utf-8')
                                favicon = f"data:image/x-icon;base64,{favicon_data}"
                        except requests.RequestException:
                            pass
                    file.write(f'<DT><A HREF="{row[1]}" ICON="{favicon}">{row[3]}</A>\n')
            file.write("</DL><p>\n")
        status_label.config(text="Bookmarks file exported successfully.", fg="green")

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