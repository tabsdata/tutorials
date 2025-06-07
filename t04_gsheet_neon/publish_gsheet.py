import os
import io
import requests
import polars as pl
import tabsdata as td


class GoogleSheetsPublisher(td.SourcePlugin):

    def chunk(self, working_dir: str) -> str:
        # Define the Google Sheets endpoint (published as CSV)
        base_endpoint = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRqkNX0lXsOtMLPOPZrxwXPcTTeKap-EjGecuILAhCmb-0vqwhuHrk2gF5pJDhhznKt_Eh9XTh6xu0C/pub?gid=1332407920&single=true&output=csv"

        # Fetch the CSV data from the endpoint
        csv_response = requests.get(base_endpoint)

        # Read the CSV data into a Polars DataFrame
        df = pl.read_csv(io.BytesIO(csv_response.content))

        # Define the destination Parquet file name
        destination_file = "data.parquet"
        destination_path = os.path.join(working_dir, destination_file)

        # Write the Polars DataFrame to a Parquet file
        df.write_parquet(destination_path)

        # Return the file path relative to the working directory
        return destination_file


@td.publisher(
    source=GoogleSheetsPublisher(),  # Initialize the source plugin
    tables="td_booth_visitors",                 # Define the output table name
)
def publish_gsheet(tf1: td.TableFrame) -> td.TableFrame:
    # Drop 'favorite_color' column from the table
    tf1 = tf1.drop("favorite_color")
    return tf1
