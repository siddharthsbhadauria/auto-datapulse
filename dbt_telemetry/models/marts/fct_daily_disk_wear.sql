-- Gold Analytics Mart: Daily Infrastructure Efficiency & Usage Summaries
WITH daily_agg AS (
    SELECT 
        record_date,
        COUNT(*) AS total_samples,
        ROUND(AVG(cpu_percent), 2) AS avg_cpu_percent,
        ROUND(MAX(cpu_percent), 2) AS max_cpu_percent,
        ROUND(AVG(ram_percent), 2) AS avg_ram_percent,
        ROUND(MAX(ram_used_gb), 2) AS max_ram_used_gb,
        ROUND(MAX(disk_percent), 2) AS max_disk_percent
    FROM {{ ref('stg_telemetry') }}
    GROUP BY record_date
)
SELECT 
    record_date,
    total_samples,
    avg_cpu_percent,
    max_cpu_percent,
    avg_ram_percent,
    max_ram_used_gb,
    max_disk_percent,
    CASE 
        WHEN max_cpu_percent > 90 THEN 'HIGH_LOAD'
        WHEN max_ram_percent > 85 THEN 'MEMORY_PRESSURE'
        ELSE 'OPTIMAL'
    END AS operational_health_tier
FROM daily_agg
ORDER BY record_date DESC
