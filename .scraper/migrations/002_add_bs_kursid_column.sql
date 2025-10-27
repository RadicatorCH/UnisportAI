-- Migration: Add bs_kursid column to sportkurse table
-- Execute this in your Supabase SQL Editor

-- Add the bs_kursid column for storing the button name for booking
ALTER TABLE sportkurse 
ADD COLUMN IF NOT EXISTS bs_kursid TEXT;

-- Add comment for documentation
COMMENT ON COLUMN sportkurse.bs_kursid IS 'Submit button name for booking (e.g., BS_Kursid_23421)';

