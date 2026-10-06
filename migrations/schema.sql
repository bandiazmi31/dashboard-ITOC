CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('Admin', 'Lead', 'ITOC Analyst', 'EOS Branch', 'Manajemen')),
    unit VARCHAR(100),
    job VARCHAR(100),
    group_shift VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    req_id VARCHAR(100) UNIQUE NOT NULL,
    mode VARCHAR(50),
    requester VARCHAR(255),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    subject TEXT,
    technician VARCHAR(255),
    sla_name VARCHAR(100),
    priority VARCHAR(50),
    created_time TIMESTAMP,
    resolved_time TIMESTAMP,
    status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE network_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sensor_name VARCHAR(255),
    device VARCHAR(255),
    location VARCHAR(255),
    isp VARCHAR(100),
    target_sla DECIMAL(5,2),
    up_time INTEGER,
    down_time INTEGER,
    avg_traffic DECIMAL(10,2),
    volume DECIMAL(10,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE soc_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date TIMESTAMP,
    threat_name VARCHAR(255),
    category VARCHAR(100),
    action VARCHAR(100),
    severity VARCHAR(50) CHECK (severity IN ('Critical', 'High', 'Medium', 'Low')),
    source_ip VARCHAR(45),
    destination_ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE handovers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    site VARCHAR(255),
    priority VARCHAR(50) CHECK (priority IN ('Normal', 'Tinggi')),
    date TIMESTAMP,
    shift VARCHAR(50) CHECK (shift IN ('Pagi', 'Sore', 'Malam')),
    open BOOLEAN DEFAULT TRUE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE access_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_tickets_req_id ON tickets(req_id);
CREATE INDEX idx_tickets_created_time ON tickets(created_time);
CREATE INDEX idx_soc_events_date_severity ON soc_events(date, severity);
CREATE INDEX idx_handovers_open_shift ON handovers(open, shift);
