from rest_framework import serializers
from auction.models import Auction, Bid



class AuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = ('id', 'title', 'description', 'seller', 'minPrice',
                  'deadline', 'state','highestBid')
        read_only_fields = ('id', 'title', 'description', 'seller', 'minPrice',
                  'deadline', 'state')


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model: Bid
        fields = ('id', 'auctionId', 'price', 'bidder')


