# Natural Language to SQL with Vanna.ai + Qdrant
This project demonstrates how to combine **Vanna.ai** and **Qdrant** to convert natural language user queries into executable SQL statements.
- **Vanna.ai**: Translates user questions into SQL using large language models and schema awareness.
- **Qdrant**: Serves as the vector database to store embeddings of database schema, documentation, and example queries for fast semantic retrieval.

## 🔑 Features
- Query any SQL database using plain English (or other languages).
- Automatic SQL generation with context from schema + examples.
- Vector search with Qdrant for relevant schema and query retrieval.
- Pluggable architecture: bring your own database, schema, and knowledge base.

## 🚀 Use Cases
- **Data teams**: Self-service analytics without writing SQL.
- **Business intelligence**: Fast ad-hoc reporting.
- **Developers**: Embed natural language query capability into apps.

## 🛠️ Tech Stack
- **Vanna.ai** – Natural language → SQL generation.
- **Qdrant** – Vector embeddings & semantic retrieval.
- **Python** – Core orchestration.
- **SQLAlchemy (optional)** – Database connectivity.

## 📂 Project Structure
.
├── data/
│   ├── ddl/          # Extracted DDL statements
│   ├── docs/         # Business documentation
│   ├── examples/     # Question-SQL training examples
│   └── general/      # General documentation
├── train_from_files.py   # Training script
├── extract_ddl.py        # SQL Server DDL extractor
└── README.md

## ⚙️ Setup
1) Clone the repository: `git clone https://github.com/your-org/your-repo.git` then `cd your-repo`
2) Create a virtual environment: `python -m venv .venv` then `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
3) Install requirements: `pip install -r requirements.txt` or `pip install PyPDF2 pyodbc python-dotenv requests`
4) Create `.env` with: `SQLSERVER_HOST=your-sql-server-host`, `SQLSERVER_DB=your-database`, `SQLSERVER_USER=your-username`, `SQLSERVER_PASSWORD=your-password`

## 📑 Scripts
### `extract_ddl.py`
- Connects to your **SQL Server** database and extracts schema definitions (tables, views, primary/foreign keys, indexes, stored procedures) into `data/ddl/`.
- Run: `python extract_ddl.py`
- Generates: `01_tables.sql`, `02_primary_keys.sql`, `03_foreign_keys.sql`, `04_views.sql`, `05_indexes.sql`, `06_stored_procedures.sql`, plus `00_schema_summary.sql`

### `train_from_files.py`
- Loads data from `data/` and trains the **Vanna.ai** service (default `http://localhost:5000`).
- Run: `python train_from_files.py`
- Steps performed: (1) Auto-training from database schema, (2) Train from **DDL** (`data/ddl/`), (3) Train from **documentation** (`data/docs/` + `data/general/`), (4) Train from **examples** (`data/examples/` with question → SQL pairs)
- Example pairs:
  - Q: How many customers do we have? → SQL: `SELECT COUNT(*) FROM customers;`
  - Q: What is the total revenue for this year? → SQL: `SELECT SUM(total_amount) FROM orders WHERE YEAR(order_date)=YEAR(GETDATE());`

## 📝 Example Workflow
1) Run `python extract_ddl.py`
2) Add business docs and training examples under `data/`
3) Run `python train_from_files.py`
4) Query your database via **Vanna.ai** using natural language

## ✅ Next Steps
- Connect **Qdrant** to store embeddings for semantic retrieval
- Extend examples in `data/examples/` with more real-world queries
- Deploy as a microservice for analytics or BI tools

## 📜 License
MIT License. See `LICENSE` for details.
