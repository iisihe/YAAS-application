from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Auction, Bid
from datetime import datetime


def updateAuction():
    print(datetime.now().time())
    # Make auction state to due, if deadline has passed
    active_auctions = Auction.objects.filter(state='active')
    if len(active_auctions) > 0:
        for active_auction in active_auctions:
            deadline = active_auction.deadline
            if timezone.now() > deadline:
                active_auction.state = 'due'
                active_auction.save()

    # Make auction state to adjudicated, send email to seller and bidder(s)
    due_auctions = Auction.objects.filter(state='due')
    if len(due_auctions) > 0:
        for due_auction in due_auctions:
            bids = Bid.objects.filter(auction=due_auction)
            if len(bids) > 0:
                bidders = []
                for bid in bids:
                    bidders.append(User.objects.get(username=bid.bidder))

                for bidder in bidders:
                    if bidders.index(bidder) == 0:
                        send_mail(
                            'Auction resolved',
                            'Auction you made a bid has now ended. You made the largest offer!',
                            'from@example.com',
                            [bidder.email]
                        )
                    else:
                        send_mail(
                            'Auction resolved',
                            'Auction you made a bid has now ended. Unfortunately you did not make the largest offer.',
                            'from@example.com',
                            [bidder.email]
                        )

            seller = User.objects.filter(username=due_auction.seller)
            send_mail(
                'Auction resolved',
                'Your auction is now resolved.',
                'from@example.com',
                [seller[0].email]
            )

            due_auction.state = 'adjudicated'
            due_auction.save()

