from django.urls import path

from kanban_app.api.views import (
    AssignedTaskListView, BoardDetailView, BoardListCreateView,
    CommentDetailView, CommentListCreateView, EmailCheckView,
    ReviewingTaskListView, TaskCreateView, TaskDetailView,
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
    path(
        'tasks/<int:task_id>/comments/',
        CommentListCreateView.as_view(),
        name='comment-list',
    ),
    path(
        'tasks/<int:task_id>/comments/<int:pk>/',
        CommentDetailView.as_view(),
        name='comment-detail',
    ),
]
