import tabsdata as td


@td.transformer(
    input_tables=["raw_customer_data"],
    output_tables=["masked_customer_data"],
)
def mask_trf(tf: td.TableFrame):
    masking_columns = cols_to_mask = [
        "first_name",
        "last_name",
        "ip_address",
        "phone_number",
        "email",
        "date_of_birth",
        "SSN",
        "Address",
        "City",
        "Postal_Code",
        "notes_extra",
    ]
    for i in masking_columns:
        tf = tf.with_columns(td.col(i).cast(td.String).str.replace_all(".", "*"))
    return tf
