from django.test import TestCase, Client
from auction.models import Auction
from django.contrib.auth.models import User
from django.urls import reverse


# Test for auction creation. It will create an auction and then check if the description of it can be found in the list of auctions
class CreateAuctionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testUser", password="asd123qw")

    def test_auctionCreate(self):

        client = Client()
        client.get(reverse('home'))

        login = client.login(username='testUser', password='asd123qw')
        self.assertTrue(login)

        title = "testtitle"
        description= "testdescription"
        minPrice = 2.0
        deadline = "2019-01-01 12:00"
        client.get(reverse("add_auction"))
        client.post(reverse("add_auction"),
                               {"title": title, "description": description, "minPrice": minPrice,
                                "deadline": deadline}, follow=True)
        client.post(reverse("auction_confirm"), {"option": "Yes", "auction_title": title, "auction_description": description,
                                                            "auction_minprice": minPrice, "auction_deadline": deadline})

        response = client.get(reverse("home"))
        self.assertContains(response, "Description:  testdescription")


#Test for making bid. It will make a bid and check if the highest bid of the auction has changed.
class BidAuctionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testUser", password="asd123qw")

    def test_auctionBid(self):

        client = Client()
        client.get(reverse('home'))

        login = client.login(username='testUser', password='asd123qw')
        self.assertTrue(login)

        auction = Auction(title="test", description="description", seller=User.objects.create(first_name='seller', email="example@example.com", password="asd123qw"),
                          minPrice="2.0", deadline="2019-01-01 12:00", state="active", version=0)
        auction.save()

        client.get(reverse("bid_auction", kwargs={"id": 1}))
        response = client.post(reverse("bid_auction", kwargs={"id": 1}),
                               {"newBid": "50.0", "version": 0, "auction": auction}, follow=True)
        self.assertContains(response, "Highest bid:  50.0")


# Test for concurrent use. It makes two user to bid an auction so, that one of users makes a bid, and then the other user
# tries to make a lower bid. It is checked, that the latest bid isn't saved and the user get error message about it.
class ConcurrentTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username="testUser1", password="asd123qw")
        self.user2 = User.objects.create_user(username="testUser2", password="asd123qw")

    def test_concurrent(self):

        client1 = Client()
        client2 = Client()

        client1.get(reverse('home'))
        login = client1.login(username='testUser1', password='asd123qw')
        self.assertTrue(login)

        client2.get(reverse('home'))
        login = client2.login(username='testUser2', password='asd123qw')
        self.assertTrue(login)

        auction = Auction(title="test", description="description", seller=User.objects.create(first_name='seller', email="example@example.com", password="asd123qw"),
                          minPrice="2.0", deadline="2019-01-01 12:00", state="active", version=0)
        auction.save()

        client1.get(reverse("bid_auction", kwargs={"id": 1}))

        client2.get(reverse("bid_auction", kwargs={"id": 1}))
        response = client2.post(reverse("bid_auction", kwargs={"id": 1}),
                               {"newBid": "50.0", "version": 0, "auction": auction}, follow=True)

        self.assertContains(response, "Highest bid:  50.0")

        response = client1.post(reverse("bid_auction", kwargs={"id": 1}),
                                {"newBid": "49.0", "version": 0, "auction": auction}, follow=True)
        self.assertContains(response, "highest bid of auction has changed.")

        response = client1.get(reverse('home'))
        self.assertContains(response, "Highest bid:  50.0")
