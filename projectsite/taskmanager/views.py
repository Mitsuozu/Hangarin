from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from .forms import CategoryForm, NoteForm, PriorityForm, ProfileForm, SubTaskForm, TaskForm
from .models import STATUS_CHOICES, Category, Note, Priority, SubTask, Task
from .profile import profile_for

STATUS_VALUES = [value for value, _label in STATUS_CHOICES]

SORT_OPTIONS = {
    "deadline": ("deadline", "Deadline: soonest first"),
    "-deadline": ("-deadline", "Deadline: latest first"),
    "newest": ("-created_at", "Recently created"),
    "oldest": ("created_at", "Oldest created"),
}

SCOPES = {
    "all": ("My Tasks", "Every task in one place."),
    "today": ("Today's Tasks", "Everything due today."),
    "upcoming": ("Upcoming Tasks", "What is coming up after today."),
    "completed": ("Completed Tasks", "Nice work. Here is what you finished."),
    "overdue": ("Overdue Tasks", "These deadlines have already passed."),
}


def with_subtask_counts(qs):
    """Adds subtask_total / subtask_done to each task."""
    return qs.annotate(
        subtask_total=Count("subtask", distinct=True),
        subtask_done=Count("subtask", filter=Q(subtask__status="Completed"), distinct=True),
    )


def safe_next(request, fallback):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect(fallback)


def greeting_for(user):
    hour = timezone.localtime().hour
    if hour < 12:
        part = "Good morning"
    elif hour < 18:
        part = "Good afternoon"
    else:
        part = "Good evening"
    name = ""
    if user.is_authenticated:
        name = profile_for(user)["first_name"]
    return f"{part}, {name}" if name else part


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "hangarin/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        mine = Task.objects.all()

        stats = mine.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="Pending")),
            in_progress=Count("id", filter=Q(status="In Progress")),
            completed=Count("id", filter=Q(status="Completed")),
        )
        total = stats["total"]

        def percent(value):
            return round(value * 100 / total) if total else 0

        status_counts = {
            "Pending": stats["pending"],
            "In Progress": stats["in_progress"],
            "Completed": stats["completed"],
        }
        status_breakdown = [
            {"label": label, "count": status_counts[value], "percent": percent(status_counts[value])}
            for value, label in STATUS_CHOICES
        ]
        priority_breakdown = [
            {"name": p.name, "count": p.task_count, "percent": percent(p.task_count)}
            for p in Priority.objects.annotate(task_count=Count("task")).order_by("-task_count", "name")
        ]

        open_tasks = mine.exclude(status="Completed").select_related("category", "priority")

        context.update(
            {
                "active_nav": "dashboard",
                "page_title": "Dashboard",
                "greeting": greeting_for(self.request.user),
                "stats": stats,
                "completion_percent": percent(stats["completed"]),
                "status_breakdown": status_breakdown,
                "priority_breakdown": priority_breakdown,
                "upcoming_deadlines": open_tasks.filter(deadline__date__gte=today).order_by("deadline")[:6],
                "recent_tasks": with_subtask_counts(mine.select_related("category", "priority")).order_by("-created_at")[:5],
            }
        )
        return context


