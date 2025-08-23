#!/usr/bin/env python3
"""
Training Data Loader for Vanna AI

This script loads training data from PDF and TXT files in the data directory
and trains the Vanna AI model with the content.

Usage:
    python train_from_files.py

Requirements:
    pip install PyPDF2 python-dotenv requests

Directory structure:
    data/
    ├── ddl/          # DDL statements (CREATE TABLE, etc.)
    ├── docs/         # Documentation files
    ├── examples/     # Question-SQL examples
    └── general/      # General documentation
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VannaTrainer:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.data_dir = Path("data")
        
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""
    
    def read_text_file(self, file_path: Path) -> str:
        """Read content from a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return ""
    
    def extract_file_content(self, file_path: Path) -> str:
        """Extract content from PDF, TXT, MD, or SQL file."""
        if file_path.suffix.lower() == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md', '.sql']:
            return self.read_text_file(file_path)
        else:
            print(f"Unsupported file type: {file_path}")
            return ""
    
    def train_documentation(self, content: str, filename: str) -> bool:
        """Send documentation to Vanna for training with verbose output."""
        print(f"[DEBUG] Sending documentation from {filename} to {self.base_url}/train/documentation")
        print(f"[DEBUG] Content (first 200 chars): {content[:200]!r}")
        try:
            response = requests.post(
                f"{self.base_url}/train/documentation",
                json={"documentation": content},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text[:500]}")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print(f"✓ Successfully trained documentation from {filename}")
                    return True
                else:
                    print(f"✗ Failed to train {filename}: {result.get('message')}")
                    return False
            else:
                print(f"✗ HTTP error {response.status_code} for {filename}")
                return False
        except Exception as e:
            print(f"✗ Error training {filename}: {e}")
            return False
    
    def train_ddl(self, content: str, filename: str) -> bool:
        """Send DDL statements to Vanna for training with verbose output."""
        print(f"[DEBUG] Sending DDL from {filename} to {self.base_url}/train/ddl")
        print(f"[DEBUG] Content (first 200 chars): {content[:200]!r}")
        try:
            response = requests.post(
                f"{self.base_url}/train/ddl",
                json={"ddl": content},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text[:500]}")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print(f"✓ Successfully trained DDL from {filename}")
                    return True
                else:
                    print(f"✗ Failed to train DDL {filename}: {result.get('message')}")
                    return False
            else:
                print(f"✗ HTTP error {response.status_code} for {filename}")
                return False
        except Exception as e:
            print(f"✗ Error training DDL {filename}: {e}")
            return False
    
    def parse_example_file(self, content: str) -> List[Dict[str, str]]:
        """
        Parse example files containing question-SQL pairs.
        Expected format:
        Q: Question here?
        SQL: SELECT * FROM table;
        
        Q: Another question?
        SQL: SELECT COUNT(*) FROM table;
        """
        examples = []
        lines = content.split('\n')
        current_question = None
        current_sql = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Q:'):
                current_question = line[2:].strip()
            elif line.startswith('SQL:'):
                current_sql = line[4:].strip()
                if current_question and current_sql:
                    examples.append({
                        "question": current_question,
                        "sql": current_sql
                    })
                    current_question = None
                    current_sql = None
        
        return examples
    
    def train_examples(self, content: str, filename: str) -> bool:
        """Train question-SQL examples with verbose output."""
        examples = self.parse_example_file(content)
        success_count = 0
        print(f"[DEBUG] Found {len(examples)} examples in {filename}")
        for i, example in enumerate(examples, 1):
            print(f"[DEBUG] Sending example {i}: {example}")
            try:
                response = requests.post(
                    f"{self.base_url}/train/question-sql",
                    json=example,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Response text: {response.text[:500]}")
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        print(f"✓ Successfully trained example {i} from {filename}")
                        success_count += 1
                    else:
                        print(f"✗ Failed to train example {i} from {filename}: {result.get('message')}")
                else:
                    print(f"✗ HTTP error {response.status_code} for example {i} from {filename}")
            except Exception as e:
                print(f"✗ Error training example {i} from {filename}: {e}")
        print(f"📊 Trained {success_count}/{len(examples)} examples from {filename}")
        return success_count > 0
    
    def auto_train(self) -> bool:
        """Trigger auto-training from database schema with verbose output."""
        print(f"[DEBUG] Sending auto-training request to {self.base_url}/train/auto")
        try:
            response = requests.post(f"{self.base_url}/train/auto", timeout=60)
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text[:500]}")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print("✓ Successfully completed auto-training from database schema")
                    return True
                else:
                    print(f"✗ Auto-training failed: {result.get('message')}")
                    return False
            else:
                print(f"✗ HTTP error {response.status_code} during auto-training")
                return False
        except Exception as e:
            print(f"✗ Error during auto-training: {e}")
            return False
    
    def process_directory(self, dir_path: Path, training_type: str) -> int:
        """Process all files in a directory for a specific training type."""
        if not dir_path.exists():
            print(f"📁 Directory {dir_path} does not exist, skipping...")
            return 0
        
        print(f"\n📁 Processing {training_type} files in {dir_path}")
        success_count = 0
        
        # Process PDF, TXT, MD, and SQL files
        file_patterns = ['*.pdf', '*.txt', '*.md', '*.sql']
        files = []
        for pattern in file_patterns:
            files.extend(dir_path.glob(pattern))
        
        if not files:
            print(f"   No files found in {dir_path}")
            return 0
        
        for file_path in files:
            print(f"📄 Processing {file_path.name}...")
            content = self.extract_file_content(file_path)
            
            if not content:
                print(f"   Skipping {file_path.name} (no content extracted)")
                continue
            
            # Train based on directory type
            if training_type == "ddl":
                success = self.train_ddl(content, file_path.name)
            elif training_type == "examples":
                success = self.train_examples(content, file_path.name)
            else:  # documentation
                success = self.train_documentation(content, file_path.name)
            
            if success:
                success_count += 1
        
        return success_count
    
    def run_training(self):
        """Run the complete training process."""
        print("🚀 Starting Vanna AI training from files...")
        print("=" * 50)
        
        # Check if data directory exists
        if not self.data_dir.exists():
            print(f"❌ Data directory '{self.data_dir}' not found!")
            print("Please create the data directory with subdirectories:")
            print("  data/ddl/       - DDL statements")
            print("  data/docs/      - Documentation files")
            print("  data/examples/  - Question-SQL examples")
            print("  data/general/   - General documentation")
            return
        
        total_success = 0
        
        # 1. Auto-train from database schema first
        print("\n🔧 Step 1: Auto-training from database schema")
        if self.auto_train():
            total_success += 1
        
        # 2. Train DDL statements
        ddl_success = self.process_directory(
            self.data_dir / "ddl", 
            "ddl"
        )
        total_success += ddl_success
        
        # 3. Train documentation
        docs_success = self.process_directory(
            self.data_dir / "docs", 
            "documentation"
        )
        total_success += docs_success
        
        # 4. Train general documentation
        general_success = self.process_directory(
            self.data_dir / "general", 
            "documentation"
        )
        total_success += general_success
        
        # 5. Train examples
        examples_success = self.process_directory(
            self.data_dir / "examples", 
            "examples"
        )
        total_success += examples_success
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Training Summary:")
        print(f"   Auto-training: {'✓' if total_success > 0 else '✗'}")
        print(f"   DDL files: {ddl_success} trained")
        print(f"   Documentation files: {docs_success + general_success} trained")
        print(f"   Example files: {examples_success} trained")
        print(f"   Total successful operations: {total_success}")
        
        if total_success > 0:
            print("\n🎉 Training completed! Your Vanna AI model has been updated.")
        else:
            print("\n⚠️  No training data was successfully processed.")

