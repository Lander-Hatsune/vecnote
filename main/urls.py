from django.urls import path
from .views import *

urlpatterns = [
    path('', DocumentListView.as_view(), name='list'),
    path('create/', CreateDocumentView.as_view(), name='create'),
    path('detail/<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('backend/create/', create_document, name='backend-create'),
]