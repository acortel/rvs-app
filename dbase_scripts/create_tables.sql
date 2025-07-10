-- Create normalize_path function
CREATE OR REPLACE FUNCTION normalize_path(path text)
RETURNS text AS $$
BEGIN
    RETURN replace(path, '\', '/');
END;
$$ LANGUAGE plpgsql;

-- Create birth_index table
CREATE TABLE IF NOT EXISTS birth_index (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    date_of_birth DATE,
    sex VARCHAR(10),
    page_no INTEGER,
    book_no INTEGER,
    reg_no VARCHAR(50),
    date_of_reg DATE,
    place_of_birth VARCHAR(255),
    name_of_mother VARCHAR(255),
    nationality_mother VARCHAR(100),
    name_of_father VARCHAR(255),
    nationality_father VARCHAR(100),
    parents_marriage_date DATE NULL,
    parents_marriage_place VARCHAR(255) NULL,
    attendant VARCHAR(255),
    late_registration BOOLEAN DEFAULT FALSE,
    twin BOOLEAN DEFAULT FALSE,
    file_path VARCHAR(255) UNIQUE,
    remarks TEXT NULL
);

-- Create death_index table
CREATE TABLE IF NOT EXISTS death_index (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    date_of_death DATE,
    sex VARCHAR(10),
    page_no INTEGER,
    book_no INTEGER,
    reg_no VARCHAR(50),
    date_of_reg DATE,
    age INTEGER,
    civil_status VARCHAR(50),
    nationality VARCHAR(100),
    place_of_death VARCHAR(255),
    cause_of_death TEXT,
    corpse_disposal VARCHAR(255),
    late_registration BOOLEAN DEFAULT FALSE,
    file_path VARCHAR(255) UNIQUE,
    remarks TEXT NULL
); 

-- Create marriage_index table
CREATE TABLE IF NOT EXISTS marriage_index (
    id SERIAL PRIMARY KEY,
    husband_name VARCHAR(255),
    wife_name VARCHAR(255),
    date_of_marriage DATE,
    page_no INTEGER,
    book_no INTEGER,
    reg_no VARCHAR(50),
    husband_age INTEGER,
    wife_age INTEGER,
    husb_nationality VARCHAR(100),
    wife_nationality VARCHAR(100),
    husb_civil_status VARCHAR(50),
    wife_civil_status VARCHAR(50),
    husb_mother VARCHAR(255),
    wife_mother VARCHAR(255),
    husb_father VARCHAR(255),
    wife_father VARCHAR(255),
    date_of_reg DATE,
    place_of_marriage VARCHAR(255),
    ceremony_type VARCHAR(100),
    late_registration BOOLEAN DEFAULT FALSE,
    file_path VARCHAR(255) UNIQUE,
    remarks TEXT NULL
); 

-- Add remarks column to birth_index
ALTER TABLE birth_index ADD COLUMN IF NOT EXISTS remarks TEXT NULL;

-- Add remarks column to death_index
ALTER TABLE death_index ADD COLUMN IF NOT EXISTS remarks TEXT NULL;

-- Add remarks column to marriage_index
ALTER TABLE marriage_index ADD COLUMN IF NOT EXISTS remarks TEXT NULL; 