from rest_framework import status, generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Listing, Like, Engagement
from .serializers import (
    ListingSerializer, EngagementSerializer
)
from django.db.models import Q
from django.shortcuts import get_object_or_404

@api_view(['GET'])
def health(request):
    return Response({"message": "Server is up!"})

# PUBLIC_INTERFACE
class ListingListCreateView(generics.ListCreateAPIView):
    """List or create software listings. Supports searching and filtering."""
    serializer_class = ListingSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'tags', 'publisher__username', 'application_type']
    ordering_fields = ['created_at', 'price']

    def get_queryset(self):
        queryset = Listing.objects.all().order_by('-created_at')
        # Filtering logic
        application_type = self.request.query_params.get('application_type')
        paid = self.request.query_params.get('is_paid')
        publisher = self.request.query_params.get('publisher')
        tag = self.request.query_params.get('tag')
        # By publisher username
        if publisher:
            queryset = queryset.filter(publisher__username__icontains=publisher)
        if application_type:
            queryset = queryset.filter(application_type=application_type)
        if paid is not None:
            if paid.lower() == "true":
                queryset = queryset.filter(is_paid=True)
            elif paid.lower() == "false":
                queryset = queryset.filter(is_paid=False)
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        # Free text search via DRF search backend
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(summary__icontains=search) |
                Q(tags__icontains=[search])
            )
        return queryset

    def perform_create(self, serializer):
        # Publisher is the logged-in user
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(publisher=user)


# PUBLIC_INTERFACE
class ListingRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a single listing."""
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsPublisherOrReadOnly (custom) for production


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_listing(request, listing_id):
    """Like a software listing."""
    user = request.user
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)
    like, created = Like.objects.get_or_create(user=user, listing=listing)
    if not created:
        return Response({'detail': 'Already liked.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Liked.'}, status=status.HTTP_201_CREATED)

# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unlike_listing(request, listing_id):
    """Unlike a software listing."""
    user = request.user
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)
    Like.objects.filter(user=user, listing=listing).delete()
    return Response({'detail': 'Unliked.'}, status=status.HTTP_204_NO_CONTENT)

# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def engage_listing(request, listing_id):
    """
    Initiate engagement (message/contact) with publisher of a listing.
    Input: {message: "..."}
    """
    user = request.user
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)
    message = request.data.get('message', '')
    if not message:
        return Response({'detail': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)
    engagement = Engagement.objects.create(
        sender=user,
        recipient=listing.publisher,
        listing=listing,
        message=message,
        status='pending',
        sender_read=True,
        recipient_read=False,
    )
    return Response(EngagementSerializer(engagement).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
class EngagementListView(generics.ListAPIView):
    """
    List all engagements for current user (both inbox and outbox).
    """
    serializer_class = EngagementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Engagement.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-created_at')


# PUBLIC_INTERFACE
class InboxEngagementListView(generics.ListAPIView):
    """
    List all engagements received by the currently authenticated user ("inbox").
    """
    serializer_class = EngagementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Engagement.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')


# PUBLIC_INTERFACE
class OutboxEngagementListView(generics.ListAPIView):
    """
    List all engagements sent by the currently authenticated user ("outbox").
    """
    serializer_class = EngagementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Engagement.objects.filter(
            sender=self.request.user
        ).order_by('-created_at')


# PUBLIC_INTERFACE
class EngagementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update (status/message/read), or delete a specific engagement (if sender or recipient).
    PATCH/PUT payload may include status, message, and will also mark as read for the accessing user.
    """
    queryset = Engagement.objects.all()
    serializer_class = EngagementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        # Only allow sender or recipient
        if obj.sender != user and obj.recipient != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not authorized.")
        return obj

    def perform_update(self, serializer):
        """
        On update, mark engagement as read for the updating user.
        """
        engagement = serializer.instance
        user = self.request.user
        data = serializer.validated_data
        # Mark as read by who updates/view
        if user == engagement.recipient:
            data['recipient_read'] = True
        elif user == engagement.sender:
            data['sender_read'] = True
        serializer.save()


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_engagement_read(request, pk):
    """
    Mark an engagement (message) as read for the current user.
    """
    engagement = get_object_or_404(Engagement, pk=pk)
    user = request.user
    if engagement.recipient == user:
        engagement.recipient_read = True
    elif engagement.sender == user:
        engagement.sender_read = True
    else:
        return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
    engagement.save()
    return Response({"detail": "Marked as read."})


# PUBLIC_INTERFACE
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notifications_list(request):
    """
    List notifications for the current user.
    (Placeholder: For now, returns count/new engagements. To be extended for richer UX.)
    """
    user = request.user
    unread_inbox_count = Engagement.objects.filter(recipient=user, recipient_read=False).count()
    # Optionally, include outgoing unread (rarely used)
    return Response({
        "unread_inbox_count": unread_inbox_count,
        "notification_types": ["engagement:new_message"],
    })
