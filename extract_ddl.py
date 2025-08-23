#!/usr/bin/env python3
"""
Database DDL Extractor for Vanna AI Training

This script connects to your SQL Server database, extracts DDL (Data Definition Language)
statements for all tables, views, and stored procedures, and saves them to the data/ddl directory.

Usage:
    python extract_ddl.py

Requirements:
    pip install pyodbc python-dotenv

The script will create separate files for:
- Tables (with columns, data types, constraints)
- Views 
- Stored procedures
- Foreign key relationships
- Indexes
"""

import os
import pyodbc
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DDLExtractor:
    def __init__(self):
        self.ddl_dir = Path("data/ddl")
        self.ddl_dir.mkdir(parents=True, exist_ok=True)
        
        # Database connection details
        self.host = os.environ.get("SQLSERVER_HOST")
        self.database = os.environ.get("SQLSERVER_DB")
        self.user = os.environ.get("SQLSERVER_USER")
        self.password = os.environ.get("SQLSERVER_PASSWORD")
        
        # Auto-detect if running in Docker container
        self.is_docker = os.path.exists('/.dockerenv')
        
        if self.is_docker:
            print("Running in Docker - using SQL Server authentication")
            self.conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.host};DATABASE={self.database};UID={self.user};PWD={self.password}"
        else:
            print("Running on Windows - using Windows authentication")
            self.conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.host};DATABASE={self.database};Trusted_Connection=yes"
    
    def connect_to_database(self):
        """Establish connection to the database."""
        try:
            self.conn = pyodbc.connect(self.conn_str)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database: {self.database}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def extract_table_ddl(self):
        """Extract DDL for all tables."""
        print("\n📋 Extracting table definitions...")
        
        # Query to get table information
        table_query = """
        SELECT 
            t.TABLE_SCHEMA,
            t.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT,
            c.ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.TABLES t
        INNER JOIN INFORMATION_SCHEMA.COLUMNS c 
            ON t.TABLE_NAME = c.TABLE_NAME 
            AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
        WHERE t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
        """
        
        self.cursor.execute(table_query)
        results = self.cursor.fetchall()
        
        tables = {}
        for row in results:
            schema, table_name, col_name, data_type, char_len, num_prec, num_scale, nullable, default, pos = row
            
            full_table_name = f"{schema}.{table_name}"
            if full_table_name not in tables:
                tables[full_table_name] = []
            
            # Build column definition
            col_def = f"    {col_name} {data_type.upper()}"
            
            # Add length/precision
            if data_type.upper() in ['VARCHAR', 'NVARCHAR', 'CHAR', 'NCHAR'] and char_len:
                if char_len == -1:
                    col_def += "(MAX)"
                else:
                    col_def += f"({char_len})"
            elif data_type.upper() in ['DECIMAL', 'NUMERIC'] and num_prec:
                if num_scale:
                    col_def += f"({num_prec},{num_scale})"
                else:
                    col_def += f"({num_prec})"
            
            # Add nullable
            if nullable == 'NO':
                col_def += " NOT NULL"
            
            # Add default
            if default:
                col_def += f" DEFAULT {default}"
            
            tables[full_table_name].append(col_def)
        
        # Generate CREATE TABLE statements
        ddl_content = "-- Table Definitions\n-- Generated automatically from database schema\n\n"
        
        for table_name, columns in tables.items():
            ddl_content += f"CREATE TABLE {table_name} (\n"
            ddl_content += ",\n".join(columns)
            ddl_content += "\n);\n\n"
        
        # Save to file
        table_file = self.ddl_dir / "01_tables.sql"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
        
        print(f"✓ Saved {len(tables)} table definitions to {table_file}")
        return len(tables)
    
    def extract_primary_keys(self):
        """Extract primary key constraints."""
        print("\n🔑 Extracting primary keys...")
        
        pk_query = """
        SELECT 
            tc.TABLE_SCHEMA,
            tc.TABLE_NAME,
            tc.CONSTRAINT_NAME,
            STRING_AGG(kcu.COLUMN_NAME, ', ') WITHIN GROUP (ORDER BY kcu.ORDINAL_POSITION) as COLUMNS
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
            AND tc.TABLE_NAME = kcu.TABLE_NAME
        WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        GROUP BY tc.TABLE_SCHEMA, tc.TABLE_NAME, tc.CONSTRAINT_NAME
        ORDER BY tc.TABLE_SCHEMA, tc.TABLE_NAME
        """
        
        self.cursor.execute(pk_query)
        results = self.cursor.fetchall()
        
        ddl_content = "-- Primary Key Constraints\n-- Generated automatically from database schema\n\n"
        
        for row in results:
            schema, table_name, constraint_name, columns = row
            ddl_content += f"ALTER TABLE {schema}.{table_name}\n"
            ddl_content += f"ADD CONSTRAINT {constraint_name} PRIMARY KEY ({columns});\n\n"
        
        # Save to file
        pk_file = self.ddl_dir / "02_primary_keys.sql"
        with open(pk_file, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
        
        print(f"✓ Saved {len(results)} primary key constraints to {pk_file}")
        return len(results)
    
    def extract_foreign_keys(self):
        """Extract foreign key constraints."""
        print("\n🔗 Extracting foreign keys...")
        
        fk_query = """
        SELECT 
            fk.name AS CONSTRAINT_NAME,
            tp.name AS PARENT_TABLE,
            sp.name AS PARENT_SCHEMA,
            cp.name AS PARENT_COLUMN,
            tr.name AS REFERENCED_TABLE,
            sr.name AS REFERENCED_SCHEMA,
            cr.name AS REFERENCED_COLUMN
        FROM sys.foreign_keys fk
        INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
        INNER JOIN sys.schemas sp ON tp.schema_id = sp.schema_id
        INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
        INNER JOIN sys.schemas sr ON tr.schema_id = sr.schema_id
        INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        ORDER BY sp.name, tp.name, fk.name
        """
        
        self.cursor.execute(fk_query)
        results = self.cursor.fetchall()
        
        ddl_content = "-- Foreign Key Constraints\n-- Generated automatically from database schema\n\n"
        
        for row in results:
            constraint_name, parent_table, parent_schema, parent_column, ref_table, ref_schema, ref_column = row
            ddl_content += f"ALTER TABLE {parent_schema}.{parent_table}\n"
            ddl_content += f"ADD CONSTRAINT {constraint_name} FOREIGN KEY ({parent_column})\n"
            ddl_content += f"REFERENCES {ref_schema}.{ref_table}({ref_column});\n\n"
        
        # Save to file
        fk_file = self.ddl_dir / "03_foreign_keys.sql"
        with open(fk_file, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
        
        print(f"✓ Saved {len(results)} foreign key constraints to {fk_file}")
        return len(results)
    
    def extract_views(self):
        """Extract view definitions."""
        print("\n👁️ Extracting views...")
        
        view_query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            VIEW_DEFINITION
        FROM INFORMATION_SCHEMA.VIEWS
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        self.cursor.execute(view_query)
        results = self.cursor.fetchall()
        
        ddl_content = "-- View Definitions\n-- Generated automatically from database schema\n\n"
        
        for row in results:
            schema, view_name, definition = row
            ddl_content += f"CREATE VIEW {schema}.{view_name} AS\n"
            ddl_content += f"{definition};\n\n"
        
        # Save to file
        view_file = self.ddl_dir / "04_views.sql"
        with open(view_file, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
        
        print(f"✓ Saved {len(results)} view definitions to {view_file}")
        return len(results)
    
    def extract_indexes(self):
        """Extract index definitions."""
        print("\n📇 Extracting indexes...")
        
        index_query = """
        SELECT 
            s.name AS schema_name,
            t.name AS table_name,
            i.name AS index_name,
            i.type_desc AS index_type,
            i.is_unique,
            STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columns
        FROM sys.indexes i
        INNER JOIN sys.tables t ON i.object_id = t.object_id
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.type > 0  -- Exclude heaps
        AND i.is_primary_key = 0  -- Exclude primary keys (already handled)
        AND i.is_unique_constraint = 0  -- Exclude unique constraints
        GROUP BY s.name, t.name, i.name, i.type_desc, i.is_unique
        ORDER BY s.name, t.name, i.name
        """
        
        self.cursor.execute(index_query)
        results = self.cursor.fetchall()
        
        ddl_content = "-- Index Definitions\n-- Generated automatically from database schema\n\n"
        
        for row in results:
            schema, table_name, index_name, index_type, is_unique, columns = row
            
            unique_clause = "UNIQUE " if is_unique else ""
            ddl_content += f"CREATE {unique_clause}INDEX {index_name}\n"
            ddl_content += f"ON {schema}.{table_name} ({columns});\n\n"
        
        # Save to file
        index_file = self.ddl_dir / "05_indexes.sql"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
        
        print(f"✓ Saved {len(results)} index definitions to {index_file}")
        return len(results)
    
    def extract_stored_procedures(self):
        """Extract stored procedure definitions."""
        print("\n⚙️ Extracting stored procedures...")
        
        sp_query = """
        SELECT 
            s.name AS schema_name,
            p.name AS procedure_name,
            m.definition
        FROM sys.procedures p
        INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
        INNER JOIN sys.sql_modules m ON p.object_id = m.object_id
        ORDER BY s.name, p.name
        """
        
        self.cursor.execute(sp_query)
        results = self.cursor.fetchall()
        
        ddl_content = "-- Stored Procedure Definitions\n-- Generated automatically from database schema\n\n"
        
        for row in results:
            schema, sp_name, definition = row
            ddl_content += f"-- {schema}.{sp_name}\n"
            ddl_content += f"{definition};\n\n"
        
        # Save to file
        sp_file = self.ddl_dir / "06_stored_procedures.sql"
        with open(sp_file, 'w', encoding='utf-8') as f:
            f.write(ddl_content)
        
        print(f"✓ Saved {len(results)} stored procedure definitions to {sp_file}")
        return len(results)
    
    def create_summary_file(self, counts):
        """Create a summary file with database schema information."""
        summary_content = f"""-- Database Schema Summary
-- Database: {self.database}
-- Server: {self.host}
-- Extracted on: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}

/*
Schema Summary:
- Tables: {counts.get('tables', 0)}
- Primary Keys: {counts.get('primary_keys', 0)}
- Foreign Keys: {counts.get('foreign_keys', 0)}
- Views: {counts.get('views', 0)}
- Indexes: {counts.get('indexes', 0)}
- Stored Procedures: {counts.get('stored_procedures', 0)}

Files Generated:
1. 01_tables.sql - Table definitions with columns and data types
2. 02_primary_keys.sql - Primary key constraints
3. 03_foreign_keys.sql - Foreign key relationships
4. 04_views.sql - View definitions
5. 05_indexes.sql - Index definitions
6. 06_stored_procedures.sql - Stored procedure definitions

Usage for Vanna AI Training:
All these files will be automatically processed when you run:
python train_from_files.py
*/
"""
        
        summary_file = self.ddl_dir / "00_schema_summary.sql"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"✓ Created schema summary: {summary_file}")
    
    def run_extraction(self):
        """Run the complete DDL extraction process."""
        print("🚀 Starting DDL extraction from database...")
        print("=" * 60)
        
        if not self.connect_to_database():
            return
        
        counts = {}
        
        try:
            # Extract all DDL components
            counts['tables'] = self.extract_table_ddl()
            counts['primary_keys'] = self.extract_primary_keys()
            counts['foreign_keys'] = self.extract_foreign_keys()
            counts['views'] = self.extract_views()
            counts['indexes'] = self.extract_indexes()
            counts['stored_procedures'] = self.extract_stored_procedures()
            
            # Create summary
            self.create_summary_file(counts)
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 Extraction Summary:")
            print(f"   Tables: {counts['tables']}")
            print(f"   Primary Keys: {counts['primary_keys']}")
            print(f"   Foreign Keys: {counts['foreign_keys']}")
            print(f"   Views: {counts['views']}")
            print(f"   Indexes: {counts['indexes']}")
            print(f"   Stored Procedures: {counts['stored_procedures']}")
            print(f"\n📁 All DDL files saved to: {self.ddl_dir}")
            print("\n🎉 DDL extraction completed successfully!")
            print("\nNext steps:")
            print("1. Review the generated DDL files in data/ddl/")
            print("2. Run 'python train_from_files.py' to train Vanna AI with this schema")
            
        except Exception as e:
            print(f"❌ Error during extraction: {e}")
        finally:
            self.conn.close()
            print("✓ Database connection closed")

def main():
    """Main function to run the DDL extraction."""
    print("Database DDL Extractor for Vanna AI")
    print("===================================")
    
    extractor = DDLExtractor()
    extractor.run_extraction()

if __name__ == "__main__":
    main()
