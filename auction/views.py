from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from .models import Auction, Bid
from auction.forms import AddAuctionForm, ConfAuctionForm, CreateUserForm, EditProfileForm
from .serializers import AuctionSerializer

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.core.mail import send_mail
from os.path import isfile
import os, requests

from datetime import datetime
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from django.utils import translation

from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMAIL_DIR = os.path.join(BASE_DIR, "auction/emails")


def archive(request):
    if request.user.is_authenticated:
        set_lang(request, request.user.first_name)
    auctions = Auction.objects.filter(state='active').order_by('deadline')
    currencyRate = getCurrencyRate()
    for auction in auctions:
            auction.minPriceUSD = getUSDPrice(auction.minPrice, currencyRate)
            auction.highestBidUSD = getUSDPrice(auction.highestBid, currencyRate)
            auction.save()
    return render(request, "archive.html", {'auctions': auctions})

def set_lang(request, lang_code):
    translation.activate(lang_code)
    request.session[translation.LANGUAGE_SESSION_KEY] = lang_code

def setLanguage(request):
    return render(request, 'language_change.html')

class AddAuction(LoginRequiredMixin, View):
    def get(self, request):
        form = AddAuctionForm()
        return render(request, 'add_auction.html', {'form': form})

    def post(self, request):
        form = AddAuctionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            auction_title = cd['title']
            auction_description = cd['description']
            auction_minprice = float(cd['minPrice'])
            #auction_currency = cd['currency']
            auction_deadline = cd['deadline']
            print("Add auction:", auction_title)
            form = ConfAuctionForm({"auction_title": auction_title, "auction_description": auction_description,
                                    "auction_minprice": auction_minprice, "auction_deadline": auction_deadline})
            return render(request, 'auction_confirm.html', {'form': form})
        else:
            messages.add_message(request, messages.ERROR, "Not valid data")
            return render(request, 'add_auction.html', {'form': form})


@login_required
def saveAuction(request):
    option = request.POST.get('option', '')
    if option == 'Yes':
        auction_title = request.POST.get('auction_title', '')
        auction_description = request.POST.get('auction_description', '')
        auction_minprice = request.POST.get('auction_minprice', '')
        auction_deadline = request.POST.get('auction_deadline', '')
        #tz = pytz.timezone('Europe/Helsinki')
        #auction_deadline.replace(tzinfo=tz)
        #auction_currency = request.POST.get('auction_currency', '')
        print("Save auction:", auction_title, auction_description)
        auction = Auction(title=auction_title, description=auction_description, seller=request.user, deadline=auction_deadline, minPrice=auction_minprice)
        print(auction_minprice)
        print(type(auction_minprice))
        auction.save()
        auction_uniqueId = Auction.getUniqueId(auction)
        send_mail(
            ('Auction added'),
            ('Hi ') + auction.seller.username +('! Your auction ') + auction.title + (' is now added to our website. You can edit your auction by logging in and going Your Auctions -> Edit auction, or '
            'edit auction via this link: localhost:8000/edit/') + str(auction_uniqueId),
            'from@example.com',
            [request.user.email]
        )
        messages.add_message(request, messages.INFO, _("New auction has been saved"))
        return HttpResponseRedirect(reverse("home"))
    else:
        messages.add_message(request, messages.INFO, _("Auction cancelled"))
        return HttpResponseRedirect(reverse("home"))


class EditAuction(LoginRequiredMixin, View):
    def get(self, request, id):
        auction = get_object_or_404(Auction, id=id)
        if (request.user == auction.seller):
            return render(request, "edit_auction.html",
                          {'seller': request.user,
                           "title": auction.title,
                           "id": auction.id,
                           "description": auction.description,
                           "minprice": auction.minPrice,
                           "deadline": auction.deadline})
        else:
            return HttpResponseRedirect(reverse("home"))

    def post(self, request, id):
        auction = get_object_or_404(Auction, id=id)
        auctions = Auction.objects.filter(id=id)
        if len(auctions) > 0 and request.user == auction.seller:
            auction = auctions[0]
        else:
            messages.add_message(request, messages.INFO, _("Invalid auction id"))
            return HttpResponseRedirect(reverse("home"))


        description = request.POST["description"].strip()
        auction.description = description
        auction.version += 1
        auction.save()
        messages.add_message(request, messages.INFO, "Auction updated")
        return HttpResponseRedirect(reverse("your_auctions"))


