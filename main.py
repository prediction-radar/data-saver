import os
import sys

# Import functions from the existing scripts
from download_grib import download_latest_file, decompress_file, delete_idx_files, delete_file, grib_folder
from grib2_to_npy import grib2_to_npy

npy_folder = "npy_files/"
os.makedirs(npy_folder, exist_ok=True)

if __name__ == "__main__":
    # Download and decompress the latest file
    downloaded_file_name = download_latest_file()
    if downloaded_file_name is not None:
        compressed_file_location = os.path.join(grib_folder, downloaded_file_name + ".grib2.gz")
        decompressed_file_location = os.path.join(grib_folder, downloaded_file_name + ".grib2")
        decompress_file(compressed_file_location, decompressed_file_location)
        delete_idx_files(grib_folder)
        delete_file(compressed_file_location)
        # Convert to .npy and move to npy_files/
        npy_path = os.path.join(npy_folder, downloaded_file_name + ".npy")
        grib2_to_npy(decompressed_file_location)
        # Move the .npy file to npy_files/
        generated_npy = os.path.splitext(decompressed_file_location)[0] + ".npy"
        if os.path.exists(generated_npy):
            os.replace(generated_npy, npy_path)
            print(f"Moved {generated_npy} to {npy_path}")
        # Optionally, delete the .grib2 file
        delete_file(decompressed_file_location)
