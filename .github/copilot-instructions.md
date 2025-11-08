# AI Assistant Instructions for Smart Loan App

This document guides AI coding agents on the essential patterns and workflows for the Smart Loan Assistant application.

## Project Overview

This is a Streamlit-based web application that helps students find and apply for educational loans. Key features:
- Document OCR processing (academic & income proof)
- Bank recommendation engine
- Loan application tracking
- EMI calculator

## Architecture & Data Flow

### Core Components
- `app.py` - Main Streamlit UI and routing
- `auth_csv.py` - User authentication using CSV storage
- `ocr_pipeline.py` - Document processing and data extraction
- `bank_matching.py` - Recommendation algorithm
- `apply.py` - Loan application handling
- `emi.py` - EMI calculations

### Data Storage
- All data persisted in CSV files under `data/`
  - `users.csv` - User accounts
  - `applications.csv` - Loan applications
  - `banks.csv` - Bank details and loan products
  - `documents.csv` - Processed document metadata

### Key Integration Points
1. Tesseract OCR (system dependency)
2. Streamlit for UI rendering
3. CSV-based persistence layer

## Development Workflows

### Setup
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Running the App
```powershell
streamlit run app.py
```

### Required Dependencies
- Python 3.8+
- Tesseract OCR binary on system PATH
- See `requirements.txt` for Python packages

## Project Conventions

### UI Patterns
- Consistent card-based layout using custom CSS in `app.py`
- Navigation handled via Streamlit sidebar radio buttons
- Session state management for user authentication

### Data Access
- All file operations go through Path from pathlib
- CSV operations use pandas DataFrames
- File uploads handled by Streamlit's file_uploader

### Authentication Flow
1. Check session_state.user
2. If None, show login/register tabs
3. Redirect to home after successful auth

## Common Tasks

### Adding a New Feature
1. Create feature-specific Python module
2. Add UI components to relevant section in `app.py`
3. Update data model in CSV if needed

### Debugging
- Check Streamlit logs in terminal
- Verify CSV files in `data/` directory
- Ensure Tesseract is accessible for OCR

### Best Practices
- Use st.session_state for persistent UI state
- Follow existing CSS patterns for consistency
- Handle OCR errors gracefully
- Validate user inputs before CSV operations