ALTER SESSION SET CONTAINER=ORCLPDB1;

CREATE USER TABSDATA_USER IDENTIFIED BY mypassword1;
GRANT CONNECT, RESOURCE TO TABSDATA_USER;
GRANT CREATE SESSION TO TABSDATA_USER;
GRANT UNLIMITED TABLESPACE TO TABSDATA_USER;




