import tabsdata as td


@td.subscriber(
    tables=["td_booth_visitors"],  # Source Tabsdata table to subscribe to
    destination=td.PostgresDestination(
        uri="postgresql://ef-hard-spotlight-g63h4ojk.us-west-2.aws.neon.tech/neondb?sslmode=require",  # Postgres database URI
        destination_table=["public.event_booth_visitors"],  # Target table in Postgres
        credentials=td.UserPasswordCredentials(td.EnvironmentSecret("neon_username"), td.EnvironmentSecret("neon_password")),
        if_table_exists="replace",  # Replace table if it already exists
    ),
)
def subscribe_neon(tf1: td.TableFrame) -> td.TableFrame:
    return tf1
