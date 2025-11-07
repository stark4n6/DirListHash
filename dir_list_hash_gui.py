import hashlib
import os
import csv
import datetime
import sqlite3
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import subprocess
import platform
from PIL import Image

# --- Core Logic Functions (Optimized) ---

app_name = "DirListHash"
app_version = "v1.0 GUI"

def hash_file(filepath, hash_type='sha1'):
    """Calculates the hash of a given file based on hash_type."""
    if hash_type.lower() == 'md5':
        hasher = hashlib.md5()
    elif hash_type.lower() == 'sha1':
        hasher = hashlib.sha1()
    else:
        return ''

    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        sys.stdout.write(f"\nError hashing file {filepath}: {e}\n")
        sys.stdout.flush()
        return ''

def get_file_details(filepath):
    """Retrieves file details including size and timestamps."""
    try:
        stat_info = os.stat(filepath)
        size = stat_info.st_size
        creation_time = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modification_time = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        access_time = datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")
        return size, creation_time, modification_time, access_time
    except Exception as e:
        sys.stdout.write(f"\nError getting details for {filepath}: {e}\n")
        sys.stdout.flush()
        return 0, '', '', ''

def collect_directory_data(directory_path, hash_choice, update_counter):
    """
    Collects file and directory details including hashes into a list of dictionaries.
    Optimized: Progress reporting is throttled to minimize GUI overhead.
    """
    all_items_data = []
    total_items = 0
    # First pass to get total count
    for _, dirs, files in os.walk(directory_path):
        total_items += len(files)
        total_items += len(dirs)

    current_item_count = 0
    # Throttling interval: Update once every 1000 items, or at least once if total items < 1000.
    progress_interval = max(1, total_items // 1000) 
    
    # Initial update
    update_counter(0, total_items, "Collecting data...") 

    for root, dirs, files in os.walk(directory_path):
        for name in sorted(files):
            # 1. Construct and Normalize File Path
            filepath = os.path.normpath(os.path.join(root, name))
            
            current_item_count += 1
            
            # Throttled Update
            if current_item_count % progress_interval == 0:
                 update_counter(current_item_count, total_items, "Collecting data...")

            file_sha1_hash = ''
            if hash_choice in ['sha1', 'both']:
                file_sha1_hash = hash_file(filepath, 'sha1')
            
            file_md5_hash = ''
            if hash_choice in ['md5', 'both']:
                file_md5_hash = hash_file(filepath, 'md5')

            size, ctime, mtime, atime = get_file_details(filepath)
            
            all_items_data.append({
                'Type': 'File',
                'FullPath': filepath, # Uses the normalized path
                'Name': name,
                'Size': size,
                'SHA1 Hash': file_sha1_hash,
                'MD5 Hash': file_md5_hash,
                'Creation Time': ctime,
                'Modification Time': mtime,
                'Access Time': atime
            })

        for name in sorted(dirs):
            # 2. Construct and Normalize Directory Path
            dirpath = os.path.normpath(os.path.join(root, name))
            
            current_item_count += 1
            
            # Throttled Update
            if current_item_count % progress_interval == 0:
                 update_counter(current_item_count, total_items, "Collecting data...")

            stat_info = os.stat(dirpath)
            size = stat_info.st_size
            ctime = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            atime = datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")
            
            all_items_data.append({
                'Type': 'Folder',
                'FullPath': dirpath, # Uses the normalized path
                'Name': name,
                'Size': size,
                'SHA1 Hash': '',
                'MD5 Hash': '',
                'Creation Time': ctime,
                'Modification Time': mtime,
                'Access Time': atime
            })

    # Final progress update
    update_counter(total_items, total_items, "Collection complete.")
    return all_items_data

def export_to_csv(data, output_csv_file, hash_choice, update_counter):
    """Exports the collected data to a CSV file. Optimized: Progress reporting is throttled."""
    csv_header = ['Type', 'Full Path', 'Name', 'Size (bytes)']
    if hash_choice in ['sha1', 'both']:
        csv_header.append('SHA1 Hash')
    if hash_choice in ['md5', 'both']:
        csv_header.append('MD5 Hash')
    csv_header.extend(['Creation Time', 'Modification Time', 'Access Time'])

    total_items = len(data)
    progress_interval = max(1, total_items // 1000)
    
    update_counter(0, total_items, "Exporting to CSV...")

    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(csv_header)
        for i, item in enumerate(data):
            # Throttled Update
            if (i + 1) % progress_interval == 0:
                update_counter(i + 1, total_items, "Exporting to CSV...")

            row = [
                item['Type'],
                item['FullPath'],
                item['Name'],
                item['Size']
            ]
            if hash_choice in ['sha1', 'both']:
                row.append(item['SHA1 Hash'])
            if hash_choice in ['md5', 'both']:
                row.append(item['MD5 Hash'])
            row.extend([
                item['Creation Time'],
                item['Modification Time'],
                item['Access Time']
            ])
            csv_writer.writerow(row)

    update_counter(total_items, total_items, "CSV Export complete.")


def export_to_sqlite(data, output_db_file, hash_choice, update_counter):
    """Exports the collected data to an SQLite database using bulk insertion. Optimized: Progress reporting is throttled."""
    conn = sqlite3.connect(output_db_file)
    cursor = conn.cursor()

    columns = [
        "Type TEXT",
        "FullPath TEXT PRIMARY KEY",
        "Name TEXT",
        "Size INTEGER"
    ]
    if hash_choice in ['sha1', 'both']:
        columns.append('SHA1Hash TEXT')
    if hash_choice in ['md5', 'both']:
        columns.append('MD5Hash TEXT')
    columns.extend(['CreationTime TEXT', 'ModificationTime TEXT', 'AccessTime TEXT'])

    create_table_sql = f"CREATE TABLE IF NOT EXISTS directory_contents ({', '.join(columns)})"
    cursor.execute(create_table_sql)

    column_names_for_insert = ['Type', 'FullPath', 'Name', 'Size']
    if hash_choice in ['sha1', 'both']:
        column_names_for_insert.append('SHA1Hash')
    if hash_choice in ['md5', 'both']:
        column_names_for_insert.append('MD5Hash')
    column_names_for_insert.extend(['CreationTime', 'ModificationTime', 'AccessTime'])
    
    placeholders = ', '.join(['?'] * len(column_names_for_insert))
    insert_sql = f"INSERT OR REPLACE INTO directory_contents ({', '.join(column_names_for_insert)}) VALUES ({placeholders})"

    entry_data_list = []
    total_items = len(data)
    progress_interval = max(1, total_items // 1000)
    
    update_counter(0, total_items, "Preparing data for SQLite...")

    for i, item in enumerate(data):
        # Throttled Update
        if (i + 1) % progress_interval == 0:
            update_counter(i + 1, total_items, "Preparing data for SQLite...")

        entry_data = [
            item['Type'],
            item['FullPath'],
            item['Name'],
            item['Size']
        ]
        if hash_choice in ['sha1', 'both']:
            entry_data.append(item['SHA1 Hash'])
        if hash_choice in ['md5', 'both']:
            entry_data.append(item['MD5 Hash'])
        entry_data.extend([
            item['Creation Time'],
            item['Modification Time'],
            item['Access Time']
        ])
        
        entry_data_list.append(tuple(entry_data))
    
    try:
        # Update before bulk operation
        update_counter(total_items, total_items, "Executing bulk insert into SQLite...")
        cursor.executemany(insert_sql, entry_data_list)
        conn.commit() 
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
        
    update_counter(total_items, total_items, "SQLite Export complete.")

def open_export_folder(folder_path):
    """Opens the specified folder path using the default file explorer based on the OS."""
    if not folder_path or not os.path.isdir(folder_path):
        messagebox.showerror("Open Folder Error", f"Cannot open folder: Path is invalid or does not exist.")
        return

    sys_platform = platform.system()
    try:
        if sys_platform == "Windows":
            # Windows uses os.startfile
            os.startfile(folder_path)
        elif sys_platform == "Darwin":
            # macOS uses 'open'
            subprocess.run(["open", folder_path], check=True)
        else:
            # Linux/Other POSIX uses 'xdg-open'
            subprocess.run(["xdg-open", folder_path], check=True)
    except Exception as e:
        messagebox.showerror("Open Folder Error", f"Failed to open export folder.\nError: {e}")


# --- CustomTkinter GUI Class ---

class DirListHashApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Basic Setup ---
        self.title(f"{app_name} {app_version}")
        self.geometry("800x820")
        # Lock the window size
        self.resizable(False, False) 
        self.grid_columnconfigure(0, weight=1)
        # The log frame is at row 4, so we want it to expand
        self.grid_rowconfigure(4, weight=1) 
        
        # Variables
        self.input_dir_path = ctk.StringVar(value="") 
        self.output_dir_path = ctk.StringVar(value="") 
        self.hash_choice = ctk.StringVar(value="none") 
        self.output_choice = ctk.StringVar(value="csv")
        self.final_output_dir = None 
        
        # --- Widgets ---
        self._create_log_frame()
        self._create_image_header()
        self._create_input_frame()
        self._create_options_frame()
        self._create_status_frame()
        
        # Set default appearance
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

    def _create_image_header(self):
        image_frame = ctk.CTkFrame(self, fg_color="transparent")
        image_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        image_frame.grid_columnconfigure(0, weight=1)

        try:
            image_path = os.path.join(os.path.dirname(__file__), "logo.png")
            app_image = ctk.CTkImage(Image.open(image_path), size=(150, 150)) 
            image_label = ctk.CTkLabel(image_frame, image=app_image, text="") 
            image_label.grid(row=0, column=0, pady=10) 
        except FileNotFoundError:
            self.log("WARNING: 'logo.png' not found. Skipping image display.")
        except Exception as e:
            self.log(f"ERROR loading image: {e}")

    def _create_input_frame(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        
        # Input Directory
        ctk.CTkLabel(input_frame, text="Input Directory:").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
        ctk.CTkEntry(input_frame, textvariable=self.input_dir_path).grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")
        ctk.CTkButton(input_frame, text="Browse", command=self.select_input_dir).grid(row=0, column=2, padx=0, pady=5)
        
        # Output Directory
        ctk.CTkLabel(input_frame, text="Output Directory:").grid(row=1, column=0, padx=(0, 10), pady=5, sticky="w")
        ctk.CTkEntry(input_frame, textvariable=self.output_dir_path).grid(row=1, column=1, padx=(0, 10), pady=5, sticky="ew")
        ctk.CTkButton(input_frame, text="Browse", command=self.select_output_dir).grid(row=1, column=2, padx=0, pady=5)

    def _create_options_frame(self):
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

        # Hash Options Frame
        hash_frame = ctk.CTkFrame(options_frame)
        hash_frame.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")
        ctk.CTkLabel(hash_frame, text="Hash Type", font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5))
        
        hash_options = ["none", "sha1", "md5", "both"]
        for i, option in enumerate(hash_options):
            ctk.CTkRadioButton(hash_frame, text=option.upper(), variable=self.hash_choice, value=option).pack(padx=20, pady=2, anchor="w")

        # Output Options Frame
        output_frame = ctk.CTkFrame(options_frame)
        output_frame.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        ctk.CTkLabel(output_frame, text="Output Format", font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5))
        
        output_options = ["csv", "sqlite", "both"]
        for i, option in enumerate(output_options):
            ctk.CTkRadioButton(output_frame, text=option.upper(), variable=self.output_choice, value=option).pack(padx=20, pady=2, anchor="w")

        # Start Button
        start_button = ctk.CTkButton(self, 
                                     text="▶️ Start Scan and Export", 
                                     command=self.start_processing_thread, 
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     height=40)
        start_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.start_button = start_button 
    
    def _create_log_frame(self):
        # Log Text Area - Placed at row 4
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        ctk.CTkLabel(log_frame, text="Activity Log:").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.log_text = ctk.CTkTextbox(log_frame, wrap="word")
        self.log_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def _create_status_frame(self):
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        status_frame.columnconfigure(0, weight=1)
        
        # Progress Counter Label
        self.status_label = ctk.CTkLabel(status_frame, text="Ready.")
        self.status_label.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")

    # --- Utility Methods ---
    
    def log(self, message):
        """Appends a timestamped message to the log box, with console fallback."""
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        normalized_message = os.path.normpath(message) if ('\\' in message and os.name == 'nt') or ('/' in message and os.name != 'nt') else message 
        full_message = f"{timestamp} {normalized_message}"
        
        # FIX: Check if log_text exists before trying to use it
        if hasattr(self, 'log_text'):
            self.log_text.insert("end", full_message + "\n")
            self.log_text.see("end")
        else:
            print(full_message) # Fallback to console if GUI isn't ready
    
    def update_counter(self, current, total, text):
        """Updates the GUI status label with the counter (current/total) and text."""
        self.after(0, self._set_gui_counter, current, total, text)
        
    def _set_gui_counter(self, current, total, text):
        """Internal method for thread-safe GUI updates."""
        self.status_label.configure(text=f"{text} ({current}/{total})")

    def _write_log_to_file(self):
        """Writes the entire content of the activity log to a text file."""
        if not self.final_output_dir:
            self.log("ERROR: Cannot write log file. Final output directory not set.")
            return
            
        try:
            log_content = self.log_text.get("1.0", "end-1c") 
            log_filename = "Activity_Log_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
            log_filepath = os.path.normpath(os.path.join(self.final_output_dir, log_filename))
            
            with open(log_filepath, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            self.log(f"Activity log successfully written to: {log_filepath}")
        except Exception as e:
            self.log(f"ERROR writing activity log to file: {e}")

    # --- Button Commands ---

    def select_input_dir(self):
        """Opens a dialog to select the directory to scan/hash."""
        folder_selected = filedialog.askdirectory(title="Select Directory to Scan")
        if folder_selected:
            normalized_path = folder_selected.replace('/', '\\') if platform.system() == "Windows" else folder_selected
            self.input_dir_path.set(normalized_path)

    def select_output_dir(self):
        """Opens a dialog to select the directory for report output."""
        folder_selected = filedialog.askdirectory(title="Select Output Directory for Reports")
        if folder_selected:
            normalized_path = folder_selected.replace('/', '\\') if platform.system() == "Windows" else folder_selected
            self.output_dir_path.set(normalized_path)

    # --- Processing Logic ---

    def start_processing_thread(self):
        """Starts the main processing logic in a separate thread."""
        if not self.input_dir_path.get() or not os.path.isdir(self.input_dir_path.get()):
            messagebox.showerror("Input Error", "Please select a valid input directory.")
            return

        self.final_output_dir = None
        self.start_button.configure(state="disabled", text="Processing...")
        self.status_label.configure(text="Starting process...")
        self.log_text.delete("1.0", "end")
        
        self.log(f"--- {app_name} {app_version} ---")
        self.log(f"Process started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Input Directory: {self.input_dir_path.get()}")
        self.log(f"Output Directory: {self.output_dir_path.get()}")
        self.log(f"Hash Type: {self.hash_choice.get()}")
        self.log(f"Output Format: {self.output_choice.get()}")
        
        self.worker_thread = threading.Thread(target=self._process_directory)
        self.worker_thread.start()

    def _process_directory(self):
        """Main processing function run in the worker thread."""
        try:
            input_dir = self.input_dir_path.get()
            output_dir_base = self.output_dir_path.get()
            hash_choice = self.hash_choice.get()
            output_choice = self.output_choice.get()
            
            current_datetime = datetime.datetime.now()
            timestamp_str = current_datetime.strftime("%Y%m%d_%H%M%S") 
            output_folder_name = f"DirListHash_Out_{timestamp_str}"
            
            if not output_dir_base:
                output_dir_base = os.getcwd()

            output_dir_final = os.path.normpath(os.path.join(output_dir_base, output_folder_name))
            
            if not os.path.exists(output_dir_final):
                os.makedirs(output_dir_final)
            
            self.final_output_dir = output_dir_final 
            self.log(f"Created output directory: {self.final_output_dir}")

            self.log("Starting data collection...")
            collected_data = collect_directory_data(input_dir, hash_choice, self.update_counter) 
            self.log(f"Collected data for {len(collected_data)} items.")
            
            clean_path = input_dir.replace('\\', '_').replace('/', '_').replace(':', '_').replace(' ', '_').strip('_')
            if not clean_path: clean_path = "root"

            base_filename = f"directory_{hash_choice if hash_choice != 'none' else 'listing'}_{clean_path}_{timestamp_str}"

            if output_choice in ['csv', 'both']:
                csv_filename = base_filename + ".csv"
                output_csv_file = os.path.normpath(os.path.join(self.final_output_dir, csv_filename)) 
                self.log(f"Exporting to CSV: {output_csv_file}")
                export_to_csv(collected_data, output_csv_file, hash_choice, self.update_counter)
                self.log("CSV Export finished.")

            if output_choice in ['sqlite', 'both']:
                db_filename = base_filename + ".db"
                output_db_file = os.path.normpath(os.path.join(self.final_output_dir, db_filename)) 
                self.log(f"Exporting to SQLite: {output_db_file}")
                export_to_sqlite(collected_data, output_db_file, hash_choice, self.update_counter)
                self.log("SQLite Export finished.")

            self.after(0, self._finalize_success)

        except Exception as e:
            self.after(0, self._finalize_error, e)
            
    def _finalize_success(self):
        """Runs in the main thread after successful processing."""
        end_time = datetime.datetime.now()
        self.log(f"Process finished successfully at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_log_to_file()
        self.status_label.configure(text="Process Complete!")
        self.start_button.configure(state="normal", text="▶️ Start Scan and Export")
        
        if self.final_output_dir and os.path.isdir(self.final_output_dir):
            response = messagebox.askyesno("Success!", "Directory scan finished!\n\nOpen export folder?", icon='info', default='yes')
            if response: open_export_folder(self.final_output_dir)
        else:
            messagebox.showinfo("Success", "Directory scan and export finished successfully!")

    def _finalize_error(self, e):
        """Runs in the main thread after an error."""
        self.log(f"ERROR: {e}")
        self._write_log_to_file()
        self.status_label.configure(text="ERROR! Check log.")
        self.start_button.configure(state="normal", text="▶️ Start Scan and Export")
        messagebox.showerror("Error", f"An error occurred: {e}")

# --- Execution ---

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = DirListHashApp()
    app.mainloop()