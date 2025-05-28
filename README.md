# TasteBite Backend

Backend API for the TasteBite recipe sharing platform.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with the following variables:
```
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tastebite
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the development server:
```bash
flask run
```

## API Documentation

The API provides endpoints for:
- User authentication
- Recipe management
- Comments and ratings
- External recipe integration (TheMealDB)
- AI-powered recipe generation

## Deployment

This application is configured for deployment on Render.com. The following services are required:
- Web Service (Backend API)
- PostgreSQL Database 