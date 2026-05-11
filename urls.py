from django.urls import path

from .views import delete_stage, download_stage, edit_stage, submit_stage, view_stage

app_name = "kororinpa_stage_hub"
urlpatterns = [
    path("stage/<int:pk>", view_stage, name="view_stage"),
    path("stage/<int:pk>/edit", edit_stage, name="edit_stage"),
    path("stage/<int:pk>/delete", delete_stage, name="delete_stage"),
    path("stage/<int:pk>/download", download_stage, name="download_stage"),
    path("stages/new", submit_stage, name="submit_stage"),
]
