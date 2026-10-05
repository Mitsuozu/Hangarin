from django.urls import path

from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Tasks
    path("tasks/", views.TaskListView.as_view(scope="all"), name="task-list"),
    path("tasks/today/", views.TaskListView.as_view(scope="today"), name="task-today"),
    path("tasks/upcoming/", views.TaskListView.as_view(scope="upcoming"), name="task-upcoming"),
    path("tasks/completed/", views.TaskListView.as_view(scope="completed"), name="task-completed"),
    path("tasks/overdue/", views.TaskListView.as_view(scope="overdue"), name="task-overdue"),
    path("tasks/new/", views.TaskCreateView.as_view(), name="task-add"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task-edit"),
    path("tasks/<int:pk>/delete/", views.TaskDeleteView.as_view(), name="task-delete"),
    path("tasks/<int:pk>/toggle/", views.TaskToggleView.as_view(), name="task-toggle"),

    # Subtasks
    path("tasks/<int:task_pk>/subtasks/new/", views.SubTaskCreateView.as_view(), name="subtask-add"),
    path("subtasks/<int:pk>/edit/", views.SubTaskUpdateView.as_view(), name="subtask-edit"),
    path("subtasks/<int:pk>/delete/", views.SubTaskDeleteView.as_view(), name="subtask-delete"),
    path("subtasks/<int:pk>/toggle/", views.SubTaskToggleView.as_view(), name="subtask-toggle"),

    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category-add"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category-edit"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category-delete"),

    # Priorities
    path("priorities/", views.PriorityListView.as_view(), name="priority-list"),
    path("priorities/new/", views.PriorityCreateView.as_view(), name="priority-add"),
    path("priorities/<int:pk>/edit/", views.PriorityUpdateView.as_view(), name="priority-edit"),
    path("priorities/<int:pk>/delete/", views.PriorityDeleteView.as_view(), name="priority-delete"),

    # Notes
    path("notes/", views.NoteListView.as_view(), name="note-list"),
    path("notes/new/", views.NoteCreateView.as_view(), name="note-add"),
    path("notes/<int:pk>/edit/", views.NoteUpdateView.as_view(), name="note-edit"),
    path("notes/<int:pk>/delete/", views.NoteDeleteView.as_view(), name="note-delete"),

    path("settings/", views.SettingsView.as_view(), name="settings"),
    path("settings/profile/", views.ProfileUpdateView.as_view(), name="profile-edit"),
]
