import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'common_lib')))

import  functions_for_call # type: ignore

def create_batch_file(brand_country):
    # Get the base path from find_path function
    base_path = functions_for_call.base_path

    # Construct dynamic paths
    venv_scripts_path = os.path.join(base_path, "myenv", "Scripts")
    project_path = os.path.join(base_path, brand_country,brand_country)

    # Batch file content
    batch_content = f"""@echo off
cd /d {venv_scripts_path}
call activate.bat
cd {project_path}
scrapy crawl {brand_country}_scrape
"""

    # drive = os.path.splitdrive(base_path)[0]

    # batch_content = f"""
    # {drive}
    # cd {project_path}
    # scrapy crawl {brand_country}_scrape
    # """.strip()
    
    batch_file_paths = [
        os.path.join(base_path, "bat_files", f"{brand_country}.bat"),
    ]

    for batch_file_path in batch_file_paths:
        # Ensure the bat_files directory exists
        os.makedirs(os.path.dirname(batch_file_path), exist_ok=True)

        # Write the batch file
        with open(batch_file_path, 'w') as batch_file:
            batch_file.write(batch_content)
    print(f"Batch file created at {batch_file_path}")

def main():
    
    # Get the base path of the project
    base_path = functions_for_call.base_path

    # get the path of the bat_files directory
    bat_folder = os.path.join(base_path, "bat_files")

    # delete all the files in the bat_files directory
    for path,folders,file in os.walk(bat_folder):
        for file in file:
            os.remove(os.path.join(path,file))

    # Get all the directory name in base dir
    ommited_dirs = ['common_lib', 'myenv', 'bat_files','test_selenium']
    dirs = [d for d in os.listdir(base_path) if d not in ommited_dirs]
    
    # Create the batch file for each directory
    for brand_country in dirs:
        # Create the batch file
        create_batch_file(brand_country)

    print(f'Total {len(dirs)} batch files created')

if __name__ == "__main__":
    main()
