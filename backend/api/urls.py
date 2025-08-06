from django.urls import path
from .views import (
    health,
    ListingListCreateView,
    ListingRetrieveUpdateView,
    like_listing,
    unlike_listing,
    engage_listing,
    EngagementListView,
)
from .auth_views import (
    register, login_view, logout_view, profile,
    google_login, github_login,
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
    # Engagement
    path('listings/<int:listing_id>/engage/', engage_listing, name='engage-listing'),
    path('engagements/', EngagementListView.as_view(), name='user-engagements'),
]
