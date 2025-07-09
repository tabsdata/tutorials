import tabsdata as td


@td.subscriber(
    tables=["customers", "customers_cdc"],  # Source Tabsdata table to subscribe to
    destination=td.PostgresDestination(
        uri="postgresql://ef-hard-spotlight-g63h4ojk.us-west-2.aws.neon.tech/neondb?sslmode=require",  # Postgres database URI
        destination_table=["public.customers", "public.customers_cdc"],  # Target table in Postgres
        credentials=td.UserPasswordCredentials(td.EnvironmentSecret("NEON_USERNAME"), td.EnvironmentSecret("NEON_PASSWORD")),
        if_table_exists="replace",  # Replace table if it already exists
    ),
)
def sub_postgres(customers: td.TableFrame, customers_cdc: td.TableFrame ) -> td.TableFrame:
    return customers, customers_cdc

