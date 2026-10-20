import os
import secrets
import uuid
from typing import Any
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_admin, get_current_user, get_db
from backend.app.core.config import settings
from backend.app.models.shop import Shop, ShopVerificationDoc
from backend.app.models.user import User

router = APIRouter(prefix="/uploads", tags=["Uploads & Media"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_DOC_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = "general",
    current_user: User = Depends(get_current_user)
) -> Any:
    """Uploads and validates an image file (shops, products, profile)."""
    # Restrict folder names to prevent directory traversal
    if folder not in ["shops", "products", "profiles", "general"]:
        folder = "general"

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Validate image content using Pillow
    try:
        from io import BytesIO
        img = Image.open(BytesIO(content))
        img.verify()  # Verifies that it's a valid image
    except Exception:
        raise HTTPException(status_code=400, detail="Corrupted or invalid image file")

    safe_filename = f"{uuid.uuid4().hex}{ext}"
    dest_dir = os.path.join(settings.UPLOAD_DIR, folder)
    _ensure_dir(dest_dir)
    file_path = os.path.join(dest_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # URL path relative to static mount
    relative_url = f"/uploads/{folder}/{safe_filename}"
    return {
        "url": relative_url,
        "filename": safe_filename,
        "original_name": filename,
        "size_bytes": len(content)
    }

@router.post("/document")
async def upload_verification_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Uploads a private verification document for merchant shop verification."""
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="You must create a shop application before uploading documents")

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document format. Allowed: {', '.join(ALLOWED_DOC_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    safe_filename = f"doc_{uuid.uuid4().hex}{ext}"
    dest_dir = os.path.join(settings.UPLOAD_DIR, "documents")
    _ensure_dir(dest_dir)
    file_path = os.path.join(dest_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    doc = ShopVerificationDoc(
        shop_id=shop.id,
        document_type=document_type.strip(),
        file_path=file_path,
        original_filename=filename,
        file_size_bytes=len(content),
        is_verified=False
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "document_type": doc.document_type,
        "original_filename": doc.original_filename,
        "uploaded_at": doc.uploaded_at
    }

@router.get("/documents/{doc_id}")
def view_verification_document(
    doc_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Securely view/download a merchant's private verification document."""
    doc = db.query(ShopVerificationDoc).filter(ShopVerificationDoc.id == doc_id).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    
    return FileResponse(doc.file_path, filename=doc.original_filename)
