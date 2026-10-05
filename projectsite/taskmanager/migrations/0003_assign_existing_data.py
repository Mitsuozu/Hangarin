from django.conf import settings
from django.db import migrations


def assign_owner(apps, schema_editor):
    """Existing data goes to the first admin account (or the first account)."""
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    owner = (
        User.objects.filter(is_superuser=True).order_by('id').first()
        or User.objects.order_by('id').first()
    )
    for name in ('Category', 'Priority', 'Task'):
        Model = apps.get_model('taskmanager', name)
        orphans = Model.objects.filter(owner__isnull=True)
        if owner is None:
            if orphans.exists():
                raise RuntimeError(
                    'Your data needs an owner but there are no users yet. '
                    'Run "python manage.py createsuperuser", then "python manage.py migrate" again.'
                )
            continue
        orphans.update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        ('taskmanager', '0002_owner_nullable'),
    ]

    operations = [
        migrations.RunPython(assign_owner, migrations.RunPython.noop),
    ]
