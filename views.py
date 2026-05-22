from functools import reduce
from operator import and_, or_
from typing import Final, cast

from django.contrib.auth.decorators import login_required
from django.db.models import Case, F, Q, QuerySet, When
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from koro import BinSlot

from .forms import SearchStageForm, SubmitStageForm
from .models import Submission, music_choices, music_ytids


@require_http_methods({"GET", "HEAD", "DELETE"})
def view_stage(request: HttpRequest, pk: int) -> HttpResponse:
    target: Final[Submission] = get_object_or_404(Submission, id=pk)
    match request.method:
        case "GET" | "HEAD":
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
        case "DELETE":

            @login_required
            def delete_req(irequest: HttpRequest) -> HttpResponse:
                if (
                    target.creator != irequest.user
                    and not irequest.user.has_perm(  # type: ignore[union-attr]
                        "kororinpa_stage_hub.delete_submission"
                    )
                ):
                    return HttpResponseForbidden(
                        "You must be the owner of this stage or an administrator to delete it"
                    )
                ret: HttpResponse = render(
                    irequest,
                    "kororinpa_stage_hub/post_delete.html",
                    {"name": target.name},
                )
                target.delete()
                return ret

            return delete_req(request)
        case _:
            raise ValueError("invalid request method")


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
            form.save()
            return HttpResponseRedirect(
                reverse("kororinpa_stage_hub:view_stage", kwargs={"pk": target.pk})
            )
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
        return HttpResponseForbidden(
            "You must be the owner of this stage or an administrator to delete it"
        )
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
            ret: HttpResponseRedirect = HttpResponseRedirect(
                reverse("kororinpa_stage_hub:view_stage", kwargs={"pk": new.pk})
            )
            ret.status_code = 303
            return ret
    else:
        form = SubmitStageForm()
    return render(request, "kororinpa_stage_hub/new.html", {"form": form})


def search_stage(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "kororinpa_stage_hub/search.html",
        {"form": SearchStageForm(request.GET or None)},
    )


def search_results_stage(request: HttpRequest) -> HttpResponse:
    form: Final[SearchStageForm] = SearchStageForm(request.GET)
    if not form.is_valid():
        return HttpResponseRedirect(
            reverse("kororinpa_stage_hub:search_stage", query=request.GET)
        )
    query: QuerySet = Submission.objects.order_by(
        ("-" if form.cleaned_data["sort_direction"] == "desc" else "")
        + form.cleaned_data["sort"]
    )
    if form.cleaned_data["released_after"] is not None:
        query = query.filter(released__gt=form.cleaned_data["released_after"])
    if form.cleaned_data["released_before"] is not None:
        query = query.filter(released__lt=form.cleaned_data["released_before"])
    if form.cleaned_data["updated_after"] is not None:
        query = query.filter(updated__gt=form.cleaned_data["updated_after"])
    if form.cleaned_data["updated_before"] is not None:
        query = query.filter(updated__lt=form.cleaned_data["updated_before"])
    if form.cleaned_data["creator"] is not None:
        query = query.filter(creator=form.cleaned_data["creator"])
    if form.cleaned_data["name"]:
        if form.cleaned_data["case_sensetive"]:
            match form.cleaned_data["match"]:
                case "phrase":
                    query = query.filter(name__contains=form.cleaned_data["name"])
                case "all":
                    query = query.filter(
                        reduce(
                            and_,
                            (
                                Q(name__contains=word)
                                for word in cast(str, form.cleaned_data["name"]).split()
                            ),
                        )
                    )
                case "any":
                    query = query.filter(
                        reduce(
                            or_,
                            (
                                Q(name__contains=word)
                                for word in cast(str, form.cleaned_data["name"]).split()
                            ),
                        )
                    )
                case "regex":
                    query = query.filter(name__regex=form.cleaned_data["name"])
        else:
            match form.cleaned_data["match"]:
                case "phrase":
                    query = query.filter(name__icontains=form.cleaned_data["name"])
                case "all":
                    query = query.filter(
                        reduce(
                            and_,
                            (
                                Q(name__icontains=word)
                                for word in cast(str, form.cleaned_data["name"]).split()
                            ),
                        )
                    )
                case "any":
                    query = query.filter(
                        reduce(
                            or_,
                            (
                                Q(name__icontains=word)
                                for word in cast(str, form.cleaned_data["name"]).split()
                            ),
                        )
                    )
                case "regex":
                    query = query.filter(name__iregex=form.cleaned_data["name"])
    return render(
        request,
        "kororinpa_stage_hub/search_results.html",
        {
            "query": request.GET.urlencode,
            "results": query.values(
                "id",
                "name",
                "released",
                username=F("creator__username"),
                updated_if_unique=Case(When(~Q(updated=F("released")), F("updated"))),
            ),
        },
    )
