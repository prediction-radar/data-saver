import os
import requests
from urllib.parse import urljoin
import gzip
import shutil
import xarray as xr
import numpy as np
import glob

# Endpoint to download GRIB files from
base_url = "https://mrms.ncep.noaa.gov/data/2D/MergedReflectivityComposite/"
grib_folder = "grib_files/"  # Folder to save files

# Ensure the local directory exists
os.makedirs(grib_folder, exist_ok=True)

def get_grib_files():
    """Fetches the list of grib files available at the base URL."""
    response = requests.get(base_url)
    if response.status_code == 200:
        lines = response.text.splitlines()
        files = [line.split('"')[1] for line in lines if ".grib2.gz" in line]
        return files
    else:
        print(f"Failed to fetch file list. Status code: {response.status_code}")
        return []

def get_remote_file_size(url):
    """Returns the size of the remote file in bytes."""
    response = requests.head(url)
    if response.status_code == 200:
        return int(response.headers.get('Content-Length', 0))
    return 0

def download_file(file_name):
    """Downloads the specified GRIB file and renames it based on the timestamp."""
    url = urljoin(base_url, file_name)
    timestamp = file_name.split('_')[-1].replace('.grib2.gz', '')

    # Renaming to just the date and time
    new_file_name = f"{timestamp}.grib2.gz"
    output_path = os.path.join(grib_folder, new_file_name)

    remote_file_size = get_remote_file_size(url)

    if os.path.exists(output_path):
        local_file_size = os.path.getsize(output_path)

        if local_file_size == remote_file_size:
            print(f"{new_file_name} already exists and matches the server size. Skipping download.")
            return None

    print(f"Downloading {file_name}...")
    response = requests.get(url, stream=True)

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return timestamp

def download_latest_file():
    """Downloads the most recent GRIB file available."""
    files = get_grib_files()
    if files:
        latest_file = sorted(files)[-1]
        file_name = download_file(latest_file)
        return file_name
    else:
        print("No files found.")
        return None


def decompress_file(compressed_path, decompressed_path):
    with gzip.open(compressed_path, 'rb') as f_in:
        with open(decompressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Decompressed {compressed_path} to {decompressed_path}")

def delete_idx_files(directory_path):
    pattern = os.path.join(directory_path, '*.grib2.*.idx')
    idx_files = glob.glob(pattern)
    for file_path in idx_files:
        os.remove(file_path)
        print(f"Deleted: {file_path}")

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print(f"File {file_path} does not exists, so it could not be deleted.")


if __name__ == "__main__":
    downloaded_file_name = download_latest_file()
    if downloaded_file_name != None:
        compressed_file_location = grib_folder + downloaded_file_name + ".grib2.gz"
        decompressed_file_location = grib_folder + downloaded_file_name + ".grib2"
        decompress_file(compressed_file_location, decompressed_file_location)
        delete_idx_files(grib_folder)
        delete_file(compressed_file_location)
