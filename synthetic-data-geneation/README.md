# Synthetic Data Generation API

A sophisticated AI-powered system for generating high-quality synthetic data using LLM models. The system creates realistic data for emails and products with various complexity levels and customizable output formats.

## 🌟 Features

- **Synthetic Email Generation**: Generate realistic email content with varying complexity levels
- **Synthetic Product Generation**: Create product data with descriptions, features, and metadata
- **Multiple Output Formats**: Export data as JSON or CSV
- **Templating System**: Extensible template system for different data types
- **Multi-Interface Support**: 
  - RESTful API endpoints (FastAPI)
  - Command-line interface
- **LLM Integration**: Leveraging advanced language models for realistic content
- **Comprehensive Logging**: Detailed logging with logfire for debugging and monitoring

## 🛠 Technology Stack

- **Backend**: FastAPI
- **LLM Integration**: OpenAI-compatible API endpoints
- **Data Processing**: Pandas for CSV formatting
- **Logging**: Logfire for structured logging
- **Configuration**: YAML for flexible system settings

## 📋 Prerequisites

- Python 3.12+
- pip or uv package manager
- API key for LLM service
- Logfire account for logging

## 🛠️ Setup Environment

### Option 1: Using UV (Recommended)

1. Install UV package manager:
```bash
pip install uv
```

2. Initialize project and create virtual environment:
```bash
uv sync
```

3. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- macOS/Linux:
```bash
source .venv/bin/activate
```

### Option 2: Using Pip

1. Create a new virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- macOS/Linux:
```bash
source venv/bin/activate
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/synthetic-data-generation.git
cd synthetic-data-generation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API key configuration
```
4. Run Logfire Auth:
```bash
logfire auth
```

## 🔑 Setting up LLM API

1. Get an API key from your LLM provider
2. Get your Logfire project token
3. Add the API key and Logfire token to your `.env` file:
```
API_KEY=your_api_key_here
BASE_URL=your_api_base_url
MODEL=your_model_name  # Default: gemini-2.0-flash
LOGFIRE_TOKEN  = your_logfire_project_token
```

## 🔧 Configuration

Configure system settings in `config/system_config.yaml`:
```yaml
# LLM configuration
llm:
  provider: "openai"
  model: "gpt-4-turbo"
  temperature: 0.7
  max_tokens: 2000

# Output configuration
output:
  default_format: "json"
  file_path: "data/output/"
  include_metadata: true
```

## 🏃‍♂️ Running the Application

### FastAPI Backend

```bash
python main.py
```
The API will be available at http://localhost:8000

### Command Line Interface

```bash
python src/generate_data.py --template emails --count 5 --format json
```

## 📚 API Endpoints

### GET /health
Health check endpoint

### POST /generate
Generate synthetic data
- Request: 
```json
{
  "template_name": "emails",
  "count": 10,
  "output_format": "json"
}
```
- Response: Generated data details

### GET /templates
List available templates

## 💻 Usage Examples

### Python Client
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={
        "template_name": "emails",
        "count": 5,
        "output_format": "json"
    }
)
print(response.json())
```

### Command Line
```bash
# Generate 10 emails in JSON format
python src/generate_data.py --template emails --count 10 --format json

# Generate 5 products in CSV format
python src/generate_data.py --template products --count 5 --format csv
```

## 🏗 Project Structure

```
synthetic-data-generation/
├── main.py                 # FastAPI application
├── src/
│   ├── assistant.py        # LLM integration
│   ├── generator.py        # Main data generation logic
│   ├── generate_data.py    # CLI entry point
│   ├── templates/
│   │   ├── email_template.py   # Email template
│   │   └── product_template.py # Product template
│   └── utils/
│       ├── config_loader.py    # Configuration loading
│       ├── logger.py           # Logging utilities
│       └── output_formatter.py # Output formatting
|       └── pydantic_generator.py # Pydantic model generation 
├── config/
│   ├── email_templates.yaml       # Email generation configurations
│   ├── product_templates.yaml     # Product description configurations  
│   └── system_config.yaml         # System-wide settings
├── data/
│   └── output/             # Generated data output
├── requirements.txt        # Dependencies
└── .env                    # Environment variables
```

## 🔒 Error Handling

The system includes comprehensive error handling with detailed logging:
- Validation errors for input parameters
- Configuration errors
- LLM API connection issues
- Data formatting and output errors