class EditAuctionLink(View):
    def get(self, request, uniqueId):
        auction = get_object_or_404(Auction, uniqueId=uniqueId)
        return render(request, "edit_auction.html",
                        {'seller': auction.seller,
                        "title": auction.title,
                        "id": auction.id,
                        "description": auction.description,
                        "minprice": auction.minPrice,
                        "deadline": auction.deadline,
                        "uniqueId": auction.uniqueId})

    def post(self, request, uniqueId):
        auctions = Auction.objects.filter(uniqueId=uniqueId)
        if len(auctions) > 0:
            auction = auctions[0]
        else:
            messages.add_message(request, messages.INFO, _("Invalid auction id"))
            return HttpResponseRedirect(reverse("home"))


        description = request.POST["description"].strip()
        auction.description = description
        auction.save()
        messages.add_message(request, messages.INFO, _("Auction updated"))
        return HttpResponseRedirect(reverse("home"))


@login_required
def yourAuctions(request):
    auction = Auction.objects.all()
    return render(request, "your_auctions.html", {'auctions': auction})

class Registration(View):
    def get(self, request):
        form = CreateUserForm()
        return render(request, "registration/registration.html", {'form': form})

    def post(self, request):
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.ERROR, _("Successfully registrated!"))
            return HttpResponseRedirect(reverse("home"))
        else:
            messages.error(request, _('Check the values in the form.'))
            return render(request, "registration/registration.html", {'form': form})



class ChangePassword(LoginRequiredMixin, View):
    def get(self, request):
        form = PasswordChangeForm(request.user)
        return render(request, 'change_password.html', {'form': form})

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Your password was successfully updated!'))
            return redirect('change_password')
        else:
            messages.error(request, _('The password was not suitable'))
            return render(request, 'change_password.html', {'form': form})


class EditProfile(LoginRequiredMixin, View):
    def get(self, request):
        form = EditProfileForm(instance=request.user)
        return render(request, 'edit_profile.html', {'form': form})

    def post(self, request):
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile is successfully updated!'))
            return redirect('change_email')
        else:
            messages.error(request, _('Could not save the changes'))
            return render(request, 'archive.html', {'form': form})


def search(request):
    auctions = Auction.objects.filter(Q(title=request.GET.get('search')))
    return render(request, 'archive.html', {'auctions': auctions})


@staff_member_required
def emailhistory(request):
    files = [f for f in os.listdir(EMAIL_DIR) if isfile(os.path.join(EMAIL_DIR, f))]
    contents = []
    for file in files:
        path = os.path.join(EMAIL_DIR, file)
        contents.append(open(path, 'r').read())
    return render(request, 'email_history.html', {'contents': contents})


@staff_member_required
def banAuction(request, id):
    auction = Auction.objects.get(id=id)
    auction.state = 'banned'
    auction.save()

    bids = Bid.objects.filter(auction=auction)
    if len(bids) > 0:
        bidders = []
        for bid in bids:
            bidders.append(User.objects.get(username=bid.bidder))

        for bidder in bidders:
            send_mail(
                'Auction banned',
                'Auction you made a bid is banned.',
                'from@example.com',
                [bidder.email]
            )

    seller = User.objects.filter(username=auction.seller)
    send_mail(
        'Auction banned',
        'Your auction is banned because it did not follow the terms of the site.',
        'from@example.com',
        [seller[0].email]
    )

    messages.add_message(request, messages.INFO, "Auction banned")
    return HttpResponseRedirect(reverse("all_auctions"))


