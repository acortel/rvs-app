-- Add released_by column to releasing_log table
ALTER TABLE releasing_log
ADD COLUMN released_by TEXT;

-- Set a default value for existing records (you may want to adjust this)
UPDATE releasing_log
SET released_by = 'system_migration'
WHERE released_by IS NULL;

-- Make the column NOT NULL after setting default values
ALTER TABLE releasing_log
ALTER COLUMN released_by SET NOT NULL; 