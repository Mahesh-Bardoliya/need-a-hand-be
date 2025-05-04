from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from ..dependencies import get_current_user
from ..dependencies import get_db_session
from ..helpers.errors_and_exceptions import raise_error_message
from ..models import HelpOffer
from ..models import HelpRequest
from ..models import User
from ..schemas.help_offers import HelpOfferCreateSchema
from ..schemas.help_offers import HelpOfferResponseSchema

help_offers = APIRouter(prefix="/help_offers", tags=["HelpOffers"])


@help_offers.post(
    "", response_model=HelpOfferResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_help_offer(
    help_offer_data: HelpOfferCreateSchema,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new offer to help with a request.

    Frontend Usage:
    - Use for "Offer Help" button on help request detail page
    - Only show to authenticated users who aren't request creator
    - Include optional message field in offer form

    Required Fields:
    - help_request_uuid: UUID of help request
    - message: Optional message to request creator

    Workflow Integration:
    1. Display Conditions:
       - Only show "Offer Help" if user is authenticated
       - Hide button if user is request creator
       - Hide if request is inactive

    2. Form Submission:
       - Show message input field (optional)
       - Submit offer with help request UUID
       - Handle success by updating UI state

    Error Handling:
    - 401: Not authenticated
    - 404: Help request not found
    - 400: Can't offer help to own request
    """

    help_request = (
        db_session.query(HelpRequest)
        .filter_by(uuid=help_offer_data.help_request_uuid, deleted_at=None)
        .one_or_none()
    )

    if not help_request:
        raise_error_message(
            status_code=404,
            message="Help request not found.",
            error_code=4004,
            details=[{"dev_error": ""}],
        )

    if help_request.user == current_user:
        raise_error_message(
            status_code=400,
            message="You cannot offer help to your own request.",
            error_code=4005,
            details=[{"dev_error": ""}],
        )

    help_offer = HelpOffer(
        help_request=help_request,
        helper=current_user,
        message=help_offer_data.message,
        is_accepted=False,
    )
    db_session.add(help_offer)
    db_session.commit()

    return help_offer


@help_offers.put(
    "/{help_offer_uuid}/accept",
    response_model=HelpOfferResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def accept_help_offer(
    help_offer_uuid: UUID,
    db_session: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """
    Accept a help offer for your request.

    Frontend Usage:
    - Use for "Accept Offer" button on help request detail page
    - Only show to request owner
    - Updates both offer and request status

    Workflow Integration:
    1. Display Conditions:
       - Only show accept buttons if user is request owner
       - Only show for active requests
       - Implement confirmation dialog

    2. After Acceptance:
       - Update UI to show accepted status
       - Disable other accept buttons
       - Show success notification
       - Update request status to inactive

    Error Handling:
    - 401: Not request owner
    - 404: Help offer not found
    - 400: Request no longer active
    """

    help_offer = (
        db_session.query(HelpOffer)
        .filter_by(uuid=help_offer_uuid, deleted_at=None)
        .options(selectinload(HelpOffer.help_request))
        .one_or_none()
    )

    if not help_offer:
        raise_error_message(
            status_code=404,
            message="Help offer not found.",
            error_code=4004,
            details=[{"dev_error": ""}],
        )

    if not help_offer.help_request.is_active:
        raise_error_message(
            status_code=400,
            message="Help offer is no longer valid.",
            error_code=4000,
            details=[{"dev_error": ""}],
        )

    if help_offer.help_request.user != current_user:
        raise_error_message(
            status_code=401,
            message="Unauthorized.",
            error_code=4001,
            details=[{"dev_error": ""}],
        )

    help_offer.is_accepted = True
    help_offer.help_request.is_active = False
    db_session.commit()

    return help_offer
