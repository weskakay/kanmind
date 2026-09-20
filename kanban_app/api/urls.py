from django.urls import path

from kanban_app.api.task_views import (
    AssignedTaskListView, ReviewingTaskListView, TaskCreateView,
    TaskDetailView,
)
from kanban_app.api.views import (
    BoardDetailView, BoardListCreateView, EmailCheckView,
)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list'),
    path('boards/<int:pk>/', BoardDetailView.as_view(), name='board-detail'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
    path('tasks/', TaskCreateView.as_view(), name='task-create'),
    path(
        'tasks/assigned-to-me/',
        AssignedTaskListView.as_view(),
        name='task-assigned',
    ),
    path(
        'tasks/reviewing/',
        ReviewingTaskListView.as_view(),
        name='task-reviewing',
    ),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
]
