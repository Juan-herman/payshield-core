-- ============================================================================
-- PayShield Core - Esquema de Base de Datos Transaccional
-- ============================================================================

-- 1. Tabla de Cuentas y Balances
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    -- Regla de integridad financiera: el saldo no puede ser negativo
    balance NUMERIC(12, 2) DEFAULT 0.00 CHECK (balance >= 0)
);

-- 2. Ledger de Transacciones (Auditoría contable inmutable)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    sender_id INT REFERENCES accounts(id),
    receiver_id INT REFERENCES accounts(id),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL
);

-- 3. Datos iniciales simulados para pruebas
INSERT INTO accounts (username, password_hash, role, balance) VALUES
('comercio_central', 'hash_pass_comercio', 'merchant', 0.00),
('usuario_demo', 'hash_pass_demo', 'user', 150000.00);
