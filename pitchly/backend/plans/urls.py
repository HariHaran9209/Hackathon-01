from django.urls import path
from . import views

urlpatterns = [
    # Projects
    path('projects/', views.ProjectListCreateView.as_view(), name='project-list-create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<int:pk>/chat/', views.project_chat, name='project-chat'),
    path('projects/<int:pk>/readme/', views.project_readme, name='project-readme'),
    path('projects/<int:project_id>/tasks/', views.TaskCreateView.as_view(), name='project-task-create'),

    # Tasks
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),

    # Suggestions
    path('suggestions/<int:pk>/accept/', views.accept_suggestion, name='suggestion-accept'),
    path('suggestions/<int:pk>/reject/', views.reject_suggestion, name='suggestion-reject'),
]
