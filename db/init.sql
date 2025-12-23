-- Simple init script: create patients table and insert two sample patients
CREATE TABLE IF NOT EXISTS patients (
  id SERIAL PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  date_of_birth DATE,
  medical_record_number TEXT
);

INSERT INTO patients (first_name, last_name, date_of_birth, medical_record_number)
VALUES ('John', 'Doe', '1980-01-15', 'MRN001')
ON CONFLICT DO NOTHING;

INSERT INTO patients (first_name, last_name, date_of_birth, medical_record_number)
VALUES ('Jane', 'Smith', '1992-06-23', 'MRN002')
ON CONFLICT DO NOTHING;
