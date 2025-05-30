"""
Tenders API endpoints.
"""

from typing import List, Any, Optional, Dict
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_current_active_user
from app.domains.auth.models import User
from app.domains.tenders.service import TenderService
from app.domains.tenders.schemas import (
    TenderCreate, TenderUpdate, TenderResponse, TenderListResponse,
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteListResponse,
    TenderDocumentResponse, TenderInvitationCreate, TenderInvitationResponse,
    TenderWatchResponse, TenderStatsResponse
)

router = APIRouter()
tender_service = TenderService()


# Tender endpoints
@router.get("/", response_model=TenderListResponse)
async def get_tenders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    tender_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderListResponse:
    """Get list of tenders with filtering and pagination."""
    try:
        result = await tender_service.get_tenders(
            session=session,
            current_user=current_user,
            skip=skip,
            limit=limit,
            status=status,
            tender_type=tender_type,
            category=category,
            search=search
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tenders: {str(e)}"
        )


@router.post("/", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
async def create_tender(
    tender_data: TenderCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderResponse:
    """Create a new tender."""
    try:
        tender = await tender_service.create_tender(
            session=session,
            current_user=current_user,
            tender_data=tender_data
        )
        return tender
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tender: {str(e)}"
        )


@router.get("/{tender_id}", response_model=TenderResponse)
async def get_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderResponse:
    """Get tender by ID."""
    try:
        tender = await tender_service.get_tender_by_id(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        if not tender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        return tender
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tender: {str(e)}"
        )


@router.put("/{tender_id}", response_model=TenderResponse)
async def update_tender(
    tender_id: UUID,
    tender_data: TenderUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderResponse:
    """Update tender."""
    try:
        tender = await tender_service.update_tender(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            tender_data=tender_data
        )
        if not tender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        return tender
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tender: {str(e)}"
        )


@router.delete("/{tender_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete tender."""
    try:
        deleted = await tender_service.delete_tender(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tender: {str(e)}"
        )


@router.post("/{tender_id}/publish", response_model=TenderResponse)
async def publish_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderResponse:
    """Publish a tender (change status from draft to published)."""
    try:
        tender = await tender_service.publish_tender(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        if not tender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        return tender
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error publishing tender: {str(e)}"
        )


@router.post("/{tender_id}/close", response_model=TenderResponse)
async def close_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderResponse:
    """Close a tender (change status to closed)."""
    try:
        tender = await tender_service.close_tender(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        if not tender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        return tender
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error closing tender: {str(e)}"
        )


# Quote endpoints
@router.get("/{tender_id}/quotes", response_model=QuoteListResponse)
async def get_tender_quotes(
    tender_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> QuoteListResponse:
    """Get all quotes for a tender."""
    try:
        result = await tender_service.get_tender_quotes(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            skip=skip,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving quotes: {str(e)}"
        )


@router.post("/{tender_id}/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    tender_id: UUID,
    quote_data: QuoteCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> QuoteResponse:
    """Create a new quote for a tender."""
    try:
        quote = await tender_service.create_quote(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            quote_data=quote_data
        )
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quote: {str(e)}"
        )


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> QuoteResponse:
    """Get quote by ID."""
    try:
        quote = await tender_service.get_quote_by_id(
            session=session,
            current_user=current_user,
            quote_id=quote_id
        )
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )
        return quote
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving quote: {str(e)}"
        )


@router.put("/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: UUID,
    quote_data: QuoteUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> QuoteResponse:
    """Update quote."""
    try:
        quote = await tender_service.update_quote(
            session=session,
            current_user=current_user,
            quote_id=quote_id,
            quote_data=quote_data
        )
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating quote: {str(e)}"
        )


@router.delete("/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete quote."""
    try:
        deleted = await tender_service.delete_quote(
            session=session,
            current_user=current_user,
            quote_id=quote_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting quote: {str(e)}"
        )


@router.post("/quotes/{quote_id}/submit", response_model=QuoteResponse)
async def submit_quote(
    quote_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> QuoteResponse:
    """Submit a quote (change status from draft to submitted)."""
    try:
        quote = await tender_service.submit_quote(
            session=session,
            current_user=current_user,
            quote_id=quote_id
        )
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting quote: {str(e)}"
        )


@router.post("/quotes/{quote_id}/award", response_model=QuoteResponse)
async def award_quote(
    quote_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> QuoteResponse:
    """Award a quote (change status to awarded)."""
    try:
        quote = await tender_service.award_quote(
            session=session,
            current_user=current_user,
            quote_id=quote_id
        )
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error awarding quote: {str(e)}"
        )


# Document endpoints
@router.get("/{tender_id}/documents", response_model=List[TenderDocumentResponse])
async def get_tender_documents(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> List[TenderDocumentResponse]:
    """Get all documents for a tender."""
    try:
        documents = await tender_service.get_tender_documents(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )


@router.post("/{tender_id}/documents", response_model=TenderDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_tender_document(
    tender_id: UUID,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_public: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderDocumentResponse:
    """Upload a document for a tender."""
    try:
        document = await tender_service.upload_tender_document(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            file=file,
            name=name,
            description=description,
            is_public=is_public
        )
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.delete("/{tender_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tender_document(
    tender_id: UUID,
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a tender document."""
    try:
        deleted = await tender_service.delete_tender_document(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            document_id=document_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


# Invitation endpoints
@router.get("/{tender_id}/invitations", response_model=List[TenderInvitationResponse])
async def get_tender_invitations(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> List[TenderInvitationResponse]:
    """Get all invitations for a tender."""
    try:
        invitations = await tender_service.get_tender_invitations(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        return invitations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving invitations: {str(e)}"
        )


@router.post("/{tender_id}/invitations", response_model=TenderInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_tender_invitation(
    tender_id: UUID,
    invitation_data: TenderInvitationCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderInvitationResponse:
    """Create a new invitation for a tender."""
    try:
        invitation = await tender_service.create_tender_invitation(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            invitation_data=invitation_data
        )
        return invitation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating invitation: {str(e)}"
        )


@router.post("/{tender_id}/invitations/{invitation_id}/accept", response_model=TenderInvitationResponse)
async def accept_tender_invitation(
    tender_id: UUID,
    invitation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderInvitationResponse:
    """Accept a tender invitation."""
    try:
        invitation = await tender_service.accept_tender_invitation(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            invitation_id=invitation_id
        )
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        return invitation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accepting invitation: {str(e)}"
        )


@router.post("/{tender_id}/invitations/{invitation_id}/reject", response_model=TenderInvitationResponse)
async def reject_tender_invitation(
    tender_id: UUID,
    invitation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderInvitationResponse:
    """Reject a tender invitation."""
    try:
        invitation = await tender_service.reject_tender_invitation(
            session=session,
            current_user=current_user,
            tender_id=tender_id,
            invitation_id=invitation_id
        )
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        return invitation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting invitation: {str(e)}"
        )


# Watch endpoints
@router.post("/{tender_id}/watch", response_model=TenderWatchResponse, status_code=status.HTTP_201_CREATED)
async def watch_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderWatchResponse:
    """Start watching a tender for updates."""
    try:
        watch = await tender_service.watch_tender(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        return watch
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error watching tender: {str(e)}"
        )


@router.delete("/{tender_id}/watch", status_code=status.HTTP_204_NO_CONTENT)
async def unwatch_tender(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Stop watching a tender."""
    try:
        unwatched = await tender_service.unwatch_tender(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        if not unwatched:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watch not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unwatching tender: {str(e)}"
        )


@router.get("/{tender_id}/watch", response_model=Optional[TenderWatchResponse])
async def get_tender_watch(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Optional[TenderWatchResponse]:
    """Get current user's watch for a tender."""
    try:
        watch = await tender_service.get_tender_watch(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        return watch
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving watch: {str(e)}"
        )


# Statistics endpoints
@router.get("/{tender_id}/stats", response_model=TenderStatsResponse)
async def get_tender_stats(
    tender_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> TenderStatsResponse:
    """Get statistics for a tender."""
    try:
        stats = await tender_service.get_tender_stats(
            session=session,
            current_user=current_user,
            tender_id=tender_id
        )
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tender not found"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving stats: {str(e)}"
        )


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_tenders_overview_stats(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get overview statistics for all accessible tenders."""
    try:
        stats = await tender_service.get_tenders_overview_stats(
            session=session,
            current_user=current_user
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving overview stats: {str(e)}"
        )
