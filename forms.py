from django.forms import (
    CharField,
    ChoiceField,
    FileField,
    FileInput,
    Form,
    Textarea,
    URLField,
)

from .models import music_choices


class SubmitStageForm(Form):
    name: CharField = CharField(max_length=255)
    stage_data: FileField = FileField(widget=FileInput)
    embed: URLField = URLField(required=False, empty_value=None)
    description: CharField = CharField(widget=Textarea, required=False)
    music: ChoiceField = ChoiceField(initial=9, choices=music_choices)
