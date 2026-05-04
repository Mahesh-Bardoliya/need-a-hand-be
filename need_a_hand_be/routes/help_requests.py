import json
import typing
from datetime import UTC
from datetime import datetime as dt
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import status
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from ..dependencies import get_current_user
from ..dependencies import get_db_session
from ..helpers.errors_and_exceptions import raise_error_message
from ..models import HelpRequest
from ..models import User
from ..schemas.help_requests import HelpRequestCreateSchema
from ..schemas.help_requests import HelpRequestFilterSchema
from ..schemas.help_requests import HelpRequestPaginatePayload
from ..schemas.help_requests import HelpRequestResponseSchema
from ..schemas.utils import PaginatedResponse
from .utils import apply_filters
from .utils import apply_search
from .utils import apply_sorting
from .utils import change_case

help_requests = APIRouter(prefix="/help_requests", tags=["HelpRequests"])


@help_requests.post(
    "/paginate",
    response_model=PaginatedResponse[HelpRequestResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def fetch_help_requests(
    payload: HelpRequestPaginatePayload,
    page: int = 1,
    size: int = 50,
    db_session: Session = Depends(get_db_session),
):
    if page <= 0:
        raise_error_message(
            status_code=400,
            message="Page number should be 1 or greater",
            error_code=4001,
            details=[],
        )
    if size <= 0:
        raise_error_message(
            status_code=400,
            message="Page size should be 1 or greater",
            error_code=4001,
            details=[],
        )

    query = payload.query.model_dump(exclude_unset=True)
    search = payload.search
    sorting = {
        change_case(column_name): order
        for column_name, order in payload.sorting.items()
    }

    help_request_query = db_session.query(HelpRequest).options(
        selectinload(HelpRequest.user)
    )
    if query:
        help_request_query = apply_filters(HelpRequest, help_request_query, query)
    if search:
        help_request_query = apply_search(
            help_request_query,
            HelpRequest,
            ["title", "description", "location"],
            search,
        )

    if sorting:
        help_request_query = apply_sorting(
            HelpRequest, help_request_query, sorting, ["title", "is_active", "location"]
        )
    else:
        help_request_query = help_request_query.order_by(
            desc(func.coalesce(HelpRequest.updated_at, HelpRequest.created_at))
        )

    offset = (page - 1) * size
    help_requests = help_request_query.offset(offset).limit(size).all()

    data = {
        "items": help_requests,
        "size": len(help_requests),
        "page": page,
    }

    return data


@help_requests.get(
    "/{help_request_uuid}",
    response_model=HelpRequestResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def retrieve_help_requests(
    help_request_uuid: UUID,
    db_session: Session = Depends(get_db_session),
):
    """
    Retrieve detailed information for a specific help request.

    Frontend Usage:
    - Use for help request detail page
    - Called when user clicks on a help request from the listing
    - Display complete information about the request and its creator

    Workflow Integration:
    1. User clicks help request in listing:
       - Extract UUID from selected request
       - Navigate to detail page with UUID
       - Fetch full details using this endpoint

    2. Sharing/Deep Linking:
       - Use UUID from URL to fetch request details
       - Show 404 page if request not found

    Error Responses:
    - 404: Help request not found or deleted
    """
    help_request = (
        db_session.query(HelpRequest)
        .filter(HelpRequest.uuid == help_request_uuid)
        .options(selectinload(HelpRequest.user))
    ).one_or_none()
    if not help_request:
        raise_error_message(
            status_code=404,
            message="Help request not found.",
            error_code=4004,
            details=[],
        )
    return help_request


@help_requests.post(
    "",
    response_model=HelpRequestResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_help_requests(
    help_request_data: HelpRequestCreateSchema,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
):
    """
    Create a new help request.

    Frontend Usage:
    - Use in "Create Help Request" form
    - Requires user authentication
    - Automatically sets creator and active status

    Required Fields:
    - title: Request title
    - description: Detailed request description
    - location: Where help is needed

    Workflow Integration:
    1. User Authentication:
       - Ensure user is logged in before showing create form
       - Redirect to login if unauthenticated

    2. Form Submission:
       - Validate required fields client-side
       - Submit form data as JSON
       - Handle successful creation by redirecting to new request

    Error Handling:
    - 401: Unauthorized (not logged in)
    - 400: Invalid request data
    """
    help_request = HelpRequest(**help_request_data.model_dump())
    help_request.user = current_user
    help_request.is_active = True
    db_session.add(help_request)
    db_session.commit()
    return help_request


@help_requests.delete("/{help_request_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_help_requests(
    help_request_uuid: UUID,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
):
    """
    Soft delete a help request.

    Frontend Usage:
    - Use for "Delete Request" button on help request detail page
    - Only show delete option to request owner
    - Implement confirmation dialog before deletion

    Workflow Integration:
    1. Display Conditions:
       - Only show delete button if current user is request owner
       - Add confirmation dialog

    2. After Deletion:
       - Redirect to help requests listing
       - Show success notification
       - Update UI to remove deleted request

    Error Handling:
    - 401: User not authorized (not request owner)
    - 404: Request not found
    """
    help_request = (
        db_session.query(HelpRequest)
        .filter(HelpRequest.uuid == help_request_uuid)
        .options(selectinload(HelpRequest.user))
    ).one_or_none()
    if not help_request:
        raise_error_message(
            status_code=404,
            message="Help request not found.",
            error_code=4004,
            details=[],
        )
    if help_request.user != current_user:
        raise_error_message(
            status_code=403,
            message="Unauthorized.",
            error_code=4003,
            details=[],
        )
    help_request.deleted_at = dt.now(UTC).replace(tzinfo=None)
    db_session.add(help_request)
    db_session.commit()
