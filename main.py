# import the necessary stuff
import pandas as pd
from datetime import datetime
import os
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk

# Constants and Helper Functions
LOG_FILE = 'log.csv'
STORAGE_LOG_FILE = 'StorageLog.csv'
columns = ['Equipment', 'Tech Name', 'Cabinet/Location', 'Shelf', 'Status', 'Timestamp']

def create_csv_if_not_exists(file_name, columns):
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_name, index=False)
        print(f"Created {file_name} with columns: {columns}")
    else:
        print(f"{file_name} already exists.")
        # For debugging, print the first few lines of the existing file
        print(pd.read_csv(file_name).head())

def determine_status(equipment, cabinet):
    log_file = STORAGE_LOG_FILE if equipment.startswith('STOR.') else LOG_FILE
    if not os.path.exists(log_file):
        return 'checked in'

    df = pd.read_csv(log_file)
    count = df[df['Equipment'] == equipment].shape[0]

    if cabinet == 'Quality Calibration':
        return 'checked out'

    return 'checked out' if count % 2 == 1 else 'checked in'

def delete_last_entry_for_equipment(equipment_name, log_file):
    try:
        df = pd.read_csv(log_file)
        equipment_entries = df[df['Equipment'] == equipment_name]
        if not equipment_entries.empty:
            df = df.drop(equipment_entries.index[-1])
            df.to_csv(log_file, index=False)
            return True
        else:
            return False
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return False

# Main Application Class
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.entries = {}
        self.entry_list = []

        large_font = font.Font(family='Helvetica', size=16)
        container = tk.Frame(self, bd=1, relief=tk.SOLID)
        container.pack(expand=True, padx=5, pady=5)

        # Create entry fields for each column
        for col in columns[:-2]:
            self.create_entry_field(container, col, large_font)

        # Message label within the container
        self.msg_label = tk.Label(container, text="", font=large_font)
        self.msg_label.pack(side=tk.BOTTOM, padx=5, pady=5)

        # Load and display logo outside the container
        self.load_display_logo()

    def create_entry_field(self, parent, column_name, font):
        row = tk.Frame(parent)
        label = tk.Label(row, text=f"Please Scan the {column_name}: ", font=font)
        entry = tk.Entry(row, font=font, width=30)
        entry.bind('<Return>', self.handle_return_key)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        label.pack(side=tk.LEFT)
        entry.pack(side=tk.RIGHT)
        self.entries[column_name] = entry
        self.entry_list.append(entry)

    def load_display_logo(self):
        base_height = 50
        img = Image.open("lancer_logo.png")
        h_percent = (base_height / float(img.size[1]))
        w_size = int((float(img.size[0]) * float(h_percent)))
        img = img.resize((w_size, base_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label_photo = tk.Label(self, image=photo)
        label_photo.photo = photo
        label_photo.pack(side=tk.BOTTOM, anchor=tk.W)

    def handle_return_key(self, event):
        current_index = self.entry_list.index(event.widget)
        user_input = event.widget.get()

        if user_input.lower() == 'void':
            self.void_entry()
            return

        if current_index == 1 and user_input.lower() == 'admin correction':
            self.handle_admin_correction()
            return

        if current_index + 1 < len(self.entry_list):
            self.entry_list[current_index + 1].focus_set()
        else:
            self.save_entry()

    def save_entry(self):
        missing_field = next((col for col in columns[:-2] if not self.entries[col].get().strip()), None)
        if missing_field:
            self.display_message(f"Entry not submitted. Missing '{missing_field}' field.", 'red')
            self.clear_entries()
            return

        current_entry = self.collect_entry_data()
        log_file = STORAGE_LOG_FILE if current_entry['Equipment'].startswith("STOR.") else LOG_FILE
        self.append_entry_to_file(current_entry, log_file)
        self.display_message("Submission successful!", 'green')
        self.after(4000, self.clear_entries)

    def collect_entry_data(self):
        return {col: self.entries[col].get() for col in columns[:-2]}

    def append_entry_to_file(self, entry, file_name):
        entry['Status'] = determine_status(entry['Equipment'], entry.get('Cabinet/Location', ''))
        entry['Timestamp'] = datetime.now().strftime('%m-%d-%Y %I:%M %p')

        with open(file_name, 'a', newline='') as f:
            pd.DataFrame([entry]).to_csv(f, header=False, index=False)

    def display_message(self, message, color):
        self.msg_label.config(text=message, fg=color, font='Helvetica 16 bold')
        self.after(4000, lambda: self.msg_label.config(text=''))

    def clear_entries(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.entries['Equipment'].focus_set()

    def void_entry(self):
        self.clear_entries()
        self.display_message("Submission voided. Please restart.", 'red')

    def handle_admin_correction(self):
        equipment_name = self.entries['Equipment'].get().strip()
        if equipment_name:
            log_file = STORAGE_LOG_FILE if equipment_name.startswith("STOR.") else LOG_FILE
            deleted = delete_last_entry_for_equipment(equipment_name, log_file)
            message = "Admin Correction: Last entry for '{}' deleted. Please restart.".format(equipment_name) if deleted else "No entries found for '{}'.".format(equipment_name)
            self.display_message(message, 'orange' if deleted else 'red')
            self.clear_entries()
        else:
            self.display_message("Please enter the Equipment name for Admin Correction.", 'red')

    def equipment_exists(self, equipment_name, log_file):
        try:
            df = pd.read_csv(log_file)
            return not df[df['Equipment'] == equipment_name].empty
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return False

# Main Function
def main():
    create_csv_if_not_exists(LOG_FILE, columns)
    create_csv_if_not_exists(STORAGE_LOG_FILE, columns)
    app = App()
    app.mainloop()

if __name__ == '__main__':
    main()
