-- Migration script to setup employee_users table for admin and staff
-- Run this SQL script on your MySQL database

USE sevenext;

-- Check if employee_users table exists, if not create it
CREATE TABLE IF NOT EXISTS employee_users (
    id INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'staff', 'super_admin') NOT NULL DEFAULT 'staff',
    status ENUM('active', 'inactive', 'blocked') NOT NULL DEFAULT 'active',
    
    -- Address fields
    address TEXT NULL,
    city VARCHAR(100) NULL,
    state VARCHAR(100) NULL,
    pincode VARCHAR(20) NULL,
    
    -- Permissions for staff users (stored as JSON)
    permissions JSON NULL,
    
    -- Metadata
    phone VARCHAR(15) NULL,
    last_login DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add columns if they don't exist (for existing tables)
-- This is safe to run even if columns already exist

SET @dbname = 'sevenext';
SET @tablename = 'employee_users';

-- Add address if not exists
SET @col_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'address'
);
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE employee_users ADD COLUMN address TEXT NULL AFTER status',
    'SELECT "address column already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add city if not exists
SET @col_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'city'
);
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE employee_users ADD COLUMN city VARCHAR(100) NULL AFTER address',
    'SELECT "city column already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add state if not exists
SET @col_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'state'
);
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE employee_users ADD COLUMN state VARCHAR(100) NULL AFTER city',
    'SELECT "state column already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add pincode if not exists
SET @col_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'pincode'
);
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE employee_users ADD COLUMN pincode VARCHAR(20) NULL AFTER state',
    'SELECT "pincode column already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add permissions if not exists
SET @col_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = 'permissions'
);
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE employee_users ADD COLUMN permissions JSON NULL AFTER pincode',
    'SELECT "permissions column already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verify the changes
DESCRIBE employee_users;

SELECT 'Employee Users table setup completed successfully!' as Status;
