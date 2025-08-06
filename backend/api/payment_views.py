import os
import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Listing, Transaction
from .serializers import (
    StripeCheckoutSessionSerializer,
    StripeCheckoutSessionResponseSerializer
)

# Stripe API key setup
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', os.environ.get('STRIPE_SECRET_KEY', ''))

# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Initiates a Stripe Checkout Session for purchasing or subscribing to a listing.

    Request: {
        "listing_id": <int>,
        "transaction_type": "purchase" or "subscription"
    }

    Returns: {
        "session_url": "..."
    }
    """
    serializer = StripeCheckoutSessionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    listing_id = serializer.validated_data['listing_id']
    transaction_type = serializer.validated_data['transaction_type']
    user = request.user

    try:
        listing = Listing.objects.get(pk=listing_id)
        if not listing.is_paid:
            return Response({'detail': 'Listing is not paid.'}, status=status.HTTP_400_BAD_REQUEST)
    except Listing.DoesNotExist:
        return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)

    price_cents = int(listing.price * 100)
    metadata = {
        "user_id": str(user.id),
        "listing_id": str(listing.id),
        "transaction_type": transaction_type,
    }
    success_base = os.environ.get("SITE_URL", "http://localhost:3000")
    cancel_base = success_base
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": listing.title,
                            "description": listing.summary,
                        },
                        "unit_amount": price_cents,
                        "recurring": {"interval": "month"} if transaction_type == "subscription" else None,
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription" if transaction_type == "subscription" else "payment",
            customer_email=user.email,
            success_url=f"{success_base}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{cancel_base}/payment-cancelled",
            metadata=metadata,
        )
    except Exception as e:
        return Response({"detail": f"Stripe error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Optionally record a pending transaction
    Transaction.objects.create(
        user=user,
        listing=listing,
        transaction_type=transaction_type,
        payment_provider="stripe",
        amount=listing.price,
        status="pending",
    )
    resp = StripeCheckoutSessionResponseSerializer({"session_url": session.url})
    return Response(resp.data)


# PUBLIC_INTERFACE
@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe webhook endpoint to listen for payment or subscription status changes.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")  # Should be set in .env & Stripe dashboard

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return Response(status=400)
    except stripe.error.SignatureVerificationError:
        return Response(status=400)

    # Handle event types
    if event['type'] in ['checkout.session.completed', 'checkout.session.async_payment_succeeded']:
        session = event['data']['object']
        metadata = session.get('metadata', {})
        user_id = int(metadata.get('user_id', 0))
        listing_id = int(metadata.get('listing_id', 0))
        transaction_type = metadata.get('transaction_type', 'purchase')

        try:
            from .models import Transaction, Listing, User
            listing = Listing.objects.get(pk=listing_id)
            user = User.objects.get(pk=user_id)
            txn = Transaction.objects.filter(
                user=user,
                listing=listing,
                transaction_type=transaction_type,
                payment_provider="stripe",
                status="pending"
            ).order_by('-timestamp').first()
            if txn:
                txn.status = "completed"
                txn.save()
        except Exception:
            pass  # Log in production

    # Optionally, handle failures (checkout.session.expired, payment_failed etc.)

    return Response(status=200)
