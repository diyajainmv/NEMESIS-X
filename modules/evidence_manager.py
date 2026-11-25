
from pathlib import Path
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "videos" / "uploads"

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov"}


def save_evidence(uploaded_file):
    """Save an uploaded video permanently."""

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    original_name = Path(uploaded_file.name).name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported video format.")

    unique_name = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return str(file_path.relative_to(BASE_DIR))


def get_evidence_path(relative_path):
    """Get the full path of a saved evidence file."""

    file_path = (BASE_DIR / relative_path).resolve()

    if not file_path.is_relative_to(UPLOAD_DIR.resolve()):
        raise ValueError("Invalid evidence file path.")

    if not file_path.is_file():
        return None

    return file_path
