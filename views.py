from typing import Final, Optional

from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from koro import BinSlot, XmlSlot

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
    return (
        HttpResponse(
            XmlSlot.serialize(target.stage_data),
            content_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="{slugify(target.name)}.xml"'
            },
        )
        if request.GET.get("xml", "false") == "true"
        else HttpResponse(
            BinSlot.serialize(target.stage_data),
            content_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{slugify(target.name)}.bin"'
            },
        )
    )


@login_required
def submit_stage(request: HttpRequest) -> HttpResponse:
    form: SubmitStageForm
    if request.method == "POST":
        form = SubmitStageForm(request.POST, request.FILES)
        if form.is_valid():
            file: Final[Optional[UploadedFile]] = form.files.get("stage_data")
            if file is not None:
                untyped_content: Final[str | bytes] = file.read()
                content: Final[bytes] = (
                    untyped_content.encode("shift_jis", "xmlcharrefreplace")
                    if isinstance(untyped_content, str)
                    else bytes(untyped_content)
                )
                new: Final[Submission] = Submission(
                    name=form.cleaned_data["name"],
                    stage_data=(XmlSlot if content[0] else BinSlot).deserialize(
                        content
                    ),
                    creator=request.user,
                    embed=form.cleaned_data["embed"],
                    description=form.cleaned_data["description"],
                    music=form.cleaned_data["music"],
                )
                new.save()
                return HttpResponseRedirect(f"/kororinpa/{new.id}")  # type: ignore[attr-defined]
    else:
        form = SubmitStageForm()
    return render(request, "kororinpa/new.html", {"form": form})
