from django.urls import path
from .views import (
    health,
    ListingListCreateView,
    ListingRetrieveUpdateView,
    like_listing,
    unlike_listing,
    engage_listing,
    EngagementListView,
    EngagementDetailView,
    InboxEngagementListView,
    OutboxEngagementListView,
    mark_engagement_read,
    notifications_list,
)
from .auth_views import (
    register, login_view, logout_view, profile,
    google_login, github_login,
)
from .payment_views import (
    create_checkout_session,
    stripe_webhook,
)

urlpatterns = [
    path('health/', health, name='Health'),
    path('auth/register/', register, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/profile/', profile, name='profile'),
    path('auth/google/', google_login, name='google-login'),
    path('auth/github/', github_login, name='github-login'),

    # Listings
    path('listings/', ListingListCreateView.as_view(), name='listings-list-create'),
    path('listings/<int:pk>/', ListingRetrieveUpdateView.as_view(), name='listings-detail'),
    # Like / Unlike
    path('listings/<int:listing_id>/like/', like_listing, name='like-listing'),
    path('listings/<int:listing_id>/unlike/', unlike_listing, name='unlike-listing'),
    # Engagement (messaging) endpoints
    path('listings/<int:listing_id>/engage/', engage_listing, name='engage-listing'),
    path('engagements/', EngagementListView.as_view(), name='user-engagements'),
    path('engagements/<int:pk>/', EngagementDetailView.as_view(), name='engagement-detail'),
    path('engagements/inbox/', InboxEngagementListView.as_view(), name='engagement-inbox'),
    path('engagements/outbox/', OutboxEngagementListView.as_view(), name='engagement-outbox'),
    path('engagements/<int:pk>/mark-read/', mark_engagement_read, name='engagement-mark-read'),
    path('notifications/', notifications_list, name='notifications-list'),  # Placeholder

    # Stripe payment endpoints
    path('payment/checkout-session/', create_checkout_session, name='payment-checkout-session'),
    path('payment/stripe-webhook/', stripe_webhook, name='payment-stripe-webhook'),
]
