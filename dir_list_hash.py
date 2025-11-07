import hashlib
import os
import csv
import datetime
import sqlite3
import sys # Import sys for `sys.stdout.write` and `sys.stdout.flush`

app_name = "DirListHash"
app_version = "v1.0"

def hash_file(filepath, hash_type='sha1'):
    """Calculates the hash of a given file based on hash_type."""
    if hash_type.lower() == 'md5':
        hasher = hashlib.md5()
    elif hash_type.lower() == 'sha1':
        hasher = hashlib.sha1()
    else:
        # If hash_type is 'none' or invalid, return an empty string for the hash
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

def collect_directory_data(directory_path, hash_choice):
    """
    Collects file and directory details including hashes into a list of dictionaries,
    with optimized progress reporting (counter only, no path printing).
    """
    all_items_data = []
    total_items = 0
    # First pass to get total count
    for _, dirs, files in os.walk(directory_path):
        total_items += len(files)
        total_items += len(dirs)

    current_item_count = 0
    # Optimization: Only update progress every N items
    progress_interval = max(1, total_items // 1000) 
    
    for root, dirs, files in os.walk(directory_path):
        for name in sorted(files):
            filepath = os.path.join(root, name)
            current_item_count += 1
            
            # Print progress and current item (Reduced frequency)
            if current_item_count % progress_interval == 0:
                sys.stdout.write(f"\rCollecting data: {current_item_count}/{total_items}")
                sys.stdout.flush()
                
            # Removed the path printing for speed optimization
            # sys.stdout.write(f"\nProcessing: {filepath}\n") 
            # sys.stdout.flush()

            file_sha1_hash = ''
            if hash_choice in ['sha1', 'both']:
                file_sha1_hash = hash_file(filepath, 'sha1')
            
            file_md5_hash = ''
            if hash_choice in ['md5', 'both']:
                file_md5_hash = hash_file(filepath, 'md5')

            size, ctime, mtime, atime = get_file_details(filepath)
            
            all_items_data.append({
                'Type': 'File',
                'FullPath': filepath,
                'Name': name,
                'Size': size,
                'SHA1 Hash': file_sha1_hash,
                'MD5 Hash': file_md5_hash,
                'Creation Time': ctime,
                'Modification Time': mtime,
                'Access Time': atime
            })

        for name in sorted(dirs):
            dirpath = os.path.join(root, name)
            current_item_count += 1
            
            # Print progress and current item (Reduced frequency)
            if current_item_count % progress_interval == 0:
                sys.stdout.write(f"\rCollecting data: {current_item_count}/{total_items}")
                sys.stdout.flush()
                
            # Removed the path printing for speed optimization
            # sys.stdout.write(f"\nProcessing: {dirpath}\n")
            # sys.stdout.flush()

            stat_info = os.stat(dirpath)
            size = stat_info.st_size # For directories, size is usually 0 or varies by OS
            ctime = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            atime = datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")
            
            all_items_data.append({
                'Type': 'Folder',
                'FullPath': dirpath,
                'Name': name,
                'Size': size,
                'SHA1 Hash': '', # Directories don't have a direct file hash
                'MD5 Hash': '',  # Directories don't have a direct file hash
                'Creation Time': ctime,
                'Modification Time': mtime,
                'Access Time': atime
            })
            
    # Final update to show 100% completion
    sys.stdout.write(f"\rCollecting data: {total_items}/{total_items}\n") 
    sys.stdout.flush()
    return all_items_data

def export_to_csv(data, output_csv_file, hash_choice):
    """Exports the collected data to a CSV file with optimized progress reporting."""
    csv_header = ['Type', 'Full Path', 'Name', 'Size (bytes)']
    if hash_choice in ['sha1', 'both']:
        csv_header.append('SHA1 Hash')
    if hash_choice in ['md5', 'both']:
        csv_header.append('MD5 Hash')
    csv_header.extend(['Creation Time', 'Modification Time', 'Access Time'])

    total_items = len(data)
    progress_interval = max(1, total_items // 1000) # Update at least once, or every 1/1000th of the items
    
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(csv_header)
        for i, item in enumerate(data):
            
            # --- OPTIMIZATION: Update progress less frequently ---
            if (i + 1) % progress_interval == 0:
                sys.stdout.write(f"\rExporting to CSV: {i+1}/{total_items}")
                sys.stdout.flush()

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
            
    # Final update to show 100% completion
    sys.stdout.write(f"\rExporting to CSV: {total_items}/{total_items}\n") 
    sys.stdout.flush()


def export_to_sqlite(data, output_db_file, hash_choice):
    """Exports the collected data to an SQLite database using bulk insertion."""
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
    # conn.commit() # Removed: No need to commit yet

    column_names_for_insert = ['Type', 'FullPath', 'Name', 'Size']
    if hash_choice in ['sha1', 'both']:
        column_names_for_insert.append('SHA1Hash')
    if hash_choice in ['md5', 'both']:
        column_names_for_insert.append('MD5Hash')
    column_names_for_insert.extend(['CreationTime', 'ModificationTime', 'AccessTime'])
    
    placeholders = ', '.join(['?'] * len(column_names_for_insert))
    insert_sql = f"INSERT OR REPLACE INTO directory_contents ({', '.join(column_names_for_insert)}) VALUES ({placeholders})"

    # --- OPTIMIZATION: Prepare data for executemany ---
    
    entry_data_list = []
    total_items = len(data)
    
    for i, item in enumerate(data):
        # Print progress (optional but good for user feedback)
        sys.stdout.write(f"\rPreparing data for SQLite: {i+1}/{total_items}")
        sys.stdout.flush()

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
        
        # entry_data must be a tuple for executemany
        entry_data_list.append(tuple(entry_data))

    sys.stdout.write(f"\rPreparing data for SQLite: {total_items}/{total_items}\n") # Final update
    sys.stdout.flush()
    
    # --- OPTIMIZATION: Use executemany for bulk insertion ---
    sys.stdout.write(f"Executing bulk insert into SQLite...\n")
    sys.stdout.flush()
    
    try:
        # Use executemany to insert all rows in one go
        cursor.executemany(insert_sql, entry_data_list)
        # Commit the transaction only once after all insertions
        conn.commit() 
    except Exception as e:
        sys.stdout.write(f"\nError during bulk insert: {e}\n")
        conn.rollback() # Rollback on error
    finally:
        conn.close()
        
    sys.stdout.write(f"\rExporting to SQLite: {total_items}/{total_items}\n") # Final update
    sys.stdout.flush()

if __name__ == "__main__":
    print(f"{app_name} {app_version}")
    print(f"https://github.com/stark4n6/DirListHash")
    while True:
        directory_to_hash = input("Enter the path of the directory you want to list/hash (e.g., C:\\MyFiles or /home/user/documents): ")
        if os.path.isdir(directory_to_hash):
            break
        else:
            print("Error: The specified path is not a valid directory or does not exist. Please try again.")

    while True:
        hash_choice = input("Choose hash type (sha1, md5, both, or none): ").lower()
        if hash_choice in ['sha1', 'md5', 'both', 'none']:
            break
        else:
            print("Error: Invalid choice. Please choose 'sha1', 'md5', 'both', or 'none'.")

    while True:
        output_choice = input("Choose output format (csv, sqlite, both): ").lower()
        if output_choice in ['csv', 'sqlite', 'both']:
            break
        else:
            print("Error: Invalid choice. Please choose 'csv', 'sqlite', or 'both'.")

    # Get the script's run location
    script_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        output_directory_input = input(f"Enter the desired output directory for the reports (default: {script_dir}): ")
        if not output_directory_input: # User pressed Enter, use default
            output_directory = script_dir
            print(f"Output directory set to default: {output_directory}")
            break
        elif not os.path.exists(output_directory_input):
            try:
                os.makedirs(output_directory_input)
                print(f"Created output directory: {output_directory_input}")
                output_directory = output_directory_input
                break
            except OSError as e:
                print(f"Error creating directory {output_directory_input}: {e}. Please try again.")
        elif not os.path.isdir(output_directory_input):
            print("Error: The specified path is not a directory. Please try again.")
        else:
            output_directory = output_directory_input
            break

    start_time = datetime.datetime.now()
    current_datetime = datetime.datetime.now()
    timestamp_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S") 

    clean_path_for_filename = directory_to_hash.replace(os.sep, '_').replace(':', '_').replace(' ', '_')
    clean_path_for_filename = clean_path_for_filename.strip('_') 

    print(f"\nProcess started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Collect all data once
    collected_data = collect_directory_data(directory_to_hash, hash_choice)

    if output_choice in ['csv', 'both']:
        csv_filename = f"directory_listing_{clean_path_for_filename}_{timestamp_str}.csv"
        if hash_choice != 'none':
            csv_filename = f"directory_hash_report_{clean_path_for_filename}_{timestamp_str}.csv"
        output_csv_file = os.path.join(output_directory, csv_filename)
        export_to_csv(collected_data, output_csv_file, hash_choice)
        print(f"Details exported to CSV: {output_csv_file}")

    if output_choice in ['sqlite', 'both']:
        db_filename = f"directory_listing_{clean_path_for_filename}_{timestamp_str}.db"
        if hash_choice != 'none':
            db_filename = f"directory_hash_report_{clean_path_for_filename}_{timestamp_str}.db"
        output_db_file = os.path.join(output_directory, db_filename)
        export_to_sqlite(collected_data, output_db_file, hash_choice)
        print(f"Details exported to SQLite: {output_db_file}")

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print(f"\nProcess finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration}")
