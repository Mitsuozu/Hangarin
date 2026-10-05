from django import forms, template

register = template.Library()


@register.filter
def as_bs(bound_field):
    """Render a form field with Bootstrap classes (adds is-invalid on errors)."""
    widget = bound_field.field.widget
    if isinstance(widget, forms.CheckboxInput):
        css = "form-check-input"
    elif isinstance(widget, forms.Select):
        css = "form-select"
    else:
        css = "form-control"
    if bound_field.errors:
        css += " is-invalid"
    existing = widget.attrs.get("class", "")
    return bound_field.as_widget(attrs={"class": f"{existing} {css}".strip()})
