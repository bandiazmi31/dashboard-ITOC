-- SOC Import Batch Tracking Table
-- Tracks each upload batch for audit trail and period management

CREATE TABLE IF NOT EXISTS soc_upload_batch (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    template_type VARCHAR(50) NOT NULL,
    period_start DATE,
    period_end DATE,
    total_records INTEGER,
    skipped_records INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    CONSTRAINT valid_template_type CHECK (template_type IN ('threat_hc', 'url_blocked', 'traffic_rule', 'traffic_daily'))
);

-- Link soc_events to upload batch for traceability
ALTER TABLE soc_events ADD COLUMN IF NOT EXISTS upload_batch_id UUID REFERENCES soc_upload_batch(id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_soc_upload_batch_id ON soc_events(upload_batch_id);
CREATE INDEX IF NOT EXISTS idx_soc_upload_template ON soc_upload_batch(template_type, period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_soc_upload_date ON soc_upload_batch(upload_date);

-- Comments for documentation
COMMENT ON TABLE soc_upload_batch IS 'Tracks each SOC data import batch for audit and period management';
COMMENT ON COLUMN soc_upload_batch.template_type IS 'Type of SOC template: threat_hc, url_blocked, traffic_rule, traffic_daily';
COMMENT ON COLUMN soc_upload_batch.skipped_records IS 'Number of rows skipped due to validation errors';