class TaskListView(LoginRequiredMixin, ListView):
    """One list view powers My / Today's / Upcoming / Completed / Overdue."""

    model = Task
    template_name = "hangarin/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10
    scope = "all"

    def get_queryset(self):
        qs = with_subtask_counts(Task.objects.select_related("category", "priority"))
        today = timezone.localdate()

        if self.scope == "today":
            qs = qs.filter(deadline__date=today)
        elif self.scope == "upcoming":
            qs = qs.filter(deadline__date__gt=today).exclude(status="Completed")
        elif self.scope == "completed":
            qs = qs.filter(status="Completed")
        elif self.scope == "overdue":
            qs = qs.filter(deadline__lt=timezone.now()).exclude(status="Completed")

        params = self.request.GET
        query = params.get("q", "").strip()
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

        status = params.get("status")
        if status in STATUS_VALUES:
            qs = qs.filter(status=status)

        category = params.get("category", "")
        if category.isdigit():
            qs = qs.filter(category_id=category)

        priority = params.get("priority", "")
        if priority.isdigit():
            qs = qs.filter(priority_id=priority)

        ordering = SORT_OPTIONS.get(params.get("sort"), SORT_OPTIONS["deadline"])[0]
        return qs.order_by(ordering, "pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title, subtitle = SCOPES[self.scope]

        params = self.request.GET.copy()
        params.pop("page", None)

        context.update(
            {
                "scope": self.scope,
                "active_nav": self.scope,
                "page_title": title,
                "page_subtitle": subtitle,
                "categories": Category.objects.order_by("name"),
                "priorities": Priority.objects.order_by("name"),
                "status_choices": STATUS_CHOICES,
                "sort_options": [(key, value[1]) for key, value in SORT_OPTIONS.items()],
                "query_string": params.urlencode(),
                "filters_active": any(params.get(k) for k in ("q", "status", "category", "priority", "sort")),
            }
        )
        return context


class TaskToggleView(LoginRequiredMixin, View):
    """Checkbox on a task: Completed <-> Pending."""

    http_method_names = ["post"]

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task.status = "Pending" if task.status == "Completed" else "Completed"
        task.save(update_fields=["status", "updated_at"])

        next_url = request.POST.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect("task-list")


class PageMixin(LoginRequiredMixin):
    """Login required + page_title / active_nav for the layout."""

    active_nav = ""
    page_title = ""
    page_subtitle = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("active_nav", self.active_nav)
        context.setdefault("page_title", self.page_title)
        context.setdefault("page_subtitle", self.page_subtitle)
        return context


class DeleteMessageMixin:
    """Confirm page context + a success message for DeleteView."""

    template_name = "hangarin/confirm_delete.html"
    object_label = ""
    cancel_url_name = ""
    related = ()  

    def get_cancel_url(self):
        return reverse(self.cancel_url_name)

    def get_warning(self):
        parts = []
        for manager, word in self.related:
            count = getattr(self.object, manager).count()
            if count:
                parts.append(f"{count} {word}{'s' if count != 1 else ''}")
        if not parts:
            return ""
        return "This will also permanently delete " + " and ".join(parts) + "."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            object_label=self.object_label,
            cancel_url=self.get_cancel_url(),
            warning=self.get_warning(),
        )
        return context

    def form_valid(self, form):
        name = str(self.object)
        response = super().form_valid(form)
        messages.success(self.request, f"Deleted \u201c{name}\u201d.")
        return response


class TaskDetailView(PageMixin, DetailView):
    model = Task
    template_name = "hangarin/task_detail.html"
    active_nav = "all"

    def get_queryset(self):
        return Task.objects.select_related("category", "priority")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        context["page_title"] = task.title
        context["notes"] = task.note_set.order_by("-created_at")
        subtasks = list(task.subtask_set.order_by("created_at"))
        done = sum(1 for sub in subtasks if sub.status == "Completed")
        context["subtasks"] = subtasks
        context["subtask_done"] = done
        context["subtask_percent"] = round(done * 100 / len(subtasks)) if subtasks else 0
        return context


class TaskFormMixin(PageMixin, SuccessMessageMixin):
    model = Task
    form_class = TaskForm
    template_name = "hangarin/form_page.html"
    active_nav = "all"
    submit_label = "Save task"

    def get_success_url(self):
        return reverse("task-detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            submit_label=self.submit_label,
            no_categories=not Category.objects.exists(),
            no_priorities=not Priority.objects.exists(),
        )
        return context


class TaskCreateView(TaskFormMixin, CreateView):
    page_title = "New task"
    success_message = "Task created."
    submit_label = "Create task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(form_title="Create a task", cancel_url=reverse("task-list"))
        return context


class TaskUpdateView(TaskFormMixin, UpdateView):
    page_title = "Edit task"
    success_message = "Task updated."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(form_title="Edit task", cancel_url=reverse("task-detail", args=[self.object.pk]))
        return context


