"""
mwx_to_csv.py

Version: 2024.10.17
Copyright: C. Miller
License: MIT

*****************************
Convert MWX file with addon sensor data so that XDATA format can be parsed.

Warning: If multiple lines of data are recorded with the same timestamp (which
seems to happen in a small subset in test MWX files used), only one value will
be kept in the processed output. Please retain original MWX files!

Note: lxml must be installed in your Python environment for this code to run.

*****************************

"""

# Import necessary libraries
import zipfile as zf
import pandas as pd

# Function to read in MWX file and output a CSV
def mwx_to_csv(infile,outfile=None):
    # The MWX file is just a zip file with a different extension. Unzip it.
    try:
        with zf.ZipFile(infile,"r") as mwx:
            try:
                # Use a variable called 'this_file' to allow for a good error message if reading fails
                # Read in the pressure, temp, and humidity (PTU)
                this_file = "PtuResults.xml"
                ptu_results = mwx.read(this_file)
                # Read in the lat, lon, and altitude
                this_file = "GpsResults.xml"
                gps_results = mwx.read(this_file)
                # Read in north and east wind
                this_file = "WindResults.xml"
                wind_results = mwx.read(this_file)
                # Read in metadata about sounding
                this_file = "Soundings.xml"
                soundings = mwx.read(this_file)
                # Read in surface observations
                this_file = "SurfaceObservations.xml"
                surface_file = mwx.read(this_file)
            except:
                # Print a helpful error if a file fails to read properly
                Exception(f"Could not read MWX file. {this_file} not found.")
                return
    except:
        print(f"Error: {infile} could not be opened.")
        return

    # Parse the metadata
    try:
        sounding_info = pd.read_xml(soundings,parse_dates=["BeginTime","RadioResetTime"])
    except:
        print("\n\nThis program requires lxml to be installed in your Python environment.")
        return

    # Parse the PTU data
    ptu = pd.read_xml(ptu_results,parse_dates=["DataSrvTime"])

    # Convert radio time (seconds) to UTC timestamp
    ptu["DateTime"] = pd.to_datetime(ptu["RadioRxTimePk"]+1,unit="s",origin=sounding_info["RadioResetTime"].iloc[0]).round("s")
    ptu.set_index("DateTime",inplace=True)
    # Convert Kelvin to degC
    ptu["Temperature"] = (ptu["Temperature"] - 273.15).round(2)
    # Round values
    ptu["SensorPressure"] = ptu["SensorPressure"].round(2)
    ptu["Humidity"] = ptu["Humidity"].round(2)

    # Parse the GPS data
    gps = pd.read_xml(gps_results)
    gps["DateTime"] = pd.to_datetime(gps["RadioRxTimePk"]+1,unit="s",origin=sounding_info["RadioResetTime"].iloc[0]).round("s")
    gps.set_index("DateTime",inplace=True)
    # Round values
    gps["Wgs84Latitude"] = gps["Wgs84Latitude"].round(6)
    gps["Wgs84Longitude"] = gps["Wgs84Longitude"].round(6)
    gps["Wgs84Altitude"] = gps["Wgs84Altitude"].round(6)


    # Parse the wind speed data
    wind = pd.read_xml(wind_results)
    wind["DateTime"] = pd.to_datetime(wind["RadioRxTimePk"]+1,unit="s",origin=sounding_info["RadioResetTime"].iloc[0]).round("s")
    wind.set_index("DateTime",inplace=True)
    # Round values
    wind["North"] = wind["North"].round(2)
    wind["East"] = wind["East"].round(2)

    # Parse the surface observations
    surface = pd.read_xml(surface_file)

    # Round timestamps to the nearest second
    ptu.set_index(ptu.index.round("s"),inplace=True)
    gps.set_index(gps.index.round("s"),inplace=True)
    wind.set_index(wind.index.round("s"),inplace=True)

    # Combine data into a single dataframe
    ptu_output = ptu.reset_index().drop_duplicates(subset="DateTime").set_index("DateTime")
    gps_output = gps.reset_index().drop_duplicates(subset="DateTime").set_index("DateTime")
    wind_output = wind.reset_index().drop_duplicates(subset="DateTime").set_index("DateTime")
    combined_data = pd.concat([ptu_output,gps_output,wind_output],join="outer",axis=1)

    # Rename columns to have nicer names
    combined_data.rename(columns={
        "SensorPressure":"Pressure",
        "Wgs84Latitude":"GPSLatitude",
        "Wgs84Longitude":"GPSLongitude",
        "Wgs84Altitude":"GPSAltitude",
        "North":"WindNorth",
        "East":"WindEast"},inplace=True)

    # Create a text header for metadata alongside the CSV
    output_header = f"""RADIOSONDE DATA FOR {sounding_info["StationName"][0]} {sounding_info["BeginTime"].iloc[0].round("s").isoformat()} LAUNCH

ReleaseTime:{sounding_info["BeginTime"].iloc[0].round("s").isoformat()}
StationName:{sounding_info["StationName"][0]}
StationAltitude:{sounding_info["Altitude"].round(2)[0]}
StationLatitude:{sounding_info["Latitude"].round(2)[0]}
StationLongitude:{sounding_info["Longitude"].round(2)[0]}
FlightPressureMin:{sounding_info["MinPressure"].round(2)[0]}
FlightAltitudeMax:{sounding_info["MaxAltitude"].round(2)[0]}
FlightAscentRate:{sounding_info["AscentRate"].round(2)[0]}
SurfacePressure:{surface["Pressure"].round(2)[0]}
SurfaceTemperature:{(surface["Temperature"]-273.15).round(2)[0]}
SurfaceHumidity:{surface["Humidity"].round(2)[0]}
SurfaceWindSpeed:{surface["WindSpeed"].round(2)[0]}
SurfaceWindDirection:{surface["WindDirection"].round(2)[0]}

,(hPa),(degC),(%),(m),(m/s),(m/s),(WGS84),(WGS84),(WGS84),(status)
"""

    # Make a list of columns to export
    output_columns = ["Pressure","Temperature","Humidity","Height","WindNorth","WindEast","GPSLatitude","GPSLongitude","GPSAltitude","Status"]

    # Convert data from selected columns into text for export
    output_data = combined_data.dropna(subset="Height").to_csv(columns=output_columns,lineterminator="\n")

    # Set a filename based on input file if none has been set
    if outfile == None:
        outfile = infile.rstrip(".mwx")+".csv"

    # Save a new file with the header plus text data
    save_file = open(outfile,"w")
    save_file.write(output_header+output_data)
    save_file.close()
    print(f"\nWrote converted data to {outfile}\n")


if __name__ == "__main__":
    # Default function accepts user input and converts a file
    print("\n\nFormat conversion utility for MWX to CSV.\n\n")

    # Get an input file
    input_file = input("Input filename: ")
    # Guess what to name the output
    default_output = input_file.rstrip(".mwx")+".csv"
    # Check the output file
    output_file = input(f"Output file (Default {default_output}): ")
    if output_file == "":
        output_file = default_output
    # Run the conversion
    mwx_to_csv(input_file,output_file)