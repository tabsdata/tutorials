import tabsdata as td

SALESFORCE_USER = td.EnvironmentSecret("SALESFORCE_USER")
SALESFORCE_PASSWORD = td.EnvironmentSecret("SALESFORCE_PASSWORD")
SALESFORCE_TOKEN = td.EnvironmentSecret("SALESFORCE_TOKEN")
SALESFORCE_REPORT = td.EnvironmentSecret("SALESFORCE_REPORT").secret_value


@td.publisher(
    source=td.SalesforceReportSource(
        report=SALESFORCE_REPORT,
        find_report_by="name",
        column_name_strategy="columnName",
        credentials=td.SalesforceTokenCredentials(
            SALESFORCE_USER,
            SALESFORCE_PASSWORD,
            SALESFORCE_TOKEN,
        ),
    ),
    tables="sf_snapshot",
)
def salesforce_pub(
    tf: td.TableFrame,
):
    return tf
