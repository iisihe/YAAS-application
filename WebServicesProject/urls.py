"""WebServicesProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from auction.views import *

urlpatterns = [
    path('home/', archive, name="home"),
    path('search/', search, name='search'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('languageChange/', setLanguage, name='language_change'),

    path('registration/', Registration.as_view(), name="registration"),
    path('accounts/', include('django.contrib.auth.urls')),
    path('password/', ChangePassword.as_view(), name='change_password'),
    path('editprofile/', EditProfile.as_view(), name='change_email'),

    path('add/', AddAuction.as_view(), name="add_auction"),
    path('saveauction/', saveAuction, name="auction_confirm"),
    path('yourauctions/', yourAuctions, name="your_auctions"),
    path('edit/<int:id>/', EditAuction.as_view(), name="edit_auction"),
    path('edit/<uuid:uniqueId>/', EditAuctionLink.as_view(), name="edit_auction_link"),

    path('allauctions/', allAuctions, name='all_auctions'),
    path('banauction/<int:id>/', banAuction, name='ban_auction'),
    path('makeBid/<int:id>/', MakeBid.as_view(), name="bid_auction"),

    path('admin/', admin.site.urls),
    path('emailhistory/', emailhistory, name='email_history'),
    path('generatedata/', generateData, name='generate_data'),

    path('api/auctions/<int:id>/', auctionDetail),
    path('api/auctions/', AuctionsView.as_view()),
    path('api/bidauction/<int:id>/', BidAuction.as_view())
]