class TaskDeleteView(PageMixin, DeleteMessageMixin, DeleteView):
    model = Task
    page_title = "Delete task"
    active_nav = "all"
    object_label = "task"
    cancel_url_name = "task-list"
    related = (("note_set", "note"), ("subtask_set", "subtask"))

    def get_success_url(self):
        return reverse("task-list")

    def get_cancel_url(self):
        return reverse("task-detail", args=[self.object.pk])




CATEGORY_META = {
    "singular": "Category", "plural": "Categories", "nav": "categories", "icon": "i-tag",
    "list_name": "category-list", "add_name": "category-add",
    "edit_name": "category-edit", "delete_name": "category-delete",
    "filter_param": "category",
    "blurb": "Group your tasks, like Work, School or Personal.",
}
PRIORITY_META = {
    "singular": "Priority", "plural": "Priorities", "nav": "priorities", "icon": "i-flag",
    "list_name": "priority-list", "add_name": "priority-add",
    "edit_name": "priority-edit", "delete_name": "priority-delete",
    "filter_param": "priority",
    "blurb": "Levels that show how urgent a task is, like High, Medium or Low.",
}


class NamedListView(PageMixin, ListView):
    template_name = "hangarin/named_list.html"
    context_object_name = "items"
    paginate_by = 20
    meta = {}

    def get_queryset(self):
        return (
            self.model.objects.annotate(task_count=Count("task"))
            .order_by("name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(meta=self.meta, active_nav=self.meta["nav"], page_title=self.meta["plural"])
        return context


class NamedFormMixin(PageMixin, SuccessMessageMixin):
    template_name = "hangarin/form_page.html"
    meta = {}
    verb = ""

    def get_success_url(self):
        return reverse(self.meta["list_name"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = f"{self.verb} {self.meta['singular'].lower()}"
        context.update(
            active_nav=self.meta["nav"], page_title=title, form_title=title,
            cancel_url=reverse(self.meta["list_name"]), submit_label="Save",
        )
        return context


class NamedDeleteView(PageMixin, DeleteMessageMixin, DeleteView):
    meta = {}
    related = (("task_set", "task"),)

    def get_success_url(self):
        return reverse(self.meta["list_name"])

    def get_cancel_url(self):
        return reverse(self.meta["list_name"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(active_nav=self.meta["nav"], page_title=f"Delete {self.meta['singular'].lower()}")
        return context


class CategoryListView(NamedListView):
    model = Category
    meta = CATEGORY_META


class CategoryCreateView(NamedFormMixin, CreateView):
    model = Category
    form_class = CategoryForm
    meta = CATEGORY_META
    verb = "New"
    success_message = "Category created."


class CategoryUpdateView(NamedFormMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    meta = CATEGORY_META
    verb = "Edit"
    success_message = "Category updated."


class CategoryDeleteView(NamedDeleteView):
    model = Category
    meta = CATEGORY_META
    object_label = "category"


class PriorityListView(NamedListView):
    model = Priority
    meta = PRIORITY_META


class PriorityCreateView(NamedFormMixin, CreateView):
    model = Priority
    form_class = PriorityForm
    meta = PRIORITY_META
    verb = "New"
    success_message = "Priority created."


class PriorityUpdateView(NamedFormMixin, UpdateView):
    model = Priority
    form_class = PriorityForm
    meta = PRIORITY_META
    verb = "Edit"
    success_message = "Priority updated."


class PriorityDeleteView(NamedDeleteView):
    model = Priority
    meta = PRIORITY_META
    object_label = "priority"


class SubTaskCreateView(PageMixin, SuccessMessageMixin, CreateView):
    model = SubTask
    form_class = SubTaskForm
    template_name = "hangarin/form_page.html"
    active_nav = "all"
    page_title = "New subtask"
    success_message = "Subtask added."

    @cached_property
    def task(self):
        return get_object_or_404(Task, pk=self.kwargs["task_pk"])

    def form_valid(self, form):
        form.instance.parent_task = self.task
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("task-detail", args=[self.task.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_title=f"Add a subtask to \u201c{self.task.title}\u201d",
            cancel_url=reverse("task-detail", args=[self.task.pk]),
            submit_label="Add subtask",
        )
        return context


class SubTaskUpdateView(PageMixin, SuccessMessageMixin, UpdateView):
    model = SubTask
    form_class = SubTaskForm
    template_name = "hangarin/form_page.html"
    active_nav = "all"
    page_title = "Edit subtask"
    success_message = "Subtask updated."

    def get_success_url(self):
        return reverse("task-detail", args=[self.object.parent_task_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_title="Edit subtask",
            cancel_url=reverse("task-detail", args=[self.object.parent_task_id]),
            submit_label="Save subtask",
        )
        return context


class SubTaskDeleteView(PageMixin, DeleteMessageMixin, DeleteView):
    model = SubTask
    active_nav = "all"
    page_title = "Delete subtask"
    object_label = "subtask"

    def get_success_url(self):
        return reverse("task-detail", args=[self.object.parent_task_id])

    def get_cancel_url(self):
        return self.get_success_url()


class SubTaskToggleView(LoginRequiredMixin, View):
    """Checkbox on a subtask: Completed <-> Pending."""

    http_method_names = ["post"]

    def post(self, request, pk):
        sub = get_object_or_404(SubTask, pk=pk)
        sub.status = "Pending" if sub.status == "Completed" else "Completed"
        sub.save(update_fields=["status", "updated_at"])
        return safe_next(request, reverse("task-detail", args=[sub.parent_task_id]))



class NoteListView(PageMixin, ListView):
    model = Note
    template_name = "hangarin/note_list.html"
    context_object_name = "notes"
    paginate_by = 10
    active_nav = "notes"
    page_title = "Notes"
    page_subtitle = "Everything you have written down about your tasks."

    def get_queryset(self):
        qs = Note.objects.select_related("task").order_by("-created_at")
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(Q(content__icontains=query) | Q(task__title__icontains=query))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["query_string"] = params.urlencode()
        return context


class NoteFormMixin(PageMixin, SuccessMessageMixin):
    model = Note
    form_class = NoteForm
    template_name = "hangarin/form_page.html"
    active_nav = "notes"

    def _from_task(self):
        value = self.request.GET.get("task", "")
        return value if value.isdigit() else ""

    def get_success_url(self):
        task_id = self._from_task()
        if task_id:
            return reverse("task-detail", args=[task_id])
        return reverse("note-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = self._from_task()
        context.update(
            submit_label="Save note",
            cancel_url=reverse("task-detail", args=[task_id]) if task_id else reverse("note-list"),
            no_tasks=not Task.objects.exists(),
        )
        return context


class NoteCreateView(NoteFormMixin, CreateView):
    page_title = "New note"
    success_message = "Note added."

    def get_initial(self):
        initial = super().get_initial()
        task_id = self._from_task()
        if task_id:
            initial["task"] = task_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Add a note"
        return context


class NoteUpdateView(NoteFormMixin, UpdateView):
    page_title = "Edit note"
    success_message = "Note updated."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit note"
        return context


class NoteDeleteView(PageMixin, DeleteMessageMixin, DeleteView):
    model = Note
    page_title = "Delete note"
    active_nav = "notes"
    object_label = "note"
    cancel_url_name = "note-list"

    def get_success_url(self):
        return reverse("note-list")




class SettingsView(PageMixin, TemplateView):
    template_name = "hangarin/settings.html"
    active_nav = "settings"
    page_title = "Settings"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["counts"] = [
            ("Tasks", Task.objects.count()),
            ("Subtasks", SubTask.objects.count()),
            ("Categories", Category.objects.count()),
            ("Priorities", Priority.objects.count()),
            ("Notes", Note.objects.count()),
        ]
        return context


class ProfileUpdateView(PageMixin, SuccessMessageMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileForm
    template_name = "hangarin/form_page.html"
    active_nav = "settings"
    page_title = "Edit name"
    success_message = "Your name was updated."

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("settings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(form_title="Edit your name", cancel_url=reverse("settings"), submit_label="Save")
        return context
