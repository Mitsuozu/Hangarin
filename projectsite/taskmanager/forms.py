from django import forms
from django.contrib.auth import get_user_model

from .models import Category, Note, Priority, SubTask, Task


class StyledFormMixin:
    """Adds Bootstrap classes to every widget and marks invalid fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                css = "form-select"
            elif isinstance(widget, forms.CheckboxInput):
                css = "form-check-input"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            for name in self.errors:
                if name in self.fields:
                    widget = self.fields[name].widget
                    widget.attrs["class"] = f"{widget.attrs.get('class', '')} is-invalid".strip()


class TaskForm(StyledFormMixin, forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
    )

    class Meta:
        model = Task
        fields = ["title", "description", "deadline", "status", "category", "priority"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "What needs to get done?", "autofocus": True}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Optional details"}),
        }


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"autofocus": True})}


class PriorityForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Priority
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"autofocus": True})}


class NoteForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Note
        fields = ["task", "content"]
        widgets = {"content": forms.Textarea(attrs={"rows": 5, "placeholder": "Write your note…"})}


class SubTaskForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ["title", "status"]
        widgets = {"title": forms.TextInput(attrs={"placeholder": "What is the small step?", "autofocus": True})}


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name"]
        labels = {"first_name": "First name", "last_name": "Last name"}
