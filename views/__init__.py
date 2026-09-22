from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ..models import Stage


def home(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "kororinpa_stage_hub/home.html",
        {
            "stage_count": Stage.objects.count(),
            "stage_author_count": Stage.objects.values("creator").distinct().count(),
        },
    )
