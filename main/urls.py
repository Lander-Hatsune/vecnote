from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("list/", views.DocumentListView.as_view(), name="list"),
    path("create/", views.CreateDocumentView.as_view(), name="create"),
    path("detail/<int:pk>/", views.DocumentDetailView.as_view(), name="detail"),
    path("edit/<int:pk>/", views.EditDocumentView.as_view(), name="edit"),
    path("delete/<int:pk>/", views.DeleteDocumentView.as_view(), name="delete"),
    path("restore/<int:pk>/", views.RestoreDocumentView.as_view(), name="restore"),
    path("pin/<int:pk>/", views.PinDocumentView.as_view(), name="pin"),
    path("unpin/<int:pk>/", views.UnpinDocumentView.as_view(), name="unpin"),
    path("trashbin/", views.TrashbinView.as_view(), name="trashbin"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("todos/", views.TodosView.as_view(), name="todos"),
    path("update_todo/<int:pk>", views.UpdateTodoItemView.as_view(), name="update_todo"),
]
