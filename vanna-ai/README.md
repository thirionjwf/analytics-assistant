# Vanna AI Flask Application

A Flask web application powered by Vanna AI that enables natural language querying of SQL Server databases using OpenAI's language models.

## Features

- Natural language to SQL conversion
- SQL Server integration with both Windows Authentication and SQL Server Authentication
- OpenAI GPT integration for intelligent query generation
- Web-based interface for querying databases
- Training endpoints for customizing the AI model
- Multiple deployment options: Docker containerized or direct Python execution
- SSL certificate bypass for corporate environments

## Prerequisites

- Python 3.8+ (for direct execution) OR Docker and Docker Compose (for containerized deployment)
- OpenAI API key
- Access to a SQL Server database
- For direct execution: SQL Server with Windows Authentication
- For Docker deployment: SQL Server with SQL Server Authentication (sa account or dedicated user)

## Setup

### 1. Environment Configuration

Copy the `.env.template` file to `.env` and configure your settings:

```bash
cp .env.template .env
```

Edit the `.env` file with your configuration:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# SQL Server Connection
SQLSERVER_HOST=your-sql-server-host
SQLSERVER_DB=your-database-name

# SQL Server Authentication (required for Docker deployment)
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=your_sql_server_password

# SSL Configuration for corporate environments
# Set to false to disable SSL verification (useful for corporate proxies)
SSL_VERIFY=false
```

**Environment Variables Explained:**

- `OPENAI_API_KEY`: Your OpenAI API key for GPT integration
- `SQLSERVER_HOST`: SQL Server instance hostname (e.g., `localhost`, `server.domain.com`)
- `SQLSERVER_DB`: Target database name
- `SQLSERVER_USER`: SQL Server username (required for Docker, ignored for direct execution with Windows Auth)
- `SQLSERVER_PASSWORD`: SQL Server password (required for Docker, ignored for direct execution with Windows Auth)
- `SSL_VERIFY`: Set to `false` to bypass SSL certificate verification in corporate environments

### 2. Build the Application

Build the Docker image:

```bash
docker-compose build
```

This will:
- Install Python dependencies
- Install Microsoft ODBC Driver 17 for SQL Server
- Set up the Flask application environment

## Running the Application

You can run the Vanna AI application in two ways, depending on your environment and authentication requirements:

### Method 1: Direct Execution (Windows Authentication)

**Best for:** Local development on Windows machines with direct SQL Server access and Windows Authentication.

**Prerequisites:**
- Python 3.8+ installed locally
- Direct access to SQL Server with Windows Authentication
- All Python dependencies installed

**Steps:**

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   - Ensure your `.env` file is configured with proper SQL Server connection details
   - Windows Authentication will be used automatically (no SQLSERVER_USER/SQLSERVER_PASSWORD needed)

3. **Run the Application:**
   ```bash
   python app.py
   ```

4. **Access the Application:**
   - Open your browser to `http://localhost:5000`

**Advantages:**
- Uses Windows Authentication (more secure in domain environments)
- No Docker overhead
- Direct database access
- Easier debugging and development

### Method 2: Docker Deployment (SQL Server Authentication)

**Best for:** Production deployments, team environments, or when Windows Authentication is not available.

**Prerequisites:**
- Docker and Docker Compose installed
- SQL Server with SQL Server Authentication enabled
- Valid SQL Server username and password

**Steps:**

1. **Configure SQL Server Authentication:**
   - Ensure your `.env` file includes `SQLSERVER_USER` and `SQLSERVER_PASSWORD`
   - Verify the SQL Server user has appropriate database permissions

2. **Build the Docker Image:**
   ```bash
   docker-compose build
   ```

3. **Start the Service:**
   ```bash
   docker-compose up
   ```

   Or run in detached mode:
   ```bash
   docker-compose up -d
   ```

4. **Access the Application:**
   - Open your browser to `http://localhost:5000`

5. **Stop the Service:**
   ```bash
   docker-compose down
   ```

**Advantages:**
- Consistent environment across different machines
- Easy deployment and scaling
- Includes all system dependencies (ODBC drivers, etc.)
- Better for production and team environments

