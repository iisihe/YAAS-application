from django.db import models
from django.contrib.auth.models import User
import uuid



class Auction(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField()
    seller = models.ForeignKey(User, on_delete=models.CASCADE, default='')
    minPrice = models.FloatField(default=0)
    minPriceUSD = models.FloatField(default=0)
    deadline = models.DateTimeField()
    state = models.CharField(max_length=40, default='active')
    uniqueId = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    highestBid = models.FloatField(default=0)
    highestBidUSD = models.FloatField(default=0)
    version = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def getUniqueId(self):
        return self.uniqueId



class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    price = models.FloatField()
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)

    def __unicode__(self):
        return 'price {} bidder: {} in {}' .format(self.price, self.bidder.username, self.auction.title)

    class Meta:
        ordering = ['-price']