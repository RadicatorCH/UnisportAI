-- Migration: Rename buchung_href to bs_code in sportkurse table
-- Execute this in your Supabase SQL Editor

-- Rename the column from buchung_href to bs_code
ALTER TABLE sportkurse 
RENAME COLUMN buchung_href TO bs_code;

-- Optional: Add comment for documentation
COMMENT ON COLUMN sportkurse.bs_code IS 'Booking Session Code (hidden input from form), not user-specific but page-specific';

