# Developer Quick Start

This guide will help you set up the FAS Academic Data API locally for development and testing.

## Prerequisites
- Python 3.10+
- PostgreSQL (if running real ingestion, otherwise SQLite is used for tests)

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/fas-academic-data-api.git
cd fas-academic-data-api
```

## 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

## 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables
Create a `.env` file in the root of the project with safe placeholders:
```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/fas_academic_data
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```
*Note: Never commit real credentials to version control.*

## 5. Run Migrations (If Needed)
If you are setting up the database for the first time:
```bash
PYTHONPATH=. alembic upgrade head
```

## 6. Start the FastAPI Server
```bash
PYTHONPATH=. uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

## 7. View API Documentation
Open your browser and navigate to:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 8. Make Your First API Request
You can test the health endpoint using cURL:
```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "fas-academic-data-api",
  "database": "connected"
}
```

Happy coding! For detailed endpoint usage, please refer to [docs/api.md](api.md).
