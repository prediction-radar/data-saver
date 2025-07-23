import os
import requests
from urllib.parse import urljoin
import gzip
import shutil
import xarray as xr
import numpy as np
import glob
from datetime import datetime, timedelta, timezone
import re

# Endpoint to download GRIB files from
base_url = "https://mrms.ncep.noaa.gov/data/2D/MergedReflectivityAtLowestAltitude/"
grib_folder = os.path.expanduser('~/Documents/radar/data-saver/storage/grib_files/')
npy_directory = os.path.expanduser('~/Documents/radar/data-saver/storage/v2_npy_files/')

# Ensure the download directory exists
os.makedirs(grib_folder, exist_ok=True)
os.makedirs(npy_directory, exist_ok=True)

def get_grib_files():
    """Fetches the list of grib files available at the base URL."""
    response = requests.get(base_url)
    if response.status_code == 200:
        lines = response.text.splitlines()
        # Only include .grib2.gz files with timestamps (ignore .latest)
        files = [
            line.split('"')[1]
            for line in lines
            if re.search(r'MRMS_MergedReflectivityAtLowestAltitude_.*_(\d{8}-\d{6})\.grib2\.gz', line)
        ]
        return files
    else:
        print(f"Failed to fetch file list. Status code: {response.status_code}")
        return []

def get_timestamp_from_filename(file_name):
    # Extract timestamp from filename
    match = re.search(r'_(\d{8}-\d{6})\.grib2\.gz', file_name)
    if match:
        return match.group(1)
    return None

def is_within_last_24_hours(timestamp_str):
    # timestamp_str format: YYYYMMDD-HHMMSS
    try:
        file_time = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return now - timedelta(hours=24) <= file_time <= now
    except Exception as e:
        print(f"Error parsing timestamp {timestamp_str}: {e}")
        return False

def get_remote_file_size(url):
    """Returns the size of the remote file in bytes."""
    response = requests.head(url)
    if response.status_code == 200:
        return int(response.headers.get('Content-Length', 0))
    return 0

def download_file(file_name, timestamp):
    """Downloads the specified GRIB file and renames it based on the timestamp."""
    url = urljoin(base_url, file_name)
    new_file_name = f"{timestamp}.grib2.gz"
    output_path = os.path.join(grib_folder, new_file_name)

    print(f"Downloading {file_name}...")
    response = requests.get(url, stream=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return output_path

def output_to_npy(grib_file_location, npy_file_location):
    ds = xr.open_dataset(grib_file_location, engine='cfgrib')
    data_array = ds.to_array().values
    np.save(npy_file_location, data_array)

def decompress_file(compressed_path, decompressed_path):
    with gzip.open(compressed_path, 'rb') as f_in:
        with open(decompressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Decompressed {compressed_path} to {decompressed_path}")

def delete_work_files(directory_path):
    patterns = [
        os.path.join(directory_path, '*.grib2.gz'),
        os.path.join(directory_path, '*.grib2'),
        os.path.join(directory_path, '*.grib2.*.idx'),
    ]
    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            os.remove(file_path)
            print(f"Deleted: {file_path}")

def process_all_recent_files():
    files = get_grib_files()

    if not files:
        print("No files found.")
        return

    for file_name in files:
        timestamp = get_timestamp_from_filename(file_name)
        if not timestamp:
            continue
        if not is_within_last_24_hours(timestamp):
            continue
        npy_file_location = os.path.join(npy_directory, f"{timestamp}.npy")
        compressed_file_location = os.path.join(grib_folder, f"{timestamp}.grib2.gz")
        decompressed_file_location = os.path.join(grib_folder, f"{timestamp}.grib2")
        url = urljoin(base_url, file_name)
        remote_file_size = get_remote_file_size(url)
        need_redownload = False
        if os.path.exists(npy_file_location):
            local_file_size = os.path.getsize(npy_file_location)
            if local_file_size > 0:
                print(f"{npy_file_location} already exists and is non-empty. Skipping.")
                continue
            else:
                print(f"{npy_file_location} exists but is empty. Redownloading.")
                os.remove(npy_file_location)
                need_redownload = True
        else:
            print(f"{npy_file_location} does not exist. Downloading.")
            need_redownload = True

        print(f"Need to redownload: {need_redownload}")
        # Download if needed
        if need_redownload:
            download_file(file_name, timestamp)
        # Decompress, convert, cleanup
        decompress_file(compressed_file_location, decompressed_file_location)
        output_to_npy(decompressed_file_location, npy_file_location)
        delete_work_files(grib_folder)
        if os.path.exists(decompressed_file_location):
            os.remove(decompressed_file_location)
            print(f"Deleted: {decompressed_file_location}")

if __name__ == "__main__":
    process_all_recent_files()
