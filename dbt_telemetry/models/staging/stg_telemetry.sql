-- Staging Model: Clean and parse raw telemetry snapshots
WITH raw_data AS (
    SELECT 
        timestamp,
        cpu_percent,
        ram_used_gb,
        ram_total_gb,
        ram_percent,
        disk_used_gb,
        disk_total_gb,
        disk_percent,
        status
    FROM {{ source('raw_telemetry', 'snapshots') }}
)
SELECT 
    CAST(timestamp AS TIMESTAMP) AS record_timestamp,
    CAST(timestamp AS DATE) AS record_date,
    cpu_percent,
    ram_used_gb,
    ram_total_gb,
    ram_percent,
    disk_used_gb,
    disk_total_gb,
    disk_percent,
    status
FROM raw_data
