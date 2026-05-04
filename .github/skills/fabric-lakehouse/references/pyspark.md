### Spark Configuration (Best Practices)

```python
spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
spark.conf.set("spark.microsoft.delta.optimizeWrite.enabled", "true")
```

### Reading Data

```python
# CSV
df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load("Files/bronze/data.csv")

# JSON
df = spark.read.format("json").load("Files/bronze/data.json")

# Parquet
df = spark.read.format("parquet").load("Files/bronze/data.parquet")

# Delta table
df = spark.read.table("my_delta_table")

# SQL endpoint
df = spark.sql("SELECT * FROM lakehouse.my_table")
```

### Writing Delta Tables

```python
# Overwrite
df.write.format("delta").mode("overwrite").saveAsTable("silver_customers")

# Overwrite with partitioning
df.write.format("delta").mode("overwrite").partitionBy("year", "month").saveAsTable("silver_transactions")

# Append
df.write.format("delta").mode("append").saveAsTable("silver_events")
```

### CRUD Operations

```sql
-- UPDATE
UPDATE silver_customers SET status = 'inactive' WHERE last_order_date < '2023-01-01';

-- DELETE
DELETE FROM silver_customers WHERE customer_id IN (SELECT id FROM deleted_accounts);

-- MERGE (upsert)
MERGE INTO silver_customers AS target
USING new_customers AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

### Schema Definition

```python
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, DecimalType

schema = StructType([
    StructField("customer_id", StringType(), False),
    StructField("name", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("amount", DecimalType(18, 2), True),
    StructField("created_at", TimestampType(), True)
])

df = spark.read.format("csv").option("header", "true").schema(schema).load("Files/bronze/customers.csv")
```

### SQL Magic in Notebooks

```python
%%sql
SELECT category, COUNT(*) as count, SUM(amount) as total
FROM silver_transactions
GROUP BY category
ORDER BY total DESC
```

### V-Order Optimization

```python
spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
df.write.format("delta").mode("overwrite").option("vorder", "true").saveAsTable("optimized_table")
```

### Table Optimization

```python
%%sql
-- Compact files and apply Z-ordering
OPTIMIZE silver_transactions ZORDER BY (customer_id, transaction_date);

-- Remove old file versions (7-day retention)
VACUUM silver_transactions RETAIN 168 HOURS;
```

### Incremental Load Pattern

```python
# Read watermark
watermark_df = spark.sql("SELECT MAX(updated_at) as last_load FROM control.watermarks WHERE table_name = 'silver_customers'")
last_load = watermark_df.collect()[0]["last_load"]

# Load only new records
new_records = spark.read.table("bronze_customers").filter(f"updated_at > '{last_load}'")

# Upsert into silver
new_records.createOrReplaceTempView("new_records")
spark.sql("""
    MERGE INTO silver_customers AS target
    USING new_records AS source
    ON target.customer_id = source.customer_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

# Update watermark
spark.sql(f"UPDATE control.watermarks SET last_load = NOW() WHERE table_name = 'silver_customers'")
```

### SCD Type 2 Pattern

```python
spark.sql("""
    MERGE INTO dim_customers AS target
    USING (
        SELECT *, current_timestamp() AS effective_date FROM staged_customers
    ) AS source
    ON target.customer_id = source.customer_id AND target.is_current = true
    WHEN MATCHED AND (target.name <> source.name OR target.address <> source.address) THEN
        UPDATE SET is_current = false, end_date = current_timestamp()
    WHEN NOT MATCHED THEN
        INSERT (customer_id, name, address, start_date, end_date, is_current)
        VALUES (source.customer_id, source.name, source.address, source.effective_date, null, true)
""")
```
