import tkinter as tk
from tkinter import filedialog, messagebox, Frame
from tkinter import ttk
import threading
from DOI import extract_doi_from_pdf
from Network import process_uploaded_pdf

class InputApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PDF Upload App")
        self.master.geometry("400x200")

        self.pdf_path = None
        self.create_widgets()

    def create_widgets(self):
        frame = Frame(self.master)
        frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        title_label = tk.Label(frame, text="Upload Your PDF", font=("Arial", 16))
        title_label.pack(pady=10)

        upload_button = tk.Button(frame, text="Upload PDF", command=self.open_input_dialog, width=25)
        upload_button.pack(pady=5)

        self.progress = ttk.Progressbar(frame, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(pady=15)

    def open_input_dialog(self):
        self.pdf_path = filedialog.askopenfilename(title="Select a PDF file", filetypes=[("PDF files", "*.pdf")])
        if self.pdf_path:
            messagebox.showinfo("File Selected", "PDF file selected successfully.")
            self.upload_pdf_file()
        else:
            messagebox.showwarning("No File Selected", "Please select a PDF file.")

    def upload_pdf_file(self):
        if self.pdf_path:
            threading.Thread(target=self.process_upload, args=(self.pdf_path,)).start()

    def process_upload(self, pdf_path):
        self.progress.start()
        try:
            process_uploaded_pdf(pdf_path)
            messagebox.showinfo("Process Complete", "PDF processed and network plotted.")
        except Exception as e:
            messagebox.showerror("Process Failed", f"Failed to process PDF:\n{e}")
        finally:
            self.progress.stop()
            
if __name__ == "__main__":
    root = tk.Tk()
    app = InputApp(root)
    root.mainloop()