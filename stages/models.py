from django.core import validators
from django.db import models

# Create your models here.
class Track(models.Model):
    """One of the game's available music selections."""
    __slots__ = ()

    title = models.CharField(max_length=32)
    ost_link = models.URLField(verbose_name="OST Link")

    def __str__(self) -> str:
        return self.title
