ALTER SESSION SET CURRENT_SCHEMA = TABSDATA_USER;
ALTER SESSION SET CONTAINER=ORCLPDB1;

-- Drop customers if it exists
BEGIN
  EXECUTE IMMEDIATE 'DROP TABLE TABSDATA_USER.customers PURGE';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -942 THEN -- -942 = table or view does not exist
      RAISE;
    END IF;
END;
/
  
-- Create the table with appropriate column types
CREATE TABLE customers (
  seq   NUMBER,
  first VARCHAR2(100),
  last  VARCHAR2(100),
  age   NUMBER,
  state VARCHAR2(2),
  zip   VARCHAR2(10)
);

-- Insert sample data into table
INSERT ALL
  INTO customers(seq, first, last, age, state, zip) VALUES (1, 'May',     'James',    22, 'NY', '80402')
  INTO customers(seq, first, last, age, state, zip) VALUES (2, 'Irene',   'McKenzie', 35, 'MO', '24473')
  INTO customers(seq, first, last, age, state, zip) VALUES (3, 'Polly',   'Phillips', 56, 'WY', '68070')
  INTO customers(seq, first, last, age, state, zip) VALUES (4, 'Vera',    'Clarke',   48, 'VT', '86838')
  INTO customers(seq, first, last, age, state, zip) VALUES (5, 'Garrett', 'Cross',    19, 'OK', '26862')
  INTO customers(seq, first, last, age, state, zip) VALUES (6, 'Roy',     'Chavez',   40, 'CO', '79642')
  INTO customers(seq, first, last, age, state, zip) VALUES (7, 'Gene',    'Barber',   22, 'ND', '89517')
  INTO customers(seq, first, last, age, state, zip) VALUES (8, 'Annie',   'Spencer',  42, 'AK', '44788')
  INTO customers(seq, first, last, age, state, zip) VALUES (9, 'Ina',     'Dean',     26, 'OH', '45074')
SELECT * FROM dual;

COMMIT;
/

SELECT * FROM TABSDATA_USER.customers;
