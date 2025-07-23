import hashlib
import os
import csv
import datetime
from tqdm import tqdm

def hash_file(filepath, hash_type='sha1'):
    """Calculates the hash of a given file based on hash_type."""
    if hash_type.lower() == 'md5':
        hasher = hashlib.md5()
    elif hash_type.lower() == 'sha1':
        hasher = hashlib.sha1()
    else:
        raise ValueError("Invalid hash type specified. Choose 'md5' or 'sha1'.")

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def get_file_details(filepath):
    """Retrieves file details including size and timestamps."""
    stat_info = os.stat(filepath)
    size = stat_info.st_size
    creation_time = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
    modification_time = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    access_time = datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")
    return size, creation_time, modification_time, access_time

def hash_directory_with_csv(directory_path, output_csv_file, hash_choice, start_time):
    """
    Calculates the hash(es) of files and directories and generates a CSV output.
    The CSV includes full path, name, size, hash(es), and timestamps,
    with a progress bar. It does NOT calculate an overall directory hash.
    """
    total_items = 0
    for _, dirs, files in os.walk(directory_path):
        total_items += len(files)
        total_items += len(dirs)

    csv_header = ['Type', 'Full Path', 'Name', 'Size (bytes)']
    if hash_choice in ['sha1', 'both']:
        csv_header.append('SHA1 Hash')
    if hash_choice in ['md5', 'both']:
        csv_header.append('MD5 Hash')
    csv_header.extend(['Creation Time', 'Modification Time', 'Access Time'])

    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(csv_header)

        with tqdm(total=total_items, desc="Processing directory", unit="item") as pbar:
            for root, dirs, files in os.walk(directory_path):
                for name in sorted(files):
                    filepath = os.path.join(root, name)
                    
                    file_sha1_hash = ''
                    if hash_choice in ['sha1', 'both']:
                        file_sha1_hash = hash_file(filepath, 'sha1')
                    
                    file_md5_hash = ''
                    if hash_choice in ['md5', 'both']:
                        file_md5_hash = hash_file(filepath, 'md5')

                    size, ctime, mtime, atime = get_file_details(filepath)
                    
                    entry_data = ['File', filepath, name, size]
                    if hash_choice in ['sha1', 'both']:
                        entry_data.append(file_sha1_hash)
                    if hash_choice in ['md5', 'both']:
                        entry_data.append(file_md5_hash)
                    entry_data.extend([ctime, mtime, atime])
                    
                    csv_writer.writerow(entry_data)
                    pbar.update(1)

                for name in sorted(dirs):
                    dirpath = os.path.join(root, name)
                    stat_info = os.stat(dirpath)
                    size = stat_info.st_size
                    ctime = datetime.datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                    mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    atime = datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    entry_data = ['Folder', dirpath, name, size]
                    if hash_choice in ['sha1', 'both']:
                        entry_data.append('') 
                    if hash_choice in ['md5', 'both']:
                        entry_data.append('') 
                    entry_data.extend([ctime, mtime, atime])
                    
                    csv_writer.writerow(entry_data)
                    pbar.update(1)

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    duration_str = str(duration)

    return duration_str

if __name__ == "__main__":
    while True:
        directory_to_hash = input("Enter the path of the directory you want to hash (e.g., C:\\MyFiles or /home/user/documents): ")
        if os.path.isdir(directory_to_hash):
            break
        else:
            print("Error: The specified path is not a valid directory or does not exist. Please try again.")

    while True:
        hash_choice = input("Choose hash type (sha1, md5, or both): ").lower()
        if hash_choice in ['sha1', 'md5', 'both']:
            break
        else:
            print("Error: Invalid hash choice. Please choose 'sha1', 'md5', or 'both'.")

    start_time = datetime.datetime.now()

    current_datetime = datetime.datetime.now()
    timestamp_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S") 

    clean_path_for_filename = directory_to_hash.replace(os.sep, '_').replace(':', '_').replace(' ', '_')
    clean_path_for_filename = clean_path_for_filename.strip('_') 

    output_csv_file = f"dir_list_hash_report_{clean_path_for_filename}_{timestamp_str}.csv"

    # Print the start timestamp *before* calling the function with tqdm
    print(f"\nProcess started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    duration = hash_directory_with_csv(directory_to_hash, output_csv_file, hash_choice, start_time)

    print(f"Process finished at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration}")

    print(f"Details exported to: {output_csv_file}")
