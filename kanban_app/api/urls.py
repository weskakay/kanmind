from django.urls import path

from kanban_app.api.views import (
    BoardDetailView, BoardListCreateView, EmailCheckView,
)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list'),
    path('boards/<int:pk>/', BoardDetailView.as_view(), name='board-detail'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]