@staff_member_required
def allAuctions(request):
    auction = Auction.objects.all()
    # for auction in auction:
    #     print(type(auction.state))
    return render(request, "all_auctions.html", {'auctions': auction})

class MakeBid(LoginRequiredMixin, View):
    def get(self, request, id):
        auctions = Auction.objects.filter(state='active')
        currencyRate = getCurrencyRate()
        for auction in auctions:
            auction.minPriceUSD = getUSDPrice(auction.minPrice, currencyRate)
            auction.highestBidUSD = getUSDPrice(auction.highestBid, currencyRate)
            auction.save()
        auction = Auction.objects.get(id=id)
        if userCanBid(request, auction):
            return render(request, 'bid_auction.html',
                          {'seller': auction.seller,
                           "title": auction.title,
                           "id": auction.id,
                           "description": auction.description,
                           "minprice": auction.minPrice,
                           "minPriceUSD": auction.minPriceUSD,
                           "deadline": auction.deadline,
                           "uniqueId": auction.uniqueId,
                           "highestBid": auction.highestBid,
                           "highestBidUSD": auction.highestBidUSD,
                           "version": auction.version})
        else:
            messages.error(request, _('You cannot make a bid to this auction because you already have the highest bid, '
                                      'or you are the seller of the auction or the auction is not active.'))
            return HttpResponseRedirect(reverse('home'))


    def post(self, request, id):
        auction = Auction.objects.get(id=id)
        newBid = request.POST.get('newBid')
        version = request.POST.get('version')
        if int(auction.version) != int(version):
            messages.error(request, ('Bid was not saved, because the auction desription or highest bid of auction has changed. Please bid again.'))
            return render(request, 'bid_auction.html',
                          {'seller': auction.seller,
                           "title": auction.title,
                           "id": auction.id,
                           "description": auction.description,
                           "minprice": auction.minPrice,
                           "deadline": auction.deadline,
                           "uniqueId": auction.uniqueId,
                           "highestBid": auction.highestBid,
                           "version": auction.version})
        if bidIsValid(request, auction, newBid):
            newBid = float(newBid)
            makeBid(request, auction, newBid)
            messages.add_message(request, messages.INFO, "Bid is now made.")
            return HttpResponseRedirect(reverse('home'))
        else:
            messages.error(request, 'Not valid bid.')
            return render(request, 'bid_auction.html',
                          {'seller': auction.seller,
                           "title": auction.title,
                           "id": auction.id,
                           "description": auction.description,
                           "minprice": auction.minPrice,
                           "deadline": auction.deadline,
                           "uniqueId": auction.uniqueId,
                           "highestBid": auction.highestBid,
                           "version": auction.version})

def makeBid(request, auction, newBid):
    if thereAreBids(auction):
        previousBuyer = getHighestBid(auction).bidder
        send_mail(
            'New bid has made',
            'Hi ' + previousBuyer.username + '! There is a new bid in auction ' + auction.title + ' you have bid.',
            'from@example.com',
            [previousBuyer.email]
        )
    Bid.objects.filter(auction=auction, bidder=request.user).delete()
    Bid(auction=auction, bidder=request.user, price=newBid).save()
    send_mail(
        'New bid has made',
        'Hi ' + auction.seller.username + '! There is a new bid in your auction ' + auction.title,
        'from@example.com',
        [auction.seller.email]
    )
    send_mail(
        'Your bid was made successfully',
        'Hi ' + request.user.username + '! Your bid to the auction ' + auction.title + ' is now saved.',
        'from@example.com',
        [request.user.email]
    )
    timeLeft = auction.deadline.date() - datetime.now().date()
    hoursLeft = auction.deadline.hour - datetime.now().hour
    minutesLeft = auction.deadline.minute - datetime.now().minute
    if timeLeft.days == 0 and hoursLeft == -3 and minutesLeft < 5:
        auction.deadline += timedelta(minutes=5)
    auction.highestBid = newBid
    auction.version += 1
    auction.save()


