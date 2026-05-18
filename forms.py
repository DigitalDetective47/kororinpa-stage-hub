from django.contrib.auth.models import User
from django.forms import (
    BooleanField,
    CharField,
    ChoiceField,
    DateTimeField,
    Form,
    ModelChoiceField,
    ModelForm,
    RadioSelect,
)

from .models import Submission


class SubmitStageForm(ModelForm):
    class Meta:
        model = Submission
        fields = ["name", "stage_data", "embed", "description", "music"]


class SearchStageForm(Form):
    name: CharField = CharField(strip=False, required=False)
    match: ChoiceField = ChoiceField(
        choices={
            "phrase": "Search for entire phrase",
            "all": "Search for all terms",
            "any": "Search for any terms",
            "regex": "Treat query as regex",
        },
        widget=RadioSelect,
        initial="phrase",
    )
    case_sensetive: BooleanField = BooleanField(required=False)
    released_after: DateTimeField = DateTimeField(required=False)
    released_before: DateTimeField = DateTimeField(required=False)
    updated_after: DateTimeField = DateTimeField(required=False)
    updated_before: DateTimeField = DateTimeField(required=False)
    creator: ModelChoiceField = ModelChoiceField(
        queryset=User.objects.order_by("username"), required=False
    )
    sort: ChoiceField = ChoiceField(
        choices={
            "name": "Sort by name",
            "released": "Sort by release date",
            "updated": "Sort by update date",
            "creator__username": "Sort by creator username",
        },
        widget=RadioSelect,
        initial="updated",
    )
    sort_direction: ChoiceField = ChoiceField(
        choices={"asc": "Ascending", "desc": "Descending"},
        widget=RadioSelect,
        initial="desc",
    )