### Choosing the Right Method

| Scenario | Recommended Method |
|----------|-------------------|
| Local development on Windows | Direct Execution |
| Production deployment | Docker |
| Team development | Docker |
| Windows domain environment | Direct Execution |
| Linux/Mac development | Docker |
| CI/CD pipelines | Docker |

## Training the AI Model

Before using the application for queries, you need to train the AI model with your database schema and business context.

### 1. Auto-Train from Database Schema (Recommended First Step)

This automatically extracts your database schema and trains the model:

```bash
curl -X POST http://localhost:5000/train/auto
```

### 2. Add DDL Statements

Train with specific table definitions:

```bash
curl -X POST http://localhost:5000/train/ddl \
  -H "Content-Type: application/json" \
  -d '{
    "ddl": "CREATE TABLE customers (
      customer_id INT PRIMARY KEY,
      customer_name VARCHAR(100),
      email VARCHAR(100),
      created_date DATE
    )"
  }'
```

### 3. Add Business Documentation

Provide business context and terminology:

```bash
curl -X POST http://localhost:5000/train/documentation \
  -H "Content-Type: application/json" \
  -d '{
    "documentation": "OTIF score represents On Time In Full delivery percentage. It measures the percentage of orders delivered both on time and complete."
  }'
```

### 4. Add Question-SQL Examples

Train with example questions and their corresponding SQL queries:

```bash
curl -X POST http://localhost:5000/train/question-sql \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many customers do we have?",
    "sql": "SELECT COUNT(*) FROM customers"
  }'
```

## Usage

1. **Start the application:**
   - **Docker:** `docker-compose up`
   - **Direct:** `python app.py`

2. **Train the model:**
   - **API method:** `curl -X POST http://localhost:5000/train/auto`
   - **File method:** `python train_from_files.py`

3. **Access the web interface** at `http://localhost:5000`

4. **Ask natural language questions** about your data

## File-Based Training (Alternative Method)

In addition to the API-based training above, you can use the included `train_from_files.py` script to automatically train from files in the `data/` directory structure.

### Supported File Types

The training script supports:
- **SQL files** (`.sql`) - Database schema, DDL statements
- **PDF files** (`.pdf`) - Documentation, manuals
- **Text files** (`.txt`) - Plain text documentation
- **Markdown files** (`.md`) - Formatted documentation

### Directory Structure for File Training

```
data/
├── ddl/          # Database schema and DDL files (.sql, .txt, .md)
├── docs/         # General documentation (.pdf, .txt, .md, .sql)
├── examples/     # Question-SQL example pairs (.txt, .md)
└── general/      # Additional documentation (.pdf, .txt, .md, .sql)
```

### Running File-Based Training

**For Direct Execution:**
```bash
python train_from_files.py
```

**For Docker Deployment:**
```bash
# Copy files to container and run training
docker-compose exec vanna-ai python train_from_files.py
```

The script will:
1. Auto-train from your database schema
2. Process all files in the `data/` directory structure
3. Provide detailed progress output
4. Show a summary of training results

### Adding Training Files

Simply place your files in the appropriate `data/` subdirectories:

- **DDL/Schema files** → `data/ddl/` (great for `.sql` files exported from your database)
- **Business documentation** → `data/docs/` or `data/general/`
- **Example Q&A pairs** → `data/examples/`

The script automatically detects file types and processes them accordingly.

## Training Strategy

For best results, follow this training sequence:

1. **Auto-train from schema** - Gets basic table structure
2. **Add key DDL statements** - For important tables with relationships
3. **Add business documentation** - Define domain-specific terms
4. **Add example Q&A pairs** - Show the AI how to answer common questions

## Troubleshooting

## Troubleshooting

### Common Issues by Deployment Method

#### Docker Deployment Issues

**Container fails to start with ODBC errors:**
- Ensure your `.env` file has correct `SQLSERVER_USER` and `SQLSERVER_PASSWORD`
- Verify your SQL Server is accessible from the container network
- Check that SQL Server Authentication is enabled on your database server
- Ensure the SQL Server user has proper permissions

