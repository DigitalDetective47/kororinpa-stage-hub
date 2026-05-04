from collections.abc import Iterator, Mapping, Sequence
from csv import DictReader
from itertools import tee
from typing import Final

from django.contrib.auth.models import User
from django.db.models import (
    RESTRICT,
    BooleanField,
    CharField,
    CheckConstraint,
    DateTimeField,
    F,
    ForeignKey,
    Model,
    PositiveSmallIntegerField,
    Q,
    TextField,
    URLField,
)

from .fields import StageField

with open("kororinpa_stage_hub/music.csv", newline="") as f:
    readers: Final[
        tuple[Iterator[Mapping[str, str]], Iterator[Mapping[str, str]]]
    ] = tee(
        DictReader(f)
    )  # type: ignore[assignment]
    music_choices: Final[Mapping[int, str]] = {
        i: row["Title"] for i, row in enumerate(readers[0], 1)
    }
    music_ytids: Final[Sequence[str]] = tuple(
        row["YouTube Video ID"] for row in readers[1]
    )


class Submission(Model):
    name: CharField = CharField(max_length=255)
    stage_data: StageField = StageField()
    creator: ForeignKey = ForeignKey(User, on_delete=RESTRICT)
    released: DateTimeField = DateTimeField(auto_now_add=True)
    updated: DateTimeField = DateTimeField(auto_now=True)
    modified: BooleanField = BooleanField(default=False)
    embed: URLField = URLField(blank=True, null=True)
    description: TextField = TextField(blank=True)
    music: PositiveSmallIntegerField = PositiveSmallIntegerField(
        default=9, choices=music_choices
    )

    class Meta:
        constraints = [
            CheckConstraint(
                name="updated_after_released", condition=Q(updated__gte=F("released"))
            ),
            CheckConstraint(
                name="music_in_range",
                condition=Q(music__gt=0, music__lte=len(music_choices)),
            ),
        ]

    def __str__(self) -> str:
        return self.name
