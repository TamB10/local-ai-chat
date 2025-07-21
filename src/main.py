import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import json
import threading
import os
import PyPDF2
import time
from datetime import datetime

# === SETTINGS ===
CHATS_DIR = "saved_chats"
if not os.path.exists(CHATS_DIR):
    os.makedirs(CHATS_DIR)

ICON_PATH = "icon.png"
MODEL_LIST = ["mistral", "llama3", "zephyr", "phi3", "starling"]
APP_NAME = "Local AI Chat"

# === SPLASH SCREEN ===
def show_splash():
    splash = tk.Tk()
    splash.title("Loading...")
    splash.geometry("400x300")
    splash.overrideredirect(True)
    splash.eval('tk::PlaceWindow . center')

    try:
        splash.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
    except tk.TclError:
        pass

    ttk.Label(splash, text=APP_NAME, font=("Arial", 20, "bold"), padding=20).pack()
    ttk.Label(splash, text="Loading your local AI assistant...", justify="center").pack()
    splash.update()
    time.sleep(2)
    splash.destroy()

# === MAIN APP ===
class OllamaChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1000x600")
        self.dark_mode = False
        self.bg_color = "#2e2e2e"
        self.fg_color = "#ffffff"
        self.entry_bg = "#444444"
        self.entry_fg = "#00ff99"
        self.file_content = ""

        # Left frame for chat list
        left_frame = ttk.Frame(self.root, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)

        # Chat list label
        ttk.Label(left_frame, text="Saved Chats", font=("Arial", 10, "bold")).pack(pady=5)

        # Chat listbox
        self.chat_listbox = tk.Listbox(left_frame, bg=self.bg_color, fg=self.fg_color, selectbackground="#555", borderwidth=0, highlightthickness=0)
        self.chat_listbox.pack(fill=tk.BOTH, expand=True, padx=5)
        self.chat_listbox.bind("<<ListboxSelect>>", self.load_selected_chat)

        # Refresh button
        ttk.Button(left_frame, text="Refresh", command=self.refresh_chat_list).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(left_frame, text="New Chat", command=self.clear_chat).pack(fill=tk.X, padx=5, pady=5)

        # Right frame for chat
        right_frame = ttk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Top controls
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(pady=10, fill=tk.X)

        ttk.Label(control_frame, text="Model:").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar(value=MODEL_LIST[0])
        self.model_menu = ttk.Combobox(control_frame, textvariable=self.model_var, values=MODEL_LIST, state="readonly", width=18)
        self.model_menu.pack(side=tk.LEFT, padx=5)

        self.theme_button = ttk.Button(control_frame, text="Dark Mode", command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT, padx=5)

        # Load file
        file_frame = ttk.Frame(right_frame)
        file_frame.pack(pady=5, fill=tk.X)

        self.file_label = ttk.Label(file_frame, text="No file loaded", foreground="gray")
        self.file_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.load_button = ttk.Button(file_frame, text="Load File", command=self.load_file)
        self.load_button.pack(side=tk.RIGHT, padx=5)

        # Prompt entry
        self.entry = ttk.Entry(right_frame, font=("Arial", 14))
        self.entry.pack(pady=10, fill=tk.X)
        self.entry.bind("<Return>", lambda e: self.start_send_prompt())

        self.send_button = ttk.Button(right_frame, text="Ask AI", command=self.start_send_prompt)
        self.send_button.pack(pady=5)

        # Response box
        response_frame = ttk.Frame(right_frame)
        response_frame.pack(pady=10, padx=5, expand=True, fill=tk.BOTH)

        self.response_text = tk.Text(response_frame, wrap=tk.WORD, font=("Arial", 12), state="disabled")
        scroll = ttk.Scrollbar(response_frame, orient="vertical", command=self.response_text.yview)
        self.response_text.configure(yscrollcommand=scroll.set)

        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.response_text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Set icon
        try:
            self.root.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
        except tk.TclError:
            pass

        # Load chat list
        self.refresh_chat_list()

    def refresh_chat_list(self):
        self.chat_listbox.delete(0, tk.END)
        files = sorted([f for f in os.listdir(CHATS_DIR) if f.endswith(".txt")], reverse=True)
        for f in files:
            self.chat_listbox.insert(tk.END, f.replace(".txt", ""))

    def load_selected_chat(self, event):
        selection = self.chat_listbox.curselection()
        if not selection:
            return
        filename = self.chat_listbox.get(selection[0]) + ".txt"
        path = os.path.join(CHATS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.response_text.config(state="normal")
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(tk.END, content)
            self.response_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load chat: {str(e)}")

    def clear_chat(self):
        self.response_text.config(state="normal")
        self.response_text.delete(1.0, tk.END)
        self.response_text.config(state="disabled")

    def save_current_chat(self):
        if len(self.response_text.get(1.0, tk.END).strip()) == 0:
            return
        timestamp = datetime.now().strftime("chat_%Y-%m-%d_%H-%M.txt")
        path = os.path.join(CHATS_DIR, timestamp)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.response_text.get(1.0, tk.END))
        self.refresh_chat_list()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        theme = self.dark_mode
        self.theme_button.config(text="Light Mode" if theme else "Dark Mode")
        bg = self.bg_color if theme else "white"
        fg = self.fg_color if theme else "black"
        entry_bg = self.entry_bg if theme else "white"
        entry_fg = self.entry_fg if theme else "black"

        self.root.configure(bg=bg)
        self.response_text.configure(bg=bg, fg=fg, insertbackground=fg)
        self.entry.configure(style="Custom.TEntry")
        style = ttk.Style()
        style.configure("Custom.TEntry", fieldbackground=entry_bg, foreground=entry_fg)
        style.configure("TButton", foreground=entry_fg, background=entry_bg)
        style.map("TButton", background=[("active", "#555555")])

    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text and PDF files", "*.txt *.pdf")]
        )
        if not file_path:
            return
        try:
            if file_path.endswith(".pdf"):
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                    self.file_content = text
            elif file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    self.file_content = f.read()
            self.file_label.config(text=os.path.basename(file_path), foreground=self.entry_fg if self.dark_mode else "black")
        except Exception as e:
            self.file_label.config(text="Error loading file", foreground="red")

    def start_send_prompt(self):
        prompt = self.entry.get()
        if prompt.strip() == "":
            return
        self.entry.delete(0, tk.END)

        full_prompt = prompt
        if hasattr(self, "file_content") and self.file_content:
            full_prompt = "Document content:\n\n" + self.file_content[:3000] + "\n\nQuestion: " + prompt

        self.response_text.config(state="normal")
        self.response_text.insert(tk.END, f"\nYou: {prompt}\n\nAI: ")
        self.response_text.config(state="disabled")
        threading.Thread(target=self.send_prompt, args=(full_prompt,)).start()

    def send_prompt(self, prompt):
        model = self.model_var.get()
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": True},
                stream=True
            )

            collected = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            token = data["response"]
                            collected += token
                            self.root.after(0, self.update_response_box, collected)
                    except:
                        continue
            self.root.after(0, self.save_current_chat)
        except Exception as e:
            self.root.after(0, self.update_response_box, f"\nError: {str(e)}")

    def update_response_box(self, content):
        self.response_text.config(state="normal")
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, content)
        self.response_text.config(state="disabled")
        self.response_text.see(tk.END)

# === START ===
if __name__ == "__main__":
    show_splash()
    root = tk.Tk()
    app = OllamaChatApp(root)
    root.mainloop()
