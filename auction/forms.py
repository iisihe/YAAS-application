from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .validators import checkAuctionDeadline


class AddAuctionForm(forms.Form):

    title = forms.CharField()
    description = forms.CharField(widget=forms.Textarea())
    minPrice = forms.FloatField(localize=True, min_value=0)
    deadline = forms.DateTimeField(required=True, input_formats=['%d.%m.%Y %H:%M'], validators=[checkAuctionDeadline], help_text=_("Date format: dd.mm.yyy hh:mm"))


class ConfAuctionForm(forms.Form):
    CHOICES = [(x, x) for x in ("Yes", "No")]
    option = forms.ChoiceField(choices=CHOICES)
    auction_title = forms.CharField(widget=forms.HiddenInput())
    auction_description = forms.CharField(widget=forms.HiddenInput())
    auction_minprice = forms.FloatField(widget=forms.HiddenInput())
    auction_deadline = forms.DateTimeField(widget=forms.HiddenInput())


class CreateUserForm(UserCreationForm):

    email = forms.EmailField(label=("Email address"), required=True,
        help_text=_("Required."))
    siteLanguages = (('en', 'English'), ('fi', 'Finnish'))
    # first_name used for saving language preference
    first_name = forms.ChoiceField(choices=siteLanguages, label="Language")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "first_name")


class EditProfileForm(UserChangeForm):

    CHOICES = [(x, x) for x in ("en", "fi")]
    first_name = forms.ChoiceField(choices=CHOICES, label=("Language"), required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name")