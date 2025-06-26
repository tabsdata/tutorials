import oracledb
connection = oracledb.connect(
    user="TABSDATA_USER",
    password="mypassword1",
    dsn="127.0.0.1:1521/orclpdb1"
)

cursor = connection.cursor()
cursor.execute("SELECT * FROM TABSDATA_USER.customers")
row = cursor.fetchall()
print(row)

cursor.close()
connection.close()