def bidIsValid(request, auction, newBid):
    if len(newBid.rsplit('.')[-1]) > 2:
        return False
    newBid = float(newBid)
    if newBid > auction.minPrice and newBid > auction.highestBid:
        return True
    else:
        return False


def userCanBid(request, auction):
    if auction.state == 'active':
        if thereAreBids(auction):
            if request.user.username == getHighestBid(auction).bidder.username:
                return False
        if request.user.username == auction.seller.username:
            return False
        return True
    else:
        return False

def getHighestBid(auction):
        bids = Bid.objects.filter(auction=auction)
        if len(bids) > 0:
            return bids[0]
        else:
            return 0

def thereAreBids(auction):
        return len(Bid.objects.filter(auction=auction)) != 0

def getAllBidders(auction):
    bids = Bid.objects.filter(auction=auction)
    if len(bids) > 0:
        bidders = []
        for bid in bids:
            bidders.append(User.objects.get(username=bid.bidder).email)
        return bidders
    else:
        return

def getUSDPrice(priceInEUR, currencyRate):
    priceInUSD = priceInEUR / currencyRate
    return priceInUSD

def getEURPrice(priceInUSD, currencyRate):
    priceInEUR = priceInUSD * currencyRate
    return priceInEUR


def getCurrencyRate():
    # response = requests.get("https://openexchangerates.org/api/latest.json?app_id=6438a59eedb743fea1710706c62f2edc")
    # data = response.json()
    # return data["rates"]["EUR"]
    return 1


@renderer_classes([JSONRenderer,])
class AuctionsView(generics.ListCreateAPIView):
    queryset = Auction.objects.filter(state='active')
    serializer_class = AuctionSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('title',)


@api_view(['GET'])
@renderer_classes([JSONRenderer,])
def auctionDetail(request, id):
    if request.method == 'GET':
        auction = get_object_or_404(Auction, id=id)
        serializer = AuctionSerializer(auction)
        return Response(serializer.data)


class BidAuction(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    @renderer_classes([JSONRenderer, ])
    def get(self, request, id):
        auction = get_object_or_404(Auction, id=id)
        serializer = AuctionSerializer(auction)
        if userCanBid(request, auction) and auction.state == 'active':
            return Response(serializer.data)
        else:
           return Response('You cannot make a bid to this auction because you already have the highest bid, '
                                      'or you are the seller of the auction or the auction is not active.')

    @renderer_classes([JSONRenderer, ])
    def post(self, request, id):
        auction = get_object_or_404(Auction, id=id)
        data = request.data
        newBid = request.data.get('highestBid')
        newBid = str(newBid)
        serializer = AuctionSerializer(auction, data=data)
        if serializer.is_valid():
            if bidIsValid(request, auction, newBid):
                serializer.save()
                newBid = float(newBid)
                makeBid(request, auction, newBid)
                return Response(serializer.data)
            else:
                return Response('Not valid bid.')
        else:
            return Response(serializer.errors, status=400)

@staff_member_required
def generateData(request):

    for i in range(1, 61):
        try:
            user = User.objects.get(username=str(i+100))
        except ObjectDoesNotExist:
            user = User.objects.create_user(username=str(i + 100), password=('klcvndih123'))
            user.save()

        deadline = '2019-01-01 12:00'
        auction = Auction(title=str(i), description=str(i), seller=user,
                          deadline=deadline, minPrice=i)
        auction.save()

        if i % 5 == 0:
            bidder = User.objects.get(username=str(i + 99))
            if getHighestBid(auction) != bidder:
                bid = Bid(auction=auction, bidder=bidder, price=i+1)
                bid.save()
                auction.highestBid = i+1
                auction.save()

    messages.add_message(request, messages.INFO, "60 auctions, 60 users and 12 bids are now generated.")
    return HttpResponseRedirect(reverse('home'))
