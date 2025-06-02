import sys
import os
import xarray as xr
import numpy as np

def grib2_to_npy(grib2_path):
    # Load GRIB2 file with xarray and cfgrib engine
    ds = xr.open_dataset(grib2_path, engine="cfgrib")
    # Get the first data variable
    data_var = list(ds.data_vars)[0]
    data = ds[data_var].values
    # Prepare output path
    npy_path = os.path.splitext(grib2_path)[0] + ".npy"
    # Save as .npy
    np.save(npy_path, data)
    print(f"Saved {npy_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python grib2_to_npy.py <path_to_grib2_file>")
        sys.exit(1)
    grib2_file = sys.argv[1]
    grib2_to_npy(grib2_file)
