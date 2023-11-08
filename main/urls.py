from django.urls import path
from . import views

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="list"),
    path("create/", views.CreateDocumentView.as_view(), name="create"),
    path("detail/<int:pk>/", views.DocumentDetailView.as_view(), name="detail"),
    path("edit/<int:pk>/", views.EditDocumentView.as_view(), name="edit"),
    path("delete/<int:pk>/", views.DeleteDocumentView.as_view(), name="delete"),
    path("restore/<int:pk>/", views.RestoreDocumentView.as_view(), name="restore"),
    path("trashbin/", views.TrashbinView.as_view(), name="trashbin"),
    path("search/", views.SearchView.as_view(), name="search"),
]
