CREATE TABLE IF NOT EXISTS model_metrics (
    model_name VARCHAR(50),
    train_size INTEGER,
    mae FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
