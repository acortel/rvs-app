-- Database migration: Add superuser role support
-- File: add_superuser_column.sql

-- Add is_superuser column to users_list table
ALTER TABLE users_list 
ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE;

-- Set all existing users as non-superusers (if any NULL values exist)
UPDATE users_list 
SET is_superuser = FALSE 
WHERE is_superuser IS NULL;

-- Optional: Promote a specific user to superuser
-- Uncomment and replace 'username' with actual username
-- UPDATE users_list SET is_superuser = TRUE WHERE username = 'admin';

-- Verify the changes
-- SELECT username, firstname, lastname, is_superuser FROM users_list ORDER BY firstname, lastname;
