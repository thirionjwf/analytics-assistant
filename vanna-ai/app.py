#!/usr/bin/env python3

import os
import ssl
import urllib3
import httpx
import requests
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from vanna.flask import VannaFlaskApp

# Disable SSL warnings completely
urllib3.disable_warnings()
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
SQLSERVER_HOST = os.environ.get("SQLSERVER_HOST")
SQLSERVER_DB = os.environ.get("SQLSERVER_DB")
SQLSERVER_USER = os.environ.get("SQLSERVER_USER")
SQLSERVER_PASSWORD = os.environ.get("SQLSERVER_PASSWORD")

# SSL and Proxy Configuration
SSL_VERIFY = os.environ.get("SSL_VERIFY", "false").lower() == "true"
HTTP_PROXY = os.environ.get("HTTP_PROXY")
HTTPS_PROXY = os.environ.get("HTTPS_PROXY")

print(f"SSL_VERIFY: {SSL_VERIFY}")
print(f"HTTP_PROXY: {HTTP_PROXY}")
print(f"HTTPS_PROXY: {HTTPS_PROXY}")

# Global SSL Context for corporate environments
if not SSL_VERIFY:
    print("🔒 Configuring comprehensive SSL bypass for corporate environment...")
    
    # Set environment variables to disable SSL verification globally
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    
    # Create an unverified SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Apply globally
    ssl._create_default_https_context = lambda: ssl_context
    
    print("✅ SSL context configured with certificate verification disabled")

# Proxy configuration
proxies = {}
if HTTP_PROXY:
    proxies['http'] = HTTP_PROXY
if HTTPS_PROXY:
    proxies['https'] = HTTPS_PROXY

# Monkey patch requests and httpx for comprehensive SSL bypass
if not SSL_VERIFY:
    print("Applying comprehensive SSL bypass...")
    
    # Patch requests globally
    import requests.adapters
    import requests.sessions
    
    # Monkey patch the HTTPAdapter.send method
    original_send = requests.adapters.HTTPAdapter.send
    def patched_send(self, request, **kwargs):
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 30)
        if proxies:
            kwargs.setdefault('proxies', proxies)
        return original_send(self, request, **kwargs)
    requests.adapters.HTTPAdapter.send = patched_send
    
    # Patch requests.request
    original_request = requests.request
    def patched_request(method, url, **kwargs):
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 30)
        if proxies:
            kwargs.setdefault('proxies', proxies)
        return original_request(method, url, **kwargs)
    requests.request = patched_request
    
    # Patch Session.request
    original_session_request = requests.sessions.Session.request
    def patched_session_request(self, method, url, **kwargs):
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 30)
        if proxies:
            kwargs.setdefault('proxies', proxies)
        return original_session_request(self, method, url, **kwargs)
    requests.sessions.Session.request = patched_session_request
    
    # Patch httpx
    original_httpx_request = httpx.request
    def patched_httpx_request(method, url, **kwargs):
        kwargs.setdefault('verify', False)
        kwargs.setdefault('timeout', 30)
        if proxies:
            kwargs.setdefault('proxies', proxies)
        return original_httpx_request(method, url, **kwargs)
    httpx.request = patched_httpx_request
    
    print("✅ Comprehensive SSL bypass applied to requests, sessions, and httpx")

# Auto-detect Docker environment
def is_running_in_docker():
    try:
        return os.path.exists('/.dockerenv')
    except:
        return False

# Database connection configuration
if is_running_in_docker():
    print("Running in Docker - using SQL Server authentication")
    odbc_conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQLSERVER_HOST};DATABASE={SQLSERVER_DB};UID={SQLSERVER_USER};PWD={SQLSERVER_PASSWORD}"
else:
    print("Running on Windows - using Windows authentication")
    odbc_conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQLSERVER_HOST};DATABASE={SQLSERVER_DB};Trusted_Connection=yes"

# Enhanced Vanna class with comprehensive SSL and proxy support
class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        
        # Create custom OpenAI client with SSL bypass and proxy support
        if not SSL_VERIFY:
            print("Configuring OpenAI client with SSL bypass and proxy support...")
            
            import openai
            
            # Build httpx client configuration
            client_config = {
                'verify': False,
                'timeout': 60.0,
                'follow_redirects': True
            }
            
            # Add proxy configuration if available
            if proxies:
                client_config['proxies'] = proxies
            
            # Create custom httpx client
            self._http_client = httpx.Client(**client_config)
            
            # Replace OpenAI client
            self.client = openai.OpenAI(
                api_key=config.get('api_key'),
                http_client=self._http_client
            )
            
            print("✅ OpenAI client configured with comprehensive SSL/proxy bypass")
        else:
            print("Using standard SSL verification")

# Initialize Vanna instance
print("Initializing Vanna with comprehensive SSL/proxy configuration...")

try:
    vn = MyVanna(config={
        'api_key': OPENAI_API_KEY,
        'model': OPENAI_MODEL,
        'path': './chroma_db',
        'collection_name': 'vanna_training_data'
    })
    
    vn.connect_to_mssql(odbc_conn_str=odbc_conn_str)
    print("✅ Vanna initialized successfully")
    
except Exception as e:
    print(f"❌ Failed to initialize Vanna: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Create Flask app
app = VannaFlaskApp(vn)
flask_app = app.flask_app

# Enhanced error handling
@flask_app.errorhandler(500)
def handle_500_error(e):
    import traceback
    error_trace = traceback.format_exc()
    print(f"❌ 500 Error: {error_trace}")
    return {
        "error": "Internal server error",
        "message": "Check server logs for details",
        "ssl_verify": SSL_VERIFY
    }, 500

# Training endpoints
@flask_app.route('/train/auto', methods=['POST'])
def train_auto():
    """Auto-train from database schema"""
    try:
        df_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
        plan = vn.get_training_plan_generic(df_schema)
        vn.train(plan=plan)
        return {"status": "success", "message": "Auto-training completed"}
    except Exception as e:
        print(f"❌ Training error: {e}")
        return {"status": "error", "message": str(e)}

@flask_app.route('/train/ddl', methods=['POST'])
def train_ddl():
    """Train with DDL statement"""
    try:
        from flask import request
        data = request.json
        ddl = data.get('ddl')
        if not ddl:
            return {"status": "error", "message": "DDL statement required"}
        vn.train(ddl=ddl)
        return {"status": "success", "message": "DDL training completed"}
    except Exception as e:
        print(f"❌ DDL training error: {e}")
        return {"status": "error", "message": str(e)}

@flask_app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with SSL and proxy info"""
    return {
        "status": "healthy",
        "ssl_verify": SSL_VERIFY,
        "proxy_configured": bool(proxies),
        "openai_key_configured": bool(OPENAI_API_KEY)
    }

@flask_app.route('/test-openai', methods=['GET'])
def test_openai():
    """Test OpenAI API connectivity"""
    try:
        # Test a simple OpenAI API call
        response = vn.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'SSL test successful'"}],
            max_tokens=10
        )
        
        return {
            "status": "success",
            "response": response.choices[0].message.content,
            "ssl_verify": SSL_VERIFY
        }
    except Exception as e:
        print(f"❌ OpenAI test error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "ssl_verify": SSL_VERIFY
        }, 500

if __name__ == "__main__":
    print(f"🚀 Starting Flask app with SSL_VERIFY={SSL_VERIFY}")
    print(f"🔧 Proxy configuration: {proxies}")
    
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        import traceback
        traceback.print_exc()
