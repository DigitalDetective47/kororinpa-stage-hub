from typing import Final

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from koro import BinSlot

from .forms import SubmitStageForm
from .models import Submission, music_choices, music_ytids


def view_stage(request: HttpRequest, pk: int) -> HttpResponse:
    target: Final[Submission] = get_object_or_404(Submission, id=pk)
    return render(
        request,
        "kororinpa_stage_hub/index.html",
        {
            "submission": target,
            "track_id": music_ytids[target.music - 1],
            "track_name": music_choices[target.music],
        },
    )


def download_stage(request: HttpRequest, pk: int) -> HttpResponse:
    target: Final[Submission] = get_object_or_404(Submission, id=pk)
    target.stage_data.open("rb")
    content: Final[bytes] = target.stage_data.read()
    ret: HttpResponse
    if request.GET.get("xml", "false") == "true":
        ret = HttpResponse(
            BinSlot.decompress(content),
            content_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="{slugify(target.name)}.xml"'
            },
        )
    else:
        ret = HttpResponse(
            content,
            content_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{slugify(target.name)}.bin"'
            },
        )
    target.stage_data.close()
    return ret


@login_required
def submit_stage(request: HttpRequest) -> HttpResponse:
    form: SubmitStageForm
    if request.method == "POST":
        form = SubmitStageForm(request.POST, request.FILES)
        if form.is_valid():
            new: Final[Submission] = form.save(False)
            new.creator = request.user
            new.save()
            return HttpResponseRedirect(f"/kororinpa/stage/{new.id}")  # type: ignore[attr-defined]
    else:
        form = SubmitStageForm()
    return render(request, "kororinpa_stage_hub/new.html", {"form": form})
