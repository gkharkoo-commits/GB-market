from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_admin,
    get_current_customer,
    get_db,
)
from backend.app.models.complaint import Complaint
from backend.app.models.user import User
from backend.app.schemas.complaint import (
    ComplaintAdminReply,
    ComplaintCreate,
    ComplaintResponse,
)

router = APIRouter(prefix="/complaints", tags=["Complaints & Support"])

@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def submit_complaint(
    data: ComplaintCreate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
) -> Any:
    """Customer: Submit a complaint or support ticket."""
    complaint = Complaint(
        user_id=current_user.id,
        order_id=data.order_id,
        subject=data.subject.strip(),
        message=data.message.strip(),
        status="Open"
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint

@router.get("/my", response_model=List[ComplaintResponse])
def get_my_complaints(
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
) -> Any:
    """Customer: View their submitted complaints and admin replies."""
    return db.query(Complaint).filter(Complaint.user_id == current_user.id).order_by(Complaint.created_at.desc()).all()

@router.get("/admin/all", response_model=List[ComplaintResponse])
def list_all_complaints_admin(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: View all customer complaints."""
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()

@router.put("/admin/{complaint_id}/reply", response_model=ComplaintResponse)
def reply_complaint_admin(
    complaint_id: int,
    data: ComplaintAdminReply,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin-only: Reply to and update status of a customer complaint."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = data.status
    complaint.admin_response = data.admin_response.strip()
    db.commit()
    db.refresh(complaint)
    return complaint
