-- Migration script to add address and permissions fields to users table
-- Run this SQL script on your MySQL database

USE sevenxt;

-- Add address fields
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS address TEXT NULL AFTER status,
ADD COLUMN IF NOT EXISTS city VARCHAR(100) NULL AFTER address,
ADD COLUMN IF NOT EXISTS state VARCHAR(100) NULL AFTER city,
ADD COLUMN IF NOT EXISTS pincode VARCHAR(20) NULL AFTER state,
ADD COLUMN IF NOT EXISTS permissions JSON NULL AFTER pincode;

-- Verify the changes
DESCRIBE users;
