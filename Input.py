# Input.py
import tkinter as tk
from tkinter import filedialog, messagebox, Frame
from tkinter import ttk
import threading
import os

# Import logic for PDFs
from Local_Reference import build_reference_network, plot_networks

# Import logic for Excel
try:
    from Cross_Reference import build_cross_reference_network, plot_cross_reference_network
except ImportError:
    build_cross_reference_network = None
    plot_cross_reference_network = None

class InputApp:
    def __init__(self, master):
        self.master = master
        self.master.title("File Upload App")
        self.master.geometry("400x200")

        self.file_path = None
        self.create_widgets()

    def create_widgets(self):
        frame = Frame(self.master)
        frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        title_label = tk.Label(frame, text="Upload PDF or Excel File", font=("Arial", 16))
        title_label.pack(pady=10)

        upload_button = tk.Button(frame, text="Upload File", command=self.open_input_dialog, width=25)
        upload_button.pack(pady=5)

        self.progress = ttk.Progressbar(frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(pady=15)
        
        self.status_label = tk.Label(frame, text="", font=("Arial", 10))
        self.status_label.pack()

    def open_input_dialog(self):
        filetypes = [
            ("Supported Files", "*.pdf *.xlsx *.xls"),
            ("PDF files", "*.pdf"),
            ("Excel files", "*.xlsx *.xls")
        ]
        
        self.file_path = filedialog.askopenfilename(title="Select a File", filetypes=filetypes)
        
        if self.file_path:
            filename = os.path.basename(self.file_path)
            messagebox.showinfo("File Selected", f"Selected: {filename}")
            self.upload_file()
        else:
            messagebox.showwarning("No File Selected", "Please select a file.")

    def upload_file(self):
        if self.file_path:
            self.progress.start()
            self.status_label.config(text="Processing...")
            threading.Thread(target=self.process_file_thread, args=(self.file_path,)).start()

    def process_file_thread(self, file_path):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pdf':
                # --- Process PDF ---
                graph = build_reference_network(file_path)
                self.master.after(0, lambda: self.on_pdf_complete(graph))
                
            elif ext in ['.xlsx', '.xls']:
                # --- Process Excel ---
                if build_cross_reference_network:
                    graph = build_cross_reference_network(file_path)
                    self.master.after(0, lambda: self.on_excel_complete(graph))
                else:
                    raise ImportError("Cross_Reference.py not found or incorrectly named.")
            else:
                raise ValueError("Unsupported file format.")
                
        except Exception as e:
            error_msg = str(e)
            self.master.after(0, lambda m=error_msg: self.on_error(m))

    def on_pdf_complete(self, graph):
        self.progress.stop()
        self.status_label.config(text="")
        if graph:
            messagebox.showinfo("Process Complete", "Network built successfully. Launching plots...")
            plot_networks(graph)
        else:
            messagebox.showwarning("Result", "Could not build a network (no references found).")

    def on_excel_complete(self, graph):
        self.progress.stop()
        self.status_label.config(text="")
        if graph:
            messagebox.showinfo("Process Complete", "Excel Cross-Reference Network built successfully.")
            plot_cross_reference_network(graph)
        else:
            messagebox.showwarning("Result", "No valid cross-references found in the Excel file.")

    def on_error(self, error_msg):
        self.progress.stop()
        self.status_label.config(text="Error")
        messagebox.showerror("Process Failed", f"An error occurred:\n{error_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InputApp(root)
    root.mainloop()