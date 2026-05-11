from typing import Final

from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
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
            "track_id": music_ytids[target.music],
            "track_name": music_choices[target.music],
            "edit_permission": request.user.is_authenticated
            and (
                target.creator == request.user
                or request.user.has_perm(  # type: ignore[attr-defined]
                    "kororinpa_stage_hub.change_submission"
                )
            ),
            "delete_permission": request.user.is_authenticated
            and (
                target.creator == request.user
                or request.user.has_perm(  # type: ignore[attr-defined]
                    "kororinpa_stage_hub.delete_submission"
                )
            ),
        },
    )


@login_required
def edit_stage(request: HttpRequest, pk: int) -> HttpResponse:
    target: Final[Submission] = get_object_or_404(Submission, id=pk)
    if (
        target.creator != request.user
        and not request.user.has_perm(  # type: ignore[union-attr]
            "kororinpa_stage_hub.change_submission"
        )
    ):
        return HttpResponseForbidden("You do not have permission to edit this stage")
    form: SubmitStageForm
    if request.method == "POST":
        form = SubmitStageForm(request.POST, request.FILES, instance=target)
        if form.is_valid():
            form.save(False)
            target.modified = True
            target.save()
            return HttpResponseRedirect(f"/kororinpa/stage/{target.id}")  # type: ignore[attr-defined]
    else:
        form = SubmitStageForm(instance=target)
    return render(
        request, "kororinpa_stage_hub/edit.html", {"form": form, "submission": target}
    )


@login_required
def delete_stage(request: HttpRequest, pk: int) -> HttpResponse:
    target: Final[Submission] = get_object_or_404(Submission, id=pk)
    if (
        target.creator != request.user
        and not request.user.has_perm(  # type: ignore[union-attr]
            "kororinpa_stage_hub.delete_submission"
        )
    ):
        return HttpResponseForbidden("You do not have permission to delete this stage")
    if request.method == "POST":
        ret: HttpResponse = render(
            request, "kororinpa_stage_hub/post_delete.html", {"name": target.name}
        )
        target.delete()
        return ret
    return render(request, "kororinpa_stage_hub/delete.html", {"submission": target})


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
