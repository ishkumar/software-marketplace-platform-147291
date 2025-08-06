from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from unittest.mock import patch

from .models import Listing, Like, Transaction

User = get_user_model()

class HealthTests(APITestCase):
    def test_health(self):
        url = reverse('Health')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"message": "Server is up!"})

class ManualAuthTests(APITestCase):
    def setUp(self):
        self.reg_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('profile')
        self.username = "testuser"
        self.email = "testuser@example.com"
        self.password = "testpass123"

    def test_register_success(self):
        data = {"username": self.username, "email": self.email, "full_name": "Test User", "password": self.password}
        resp = self.client.post(self.reg_url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue("user" in resp.data)
        self.assertTrue(User.objects.filter(username=self.username).exists())

    def test_register_invalid(self):
        data = {"username": "", "email": "", "password": ""}
        resp = self.client.post(self.reg_url, data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_logout_cycle(self):
        User.objects.create_user(username=self.username, email=self.email, password=self.password)
        resp = self.client.post(self.login_url, {"username": self.username, "password": self.password})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("user" in resp.data)
        # Session established, can logout
        resp = self.client.post(self.logout_url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_login_invalid(self):
        resp = self.client.post(self.login_url, {"username": "nouser", "password": "nopass"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_requires_auth(self):
        resp = self.client.get(self.profile_url)
        # Should NOT be allowed (not authenticated)
        self.assertNotEqual(resp.status_code, 200)

class SocialAuthTests(APITestCase):
    def setUp(self):
        self.google_url = reverse('google-login')
        self.github_url = reverse('github-login')

    @patch("allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter")
    @patch("dj_rest_auth.registration.views.SocialLoginView.as_view")
    def test_google_login_view(self, mock_as_view, mock_adapter):
        # Patch to avoid actually calling Google
        mock_resp = APIClient().post("/")
        mock_resp.status_code = status.HTTP_200_OK
        mock_as_view.return_value = lambda req: mock_resp
        resp = self.client.post(self.google_url, {"access_token": "fake"})
        self.assertIn(resp.status_code, [200, 302, 400, 401])

    @patch("allauth.socialaccount.providers.github.views.GitHubOAuth2Adapter")
    @patch("dj_rest_auth.registration.views.SocialLoginView.as_view")
    def test_github_login_view(self, mock_as_view, mock_adapter):
        mock_resp = APIClient().post("/")
        mock_resp.status_code = status.HTTP_200_OK
        mock_as_view.return_value = lambda req: mock_resp
        resp = self.client.post(self.github_url, {"access_token": "fake"})
        self.assertIn(resp.status_code, [200, 302, 400, 401])

class ListingsCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pub", email="pub@example.com", password="pass")
        self.client.login(username="pub", password="pass")
        self.url = reverse('listings-list-create')
        self.detail_kwargs = lambda pk: {'pk': pk}
        self.app_type = "web"

    def create_listing(self, title="AppX", is_paid=True, price="20.0"):
        return self.client.post(self.url, {
            "title": title,
            "summary": "best app",
            "application_type": self.app_type,
            "is_paid": is_paid,
            "price": price,
            "download_url": "http://example.com/download",
            "external_link": "",
            "tags": ["productivity"]
        }, format="json")

    def test_listing_create_and_retrieve(self):
        resp = self.create_listing()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        pk = resp.data["id"]
        detail_url = reverse('listings-detail', kwargs=self.detail_kwargs(pk))
        getresp = self.client.get(detail_url)
        self.assertEqual(getresp.status_code, 200)
        self.assertEqual(getresp.data["title"], "AppX")

    def test_listing_update(self):
        resp = self.create_listing(title="FirstApp")
        pk = resp.data["id"]
        detail_url = reverse('listings-detail', kwargs=self.detail_kwargs(pk))
        patch = self.client.patch(detail_url, {"title": "UpdatedApp"})
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data["title"], "UpdatedApp")

    def test_listing_delete(self):
        resp = self.create_listing()
        pk = resp.data["id"]
        detail_url = reverse('listings-detail', kwargs=self.detail_kwargs(pk))
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        # Confirm not found
        get_resp = self.client.get(detail_url)
        self.assertEqual(get_resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_listing_search_and_filter(self):
        self.create_listing(title="b", is_paid=True, price="25")
        self.create_listing(title="freeapp", is_paid=False, price=None)
        # Search
        resp = self.client.get(self.url + "?search=freeapp")
        self.assertTrue(any(l["title"] == "freeapp" for l in resp.data))
        # Filter paid
        resp = self.client.get(self.url + "?is_paid=false")
        self.assertTrue(all(l["is_paid"] is False for l in resp.data))

class LikeUnlikeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="a@b.com", password="pass")
        self.pub = User.objects.create_user(username="pub", email="p@b.com", password="pass")
        self.client.login(username="alice", password="pass")
        self.listing = Listing.objects.create(
            publisher=self.pub,
            title="App",
            summary="A",
            application_type="web",
            is_paid=True,
            price="10.0",
        )
        self.like_url = reverse('like-listing', kwargs={'listing_id': self.listing.id})
        self.unlike_url = reverse('unlike-listing', kwargs={'listing_id': self.listing.id})

    def test_like_listing(self):
        resp = self.client.post(self.like_url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["detail"], "Liked.")
        self.assertTrue(Like.objects.filter(user=self.user, listing=self.listing).exists())

    def test_like_already(self):
        self.client.post(self.like_url)
        resp = self.client.post(self.like_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unlike_listing(self):
        self.client.post(self.like_url)
        resp = self.client.post(self.unlike_url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Like.objects.filter(user=self.user, listing=self.listing).exists())

    def test_unlike_without_like(self):
        resp = self.client.post(self.unlike_url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

class EngagementTests(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username="sender", email="s@mail.com", password="pass")
        self.recipient = User.objects.create_user(username="rec", email="r@mail.com", password="pass")
        self.client.login(username="sender", password="pass")
        self.listing = Listing.objects.create(
            publisher=self.recipient,
            title="EngageMe",
            summary="Msg test",
            application_type="web",
            is_paid=True,
            price="15.0",
        )
        self.engage_url = reverse('engage-listing', kwargs={'listing_id': self.listing.id})

    def test_engage_create_and_detail(self):
        resp = self.client.post(self.engage_url, {"message": "Hi there"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        eid = resp.data["id"]
        detail_url = reverse('engagement-detail', kwargs={'pk': eid})
        dresp = self.client.get(detail_url)
        self.assertEqual(dresp.status_code, 200)
        self.assertEqual(dresp.data["message"], "Hi there")

    def test_engage_requires_message(self):
        resp = self.client.post(self.engage_url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inbox_outbox_listing(self):
        self.client.post(self.engage_url, {"message": "Test!"})
        self.client.logout()
        self.client.login(username="rec", password="pass")
        inbox = self.client.get(reverse('engagement-inbox'))
        self.assertTrue(len(inbox.data) >= 1)
        self.client.logout()
        self.client.login(username="sender", password="pass")
        outbox = self.client.get(reverse('engagement-outbox'))
        self.assertTrue(len(outbox.data) >= 1)

    def test_engagement_mark_read(self):
        resp = self.client.post(self.engage_url, {"message": "Check mark read"})
        eid = resp.data["id"]
        self.client.logout()
        self.client.login(username="rec", password="pass")
        mark_url = reverse('engagement-mark-read', kwargs={'pk': eid})
        mark = self.client.post(mark_url)
        self.assertEqual(mark.status_code, 200)
        self.assertEqual(mark.data["detail"], "Marked as read.")

    def test_notification_unread_count(self):
        self.client.post(self.engage_url, {"message": "Check notif"})
        self.client.logout()
        self.client.login(username="rec", password="pass")
        resp = self.client.get(reverse('notifications-list'))
        self.assertIn("unread_inbox_count", resp.data)

class PaymentsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", email="buy@shop.com", password="pass")
        self.pub = User.objects.create_user(username="pub", email="shop@pub.com", password="pass")
        self.listing = Listing.objects.create(
            publisher=self.pub, title="Soft", summary="Soft", application_type="web", is_paid=True, price="30.0"
        )
        self.client.login(username="buyer", password="pass")
        self.checkout_url = reverse('payment-checkout-session')

    @patch("stripe.checkout.Session.create")
    def test_create_checkout_session(self, mock_stripe_create):
        mock_session = type('obj', (object,), {"url": "https://stripe.com/checkout/testsession"})
        mock_stripe_create.return_value = mock_session
        resp = self.client.post(self.checkout_url, {"listing_id": self.listing.id, "transaction_type": "purchase"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("session_url", resp.data)
        # There should now be a pending Transaction in DB
        txn = Transaction.objects.filter(user=self.user, listing=self.listing, status="pending").exists()
        self.assertTrue(txn)

    def test_checkout_requires_authenticated(self):
        self.client.logout()
        resp = self.client.post(self.checkout_url, {"listing_id": self.listing.id, "transaction_type": "purchase"})
        self.assertEqual(resp.status_code, 403)  # IsAuthenticated required

    @patch("stripe.Webhook.construct_event")
    @patch("stripe.checkout.Session.create")
    def test_stripe_webhook_complete(self, mock_stripe_create, mock_webhook_event):
        # Setup: create a pending transaction
        t = Transaction.objects.create(user=self.user, listing=self.listing, transaction_type="purchase",
                                       payment_provider="stripe", amount="30.0", status="pending")
        # Simulate event object as returned by Stripe
        mock_webhook_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {
                        "user_id": str(self.user.id),
                        "listing_id": str(self.listing.id),
                        "transaction_type": "purchase",
                    }
                }
            }
        }
        webhook_url = reverse('payment-stripe-webhook')
        # Simulate stripe sending POST, no sig required for mock
        resp = self.client.post(webhook_url, {}, format='json')
        self.assertEqual(resp.status_code, 200)
        # DB transaction should now be completed
        t.refresh_from_db()
        self.assertEqual(t.status, "completed")
