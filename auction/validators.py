from django.utils import timezone
from django.core.exceptions import ValidationError


def checkAuctionDeadline(deadline):
    # minimum duration is 72h (259200 s) from the moment auction is created
    min = 259200
    duration = (deadline - timezone.now()).total_seconds()
    if duration < min:
        raise ValidationError('Deadline has to be at least 72 h from this moment.')