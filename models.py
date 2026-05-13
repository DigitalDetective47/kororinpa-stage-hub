from collections.abc import Iterator, Mapping, Sequence
from csv import DictReader
from itertools import tee
from typing import Any, Final

from django.contrib.auth.models import User
from django.db.models import (
    RESTRICT,
    CharField,
    CheckConstraint,
    DateTimeField,
    F,
    FileField,
    ForeignKey,
    Model,
    PositiveSmallIntegerField,
    Q,
    TextField,
    URLField,
)
from django.db.models.functions import Now
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from koro import BinSlot

with open("kororinpa_stage_hub/music.csv", newline="") as f:
    readers: Final[
        tuple[Iterator[Mapping[str, str]], Iterator[Mapping[str, str]]]
    ] = tee(
        DictReader(f)
    )  # type: ignore[assignment]
    music_choices: Final[Mapping[int, str]] = {
        i: row["Title"] for i, row in enumerate(readers[0])
    }
    music_ytids: Final[Sequence[str]] = tuple(
        row["YouTube Video ID"] for row in readers[1]
    )


class Submission(Model):
    name: CharField = CharField(max_length=255)
    stage_data: FileField = FileField()
    creator: ForeignKey = ForeignKey(User, on_delete=RESTRICT)
    released: DateTimeField = DateTimeField(default=Now(), db_default=Now())
    updated: DateTimeField = DateTimeField(default=Now(), db_default=Now())
    embed: URLField = URLField(blank=True, null=True)
    description: TextField = TextField(blank=True)
    music: PositiveSmallIntegerField = PositiveSmallIntegerField(
        default=8, db_default=8, choices=music_choices
    )

    class Meta:
        constraints = [
            CheckConstraint(
                name="updated_after_released", condition=Q(updated__gte=F("released"))
            ),
            CheckConstraint(
                name="music_in_range", condition=Q(music__lt=len(music_choices))
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("kororinpa_stage_hub:view_stage", kwargs={"pk": self.pk})


@receiver(pre_save, sender=Submission)
def set_dates(sender: Any, instance: Submission, **kwargs: Any) -> None:
    instance.updated = Now()


@receiver(post_save, sender=Submission)
def fix_xmls(sender: Any, instance: Submission, **kwargs: Any) -> None:
    instance.stage_data.open("rb")
    if instance.stage_data.read(1)[0]:
        instance.stage_data.open("rb")
        compressed: bytes = BinSlot.compress(instance.stage_data.read())
        instance.stage_data.open("wb")
        instance.stage_data.write(compressed)
    instance.stage_data.close()
