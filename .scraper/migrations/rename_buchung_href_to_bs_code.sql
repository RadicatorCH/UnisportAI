-- Migration: Rename buchung_href to bs_code in sportkurse table
-- Execute this in your Supabase SQL Editor

ALTER TABLE sportkurse 
RENAME COLUMN buchung_href TO bs_code;