**Database connection fails:**
- Verify SQL Server is configured to accept SQL Server Authentication
- Check firewall settings allow connections on SQL Server port (usually 1433)
- Ensure the SQL Server service is running and accessible

#### Direct Execution Issues

**Python import errors:**
- Install dependencies: `pip install -r requirements.txt`
- Ensure you're using Python 3.8 or higher
- Consider using a virtual environment

**Windows Authentication fails:**
- Verify you're logged into the Windows domain
- Check that your Windows account has SQL Server permissions
- Ensure SQL Server is configured for Windows Authentication
- Verify the SQL Server service is running under proper domain context

#### General Issues

**SSL Certificate errors (Corporate environments):**
- Set `SSL_VERIFY=false` in your `.env` file
- This is common in corporate environments with proxy servers
- The application includes comprehensive SSL bypass mechanisms

**Training fails:**
- Verify your database connection is working first
- Ensure the database user has read permissions on `INFORMATION_SCHEMA` views
- Check that your OpenAI API key is valid and has sufficient credits
- For corporate networks, ensure `SSL_VERIFY=false` is set

**Web interface not accessible:**
- **For Docker:** Confirm the container is running: `docker-compose ps`
- **For Direct:** Check if Python process is running: `python app.py`
- Verify port 5000 is not being used by another service
- Check the application logs for errors

### Viewing Logs

#### Docker Deployment
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs vanna-ai
```

#### Direct Execution
- Logs are displayed directly in the terminal where you ran `python app.py`
- Enable debug mode by setting `debug=True` in the `app.run()` call

### Rebuilding/Restarting

#### Docker Deployment
```bash
# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up
```

#### Direct Execution
- Simply stop the Python process (Ctrl+C) and restart: `python app.py`

## Development

### File Structure

```
analytics-assistant/
├── app.py                     # Main Flask application
├── train_from_files.py        # Training data loader (supports PDF, TXT, MD, SQL files)
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Service orchestration
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (create from .env.template)
├── .env.template             # Environment template
├── data/                     # Training data directory
│   ├── ddl/                  # Database schema files (SQL)
│   ├── docs/                 # Documentation files (PDF, TXT, MD)
│   ├── examples/             # Question-SQL example pairs
│   └── general/              # General documentation
├── vanna-ai/                 # Documentation directory
│   └── README.md             # This file
└── chroma_db/                # ChromaDB vector database (created automatically)
```

### Extending the Application

You can extend the application by:
- Adding new training endpoints in `app.py`
- Customizing the Vanna AI configuration
- Adding authentication and authorization
- Implementing data visualization features

## Security Considerations

### General Security
- Keep your `.env` file secure and never commit it to version control
- Use strong API keys and rotate them regularly
- Implement proper authentication for production deployments
- Limit database permissions to read-only for the Vanna AI user

### Authentication Method Security

**Windows Authentication (Direct Execution):**
- More secure in domain environments as it uses existing Windows credentials
- No passwords stored in configuration files
- Relies on Windows domain security policies
- Best for internal corporate deployments

**SQL Server Authentication (Docker Deployment):**
- Requires storing database credentials in environment variables
- Use strong, unique passwords for the SQL Server user account
- Consider using dedicated service accounts with minimal required permissions
- Regularly rotate database passwords
- Ensure `.env` file permissions are restricted (not readable by other users)

### Network Security
- In corporate environments, SSL certificate verification is disabled (`SSL_VERIFY=false`)
- This is necessary for OpenAI API access through corporate proxies
- Consider implementing additional network security measures for production deployments
- Use firewalls to restrict database access to only the application server

### Database Security
- Create a dedicated database user for Vanna AI with minimal required permissions
- Grant only `SELECT` permissions on necessary tables and views
- Grant `SELECT` permissions on `INFORMATION_SCHEMA` views for auto-training
- Avoid using `sa` account in production environments
- Regularly audit database access logs

## License

This project is provided as-is for educational and development purposes.
