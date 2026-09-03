# 🤖 DATA_AGENT: Multi-Agent Orchestrated Data Platform

An autonomous, multi-agent AI data engineering system built with **LangGraph**, **LangChain**, **PostgreSQL**, and **Pandas**. 

DATA_AGENT dynamically routes natural language queries to specialized sub-agent graphs for **Text-to-SQL execution with safety guardrails** and **automated ETL pipeline execution**.

---

## 🌟 Key Features

- **Master Router Graph:** Uses Pydantic structured output classification to dynamically route requests between ETL and SQL agents.
- **SQL Analyst Sub-Graph (Text-to-SQL):**
  - **Dynamic Schema Inspection:** Fetches live database table definitions, column types, and sample records.
  - **🛡️ Security Judge Node:** Evaluates query safety via structured output to block destructive actions (`DROP`, `DELETE`, `UPDATE`, `TRUNCATE`).
- **ETL Analyst Sub-Graph:**
  - **API Data Extraction:** Autonomous JSON payload extraction and normalization into CSV, JSON, or Parquet.
  - **Dynamic Transformation:** Previews dataset schemas and generates context-aware Pandas code for automated transformations.

---

## 📐 Architecture Overview

### 1. Master Router Architecture
![Master Graph](data_agent_graph.png)

### 2. SQL Analyst Sub-Graph
![SQL Analyst Graph](sql_analyst_graph.png)

### 3. ETL Analyst Sub-Graph
![ETL Analyst Graph](etl_analyst_graph.png)

---

## 🛠️ Tech Stack

- **Frameworks:** LangGraph, LangChain
- **Validation & Schemas:** Pydantic
- **Data Engine:** Pandas, PostgreSQL
- **Language:** Python 3.13
- **Package Management:** uv
