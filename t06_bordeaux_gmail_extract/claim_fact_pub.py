import tabsdata as td
import os
from typing import List
import polars as pl
import functools
import imaplib
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime, date, timedelta
from io import BytesIO

class GmailPublisher(td.SourcePlugin):

    def chunk(self, working_dir: str) -> str:
        imap_host = td.EnvironmentSecret("imap_host").secret_value
        imap_port = td.EnvironmentSecret("imap_port").secret_value
        email_user = td.EnvironmentSecret("imap_email_user").secret_value
        email_password = td.EnvironmentSecret("imap_email_password").secret_value

        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(email_user, email_password)
        mail.select('inbox')
        date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        search_criteria = f'(UNSEEN SINCE "{date_since}")'
        status, email_ids = mail.search(None, search_criteria)
        email_id_list = email_ids[0].split()
        filenames_csv = []


        for email_id in email_id_list:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])

            subject = msg.get('subject', 'No Subject')
            sender = msg.get('from', 'Unknown Sender')
            print(f"Processing email from {sender} with subject: {subject}")

            if msg.get_content_maintype() == 'multipart':
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename and filename.endswith('.csv') and filename.startswith('TPA_Claim_Data'):
                            filename = filename.removesuffix(".csv")
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")                        
                            payload = part.get_payload(decode=True)
                            df = pl.read_csv(BytesIO(payload))

                            destination_file = f"{timestamp}_{filename}.parquet" 
                            destination_path = os.path.join(working_dir, destination_file)

                            df.write_parquet(destination_path)
                            filenames_csv.append(destination_file)
                            

        return [filenames_csv]


def standardize_schema(tf: td.TableFrame):
    target_schema = {
        "policy_number": td.String,
        "months_insured": td.Int64,
        "has_claims": td.Boolean,
        "items_insured": td.Int64,
        "claim_reference": td.String,
        "insured_name": td.String,
        "policy_start_date": td.String,
        "date_of_loss": td.String,
        "date_reported": td.String,
        "claim_status": td.String,
        "loss_type": td.String,
        "paid_amount": td.Float64,
        "reserve_amount": td.Float64,
        "total_incurred": td.Float64,
        "claim_propensity": td.Float64,
        "broker_id": td.String
    }    
    tf = tf.with_columns(*[(td.col(name) if name in tf.columns() else td.lit(None).cast(dtype).alias(name)) for name, dtype in target_schema.items()])  
    tf = tf.select(list(target_schema.keys()))  
    return tf

@td.publisher(
    source=GmailPublisher(),  # Initialize the source plugin
    tables="claims_fact_today",                 # Define the output table name
)

def claim_fact_pub(tf: List[td.TableFrame]):
    tf=  [standardize_schema(tf1) for tf1 in tf]
    union_tf= functools.reduce(lambda a, b: td.concat([a,b]), tf)
    union_tf = union_tf.with_columns(td.lit(date.today()).alias("date_loaded"))
    return union_tf.unique(subset=["policy_number", "claim_reference"], keep="first")













