---
name: fabric-lakehouse
description: Use this skill to get context about Fabric Lakehouse and its features for software systems and AI-powered functions. It offers descriptions of Lakehouse data components, organization with schemas and shortcuts, access control, and code examples. This skill supports users in designing, building, and optimizing Lakehouse solutions using best practices.
metadata:
  author: tedvilutis
  version: 1.0
---

## When to Use This Skill

Use this skill when you need to:
- Generate a document or explanation that includes definition and context about Fabric Lakehouse and its capabilities
- Design, build, and optimize Lakehouse solutions using best practices
- Understand the core concepts and components of a Lakehouse in Microsoft Fabric
- Learn how to manage tabular and non-tabular data within a Lakehouse

## Fabric Lakehouse

### Core Concepts

**What is a Lakehouse?**

"Lakehouse in Microsoft Fabric is an item that gives users a place to store their tabular data (like tables) and non-tabular data (like files)." It provides unified storage in OneLake, Delta Lake format with ACID transactions, SQL analytics endpoints, semantic models for Power BI, and support for multiple file formats.

**Key Components:**
- Delta Tables (managed tables with ACID compliance)
- Files (unstructured/semi-structured data)
- SQL Endpoint (auto-generated read-only interface)
- Shortcuts (virtual links to external/internal data)
- Fabric Materialized Views (pre-computed tables)

**Tabular Data:** Stored under "Tables" folder primarily in Delta format; can also use CSV or Parquet (Spark-only); can be internal or external.

**Schemas:** Organize Lakehouse tables as folders under "Tables"; default "dbo" schema cannot be deleted; users can create, rename, or delete others. Schema Shortcuts reference tables across lakehouses.

**Files:** Stored under "Files" folder with customizable folder structures; supports any file format.

**Fabric Materialized Views:** Pre-computed tables automatically updated on schedule for fast query performance on complex aggregations and joins.

**Spark Views:** Logical tables defined by SQL queries that don't store data but provide virtual query layers.

### Security

**Item Access/Control Plane Security:** Workspace roles (Admin, Member, Contributor, Viewer) control Lakehouse access; sharing capabilities available.

**Data Access/OneLake Security:** Based on Microsoft Entra ID and role-based access control; supports column-level and row-level security for tables.

### Lakehouse Shortcuts

Virtual links to data without copying. Types include:
- Internal (other Fabric Lakehouses/tables)
- ADLS Gen2 (Azure containers)
- Amazon S3 (AWS buckets)
- Dataverse (Microsoft Dataverse)
- Google Cloud Storage (GCS buckets)

### Performance Optimization

**V-Order Optimization:** Enable on Delta tables for faster semantic model reads through data presort optimization.

**Table Optimization:** Use OPTIMIZE command to compact files and apply Z-ordering; Vacuum cleans old files and frees storage.

### Lineage

"The Lakehouse item supports lineage, which allows users to track the origin and transformations of data." Information is automatically captured for tables and files.

### Additional Resources

See referenced files for PySpark code examples and data ingestion methods.
