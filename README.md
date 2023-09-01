# py-mwx
Python utility for converting Vaisala MWX sounding data to CSV

To convert an MWX file into a CSV file, either run this script directly or import it and use the `mwx_to_csv` function.

# Usage
This is a Python script. Python, with pandas and lxml, must be installed on your system.

Then run `python mwx_to_csv.py`.

## Arguments
`infile` (required) - the input MWX file, either absolute or relative path.

`outfile` (optional) - the output CSV file. If this is not specified, the same name as `infile` will be used with `.mwx` replaced with `.csv`.
