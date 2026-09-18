from django.urls import path

from .views import stage

app_name = "kororinpa_stage_hub"
urlpatterns = [
    path("stage/<int:pk>", stage.view, name="stage/view"),
    path("stage/<int:pk>/edit", stage.edit, name="stage/edit"),
    path("stage/<int:pk>/delete", stage.delete, name="stage/delete"),
    path("stage/<int:pk>/download", stage.download, name="stage/download"),
    path("stages/new", stage.submit, name="stage/submit"),
    path("stages/search", stage.search, name="stage/search"),
    path(
        "stages/search_results", stage.search_results, name="stage/search_results"
    ),
]