def main():
    """Main function to run the training."""
    print("Vanna AI Training Data Loader")
    print("============================")
    
    # Check if Vanna service is running
    trainer = VannaTrainer()
    try:
        response = requests.get(f"{trainer.base_url}")
        print(f"✓ Vanna AI service is running at {trainer.base_url}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Vanna AI service at {trainer.base_url}")
        print("Please make sure the service is running:")
        print("  docker-compose up   # or")
        print("  python app.py")
        return
    
    # Create example data structure if it doesn't exist
    data_dir = Path("data")
    subdirs = ["ddl", "docs", "examples", "general"]
    
    for subdir in subdirs:
        (data_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    if not any((data_dir / subdir).glob("*") for subdir in subdirs):
        print("\n📝 Creating example files...")
        
        # Create example DDL file
        (data_dir / "ddl" / "example_tables.sql").write_text("""
-- Example table definitions
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    created_date DATE DEFAULT GETDATE()
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT FOREIGN KEY REFERENCES customers(customer_id),
    order_date DATE DEFAULT GETDATE(),
    total_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending'
);
""")
        
        # Create example documentation
        (data_dir / "docs" / "business_terms.txt").write_text("""
Business Terminology:

OTIF Score: On Time In Full delivery percentage. Measures orders delivered both on time and complete.

Customer Lifetime Value (CLV): Total revenue expected from a customer over their entire relationship.

Churn Rate: Percentage of customers who stop doing business with us in a given period.

Average Order Value (AOV): Average monetary value of orders placed by customers.
""")
        
        # Create example question-SQL pairs
        (data_dir / "examples" / "common_queries.txt").write_text("""
Q: How many customers do we have?
SQL: SELECT COUNT(*) FROM customers;

Q: What is the total revenue for this year?
SQL: SELECT SUM(total_amount) FROM orders WHERE YEAR(order_date) = YEAR(GETDATE());

Q: Who are our top 5 customers by order value?
SQL: SELECT TOP 5 c.customer_name, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_name ORDER BY total_spent DESC;

Q: What is the average order value?
SQL: SELECT AVG(total_amount) FROM orders;
""")
        
        print("✓ Created example training files in data/ directory")
        print("  You can modify these files or add your own content.")
    
    # Run the training
    trainer.run_training()

if __name__ == "__main__":
    main()
