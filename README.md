<p align="center"><img width="300" height="300" alt="Image" src="https://github.com/user-attachments/assets/eb5f7371-65e4-4cf8-b643-d3bf59b335bc" /></p>

# DirListHash
A simple directory listing and hashing script. It iterates through the input path and gets the following information:
- Type (File or Folder)
- Full Path
- Name
- Size (bytes)
- SHA1 Hash (optional)
- MD5 Hash (optional)
- Creation Time
- Modification Time
- Access Time

## DISCLAIMER
The script has been tested on Windows but may not have support on other OS's, feedback is greatly appreciated!

USE AT YOUR OWN RISK!

## Usage

### Requirements
`pip install tqdm`

TQDM only used for progress bar purposes

### Options
1. Input path
2. Hashing choice (sha1, md5, both or none)
3. Output type (csv, sqlite, both)
4. Output path
