CREATE DATABASE IF NOT EXISTS curious_mind;
USE curious_mind;

CREATE TABLE IF NOT EXISTS admin (
    id INT PRIMARY KEY AUTO INCREMENT,
    first_name VARCHAR (100) NOT NULL,
    middle_name VARCHAR (100),
    last_name VARCHAR (100) NOT NULL,
    email VARCHAR (100) NOT NULL UNIQUE,
)

CREATE TABLE IF NOT EXISTS school (
    id INT PRIMARY KEY AUTO INCREMENT,
    school_name VARCAHR (250) NOT NULL,
    region VARCHAR (100) NOT NULL,
    school_address VARCHAR (500) NOT NULL,
    school_email VARCHAR (100) NOT NULL UNIQUE,
    school_contact VARCHAR (15) NOT NULL,
    contact_person NUMBER (15) NOT NULL,
    

)