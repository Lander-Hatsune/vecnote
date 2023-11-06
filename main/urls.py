from django.urls import path
from .views import *

urlpatterns = [
    path('', DocumentListView.as_view(), name='list'),
    path('create/', CreateDocumentView.as_view(), name='create'),
    path('detail/<int:pk>/', DocumentDetailView.as_view(), name='detail'),
    path('edit/<int:pk>/', EditDocumentView.as_view(), name='edit'),
]