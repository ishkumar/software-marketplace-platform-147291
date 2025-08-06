from django.db import models

# PUBLIC_INTERFACE
class User(models.Model):
    """Marketplace user, includes publishers and regular users."""
    PROVIDER_CHOICES = [
        ('local', 'Local'),
        ('google', 'Google'),
        ('github', 'GitHub'),
    ]
    username = models.CharField(max_length=64, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES, default='local')
    full_name = models.CharField(max_length=128, blank=True, null=True)
    avatar_url = models.URLField(max_length=512, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_publisher = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.username

# PUBLIC_INTERFACE
class Listing(models.Model):
    """Software listing published on the marketplace."""
    APP_TYPE_CHOICES = [
        ('saas', 'SaaS'),
        ('mobile', 'Mobile'),
        ('web', 'Web'),
        ('desktop', 'Desktop'),
        ('api', 'API'),
    ]
    publisher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=128)
    summary = models.TextField(blank=True)
    application_type = models.CharField(max_length=16, choices=APP_TYPE_CHOICES)
    is_paid = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    download_url = models.URLField(max_length=512, blank=True, null=True)
    external_link = models.URLField(max_length=512, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

# PUBLIC_INTERFACE
class Like(models.Model):
    """Record of a user liking a software listing."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'listing')

# PUBLIC_INTERFACE
class Transaction(models.Model):
    """Purchase or subscription transaction for a software listing."""
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('subscription', 'Subscription'),
    ]
    PAYMENT_PROVIDER_CHOICES = [
        ('manual', 'Manual'),
        ('stripe', 'Stripe'),
        ('test', 'Test'),
    ]
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=16, choices=TRANSACTION_TYPE_CHOICES)
    payment_provider = models.CharField(max_length=16, choices=PAYMENT_PROVIDER_CHOICES, default='manual')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

# PUBLIC_INTERFACE
class Engagement(models.Model):
    """Engagement between a user and publisher (e.g., message or contact request)."""
    ENGAGEMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('resolved', 'Resolved'),
    ]
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_engagements')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_engagements')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=ENGAGEMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
