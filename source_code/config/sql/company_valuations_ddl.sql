-- DDL for Company Valuations data table
-- Captures pricing and valuation data from various external sources

CREATE TABLE IF NOT EXISTS company_valuations (
    -- Primary key and metadata
    company_valuation_id BIGINT PRIMARY KEY,
    as_of_date DATE NOT NULL,
    price_source VARCHAR(50) NOT NULL DEFAULT 'External',
    
    -- Core company information
    company VARCHAR(255),
    sector_subsector VARCHAR(255),
    
    -- Price data (split from composite price column)
    price DECIMAL(15,2),
    price_change_amt DECIMAL(15,2),
    price_change_perc DECIMAL(8,4),
    
    -- Other pricing and financial data
    last_matched_price VARCHAR(50),
    share_class VARCHAR(100),
    post_money_valuation VARCHAR(50), -- cleaned from "Post-Money Valuation2"
    price_per_share DECIMAL(15,2),
    amount_raised VARCHAR(50),
    
    -- Raw data preservation for future parsing needs
    raw_data_json JSONB,
    
    -- Audit fields
    created_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    UNIQUE(company, as_of_date, price_source)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_company_valuations_as_of_date ON company_valuations(as_of_date);
CREATE INDEX IF NOT EXISTS idx_company_valuations_company ON company_valuations(company);
CREATE INDEX IF NOT EXISTS idx_company_valuations_sector ON company_valuations(sector_subsector);
CREATE INDEX IF NOT EXISTS idx_company_valuations_price_source ON company_valuations(price_source);

-- Comments for documentation
COMMENT ON TABLE company_valuations IS 'Company pricing and valuation data from various external sources';
COMMENT ON COLUMN company_valuations.as_of_date IS 'Date when the pricing data was captured';
COMMENT ON COLUMN company_valuations.price_source IS 'Source of the pricing data (e.g., ForgeGlobal, PitchBook, etc.)';
COMMENT ON COLUMN company_valuations.price IS 'Current price extracted from composite price field';
COMMENT ON COLUMN company_valuations.price_change_amt IS 'Price change amount extracted from price data';
COMMENT ON COLUMN company_valuations.price_change_perc IS 'Price change percentage extracted from price data';
COMMENT ON COLUMN company_valuations.post_money_valuation IS 'Post-money valuation (cleaned from Post-Money Valuation2)';
COMMENT ON COLUMN company_valuations.raw_data_json IS 'Complete raw CSV row data for future parsing if needed';