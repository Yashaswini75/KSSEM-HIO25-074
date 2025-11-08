# ocr_pipeline.py (email-safe + fully fixed)
from PIL import Image
from pathlib import Path
import json
import os
import pandas as pd
from utils import ensure_dirs, now_iso, atomic_save_csv
import re

# -----------------------------------------------------
# Dependency Flags
# -----------------------------------------------------
PDF_SUPPORT = False
OCR_SUPPORT = False
OCR_MISSING_MSG = ""

try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except Exception:
    PDF_SUPPORT = False
    OCR_MISSING_MSG = "PDF support requires 'pdf2image' package. Install with: pip install pdf2image"

try:
    import pytesseract
    OCR_SUPPORT = True
except Exception:
    OCR_SUPPORT = False
    OCR_MISSING_MSG = "OCR support requires 'pytesseract' package and Tesseract binary. Install with: pip install pytesseract and install Tesseract executable"


# -----------------------------------------------------
# Setup
# -----------------------------------------------------
ensure_dirs()
DOCS_CSV = Path("data") / "documents.csv"


# -----------------------------------------------------
# Helpers
# -----------------------------------------------------
def _ensure_ocr():
    if not OCR_SUPPORT:
        raise RuntimeError(f"OCR not available: {OCR_MISSING_MSG}")


def _ensure_pdf():
    if not PDF_SUPPORT:
        raise RuntimeError(f"PDF support not available: {OCR_MISSING_MSG}")


def _load_docs():
    """Ensure documents.csv exists and has correct columns"""
    expected_cols = [
        'doc_id', 'email', 'upload_time', 'source_files',
        'extracted_name', 'extracted_course', 'extracted_gpa', 'extracted_income', 'extracted_admission_year',
        'raw_text', 'parsed_json'
    ]
    if not os.path.exists(DOCS_CSV) or os.path.getsize(DOCS_CSV) == 0:
        df = pd.DataFrame(columns=expected_cols)
        df.to_csv(DOCS_CSV, index=False)
        return df
    else:
        df = pd.read_csv(DOCS_CSV)
        for c in expected_cols:
            if c not in df.columns:
                df[c] = None
        return df


def _append_doc(row):
    df = _load_docs()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    atomic_save_csv(df, DOCS_CSV)


# -----------------------------------------------------
# OCR Functions
# -----------------------------------------------------
def ocr_from_pdf(pdf_path):
    _ensure_pdf()
    pages = convert_from_path(pdf_path, dpi=200)
    text = []
    for p in pages:
        _ensure_ocr()
        text.append(pytesseract.image_to_string(p))
    return "\n".join(text)


def ocr_from_image(img_path):
    _ensure_ocr()
    img = Image.open(img_path)
    return pytesseract.image_to_string(img)


# -----------------------------------------------------
# Field Extraction (regex)
# -----------------------------------------------------
def extract_fields_from_text(text):
    """Extract structured info from OCR text."""
    name = None
    dob = None
    college = None
    course = None
    gpa = None
    usn = None
    income = None
    admission_year = None
    loan_amount = None

    # Name
    m = re.search(r"Name[:\s]+([A-Z][A-Za-z \.\-]{2,80})", text)
    if m:
        name = m.group(1).strip()
    else:
        m2 = re.search(r"^\s*([A-Z][A-Za-z ]{2,80})\s*$", text, re.MULTILINE)
        if m2:
            name = m2.group(1).strip()

    # GPA / CGPA
    m = re.search(r"(GPA|CGPA)[:\s]*([0-9]{1,2}\.?[0-9]{0,2})", text, re.IGNORECASE)
    if m:
        try:
            gpa = float(m.group(2))
        except:
            gpa = None

    # Income
    m = re.search(r"(Income|Family Income|family_income)[:\s₹Rs\.]*([0-9,]+)", text, re.IGNORECASE)
    if m:
        try:
            income = float(m.group(2).replace(",", ""))
        except:
            income = None

    # Admission Year
    m = re.search(r"Admission\s*Year[:\s]*([0-9]{4})", text, re.IGNORECASE)
    if m:
        try:
            admission_year = int(m.group(1))
        except:
            admission_year = None

    # Course
    m = re.search(r"Course[:\s]*([A-Za-z0-9 \-&]+)", text, re.IGNORECASE)
    if m:
        course = m.group(1).strip()

    # College
    m = re.search(r"College[:\s]*([A-Za-z0-9 &\.-]+)", text, re.IGNORECASE)
    if m:
        college = m.group(1).strip()

    # USN
    m = re.search(r"(USN|Roll No\.?|usn)[:\s]*([A-Z0-9\-]+)", text, re.IGNORECASE)
    if m:
        usn = m.group(2).strip()

    # DOB
    m = re.search(r"(DOB|Date of Birth)[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}/[0-9]{2}/[0-9]{4})", text, re.IGNORECASE)
    if m:
        dob = m.group(2).strip()

    # Loan amount
    m = re.search(r"(loan_amount|Loan amount|Loan Amount)[:\s₹Rs\.]*([0-9,]+)", text, re.IGNORECASE)
    if m:
        try:
            loan_amount = float(m.group(2).replace(",", ""))
        except:
            loan_amount = None

    return dict(
        extracted_name=name,
        extracted_dob=dob,
        extracted_college=college,
        extracted_course=course,
        extracted_gpa=gpa,
        extracted_usn=usn,
        extracted_income=income,
        extracted_admission_year=admission_year,
        extracted_loan_amount=loan_amount,
        raw_text=text
    )


# -----------------------------------------------------
# Main Upload Handler (fixed)
# -----------------------------------------------------
def process_upload(user_email, file_paths: list):
    """
    Process uploaded documents (PDF or image) for OCR + extraction.
    user_email: string identifier for user
    file_paths: list of file paths
    """
    all_text = []
    for p in file_paths:
        p = Path(p)
        try:
            if p.suffix.lower() == ".pdf":
                if not PDF_SUPPORT:
                    raise RuntimeError(f"Cannot process PDF files: {OCR_MISSING_MSG}")
                txt = ocr_from_pdf(str(p))
            elif p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'):
                txt = ocr_from_image(str(p))
            else:
                raise ValueError(f"Unsupported file type: {p.suffix}")
        except Exception as e:
            raise RuntimeError(f"OCR failed for file {p}: {e}")
        all_text.append(txt)

    joined = "\n".join(all_text)
    fields = extract_fields_from_text(joined)
    parsed_json = json.dumps(fields, ensure_ascii=False)

    df = _load_docs()
    new_id = int(df['doc_id'].max()) + 1 if len(df) > 0 and pd.notna(df['doc_id'].max()) else 1

    doc_row = {
        "doc_id": new_id,
        "email": str(user_email).strip(),  # ✅ fixed: store email string
        "upload_time": now_iso(),
        "source_files": json.dumps([str(x) for x in file_paths]),
        **fields,
        "parsed_json": parsed_json
    }

    _append_doc(doc_row)
    return doc_row
