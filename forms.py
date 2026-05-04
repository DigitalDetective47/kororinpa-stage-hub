from django.forms import ModelForm

from .models import Submission


class SubmitStageForm(ModelForm):
    class Meta:
        model = Submission
        fields = ["name", "stage_data", "embed", "description", "music"]
