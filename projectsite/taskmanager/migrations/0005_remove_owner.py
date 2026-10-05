from django.db import migrations


class Migration(migrations.Migration):
    """Back to the course ERD: tasks, categories and priorities have no owner."""

    dependencies = [
        ('taskmanager', '0004_owner_required'),
    ]

    operations = [
        migrations.RemoveField(model_name=model, name='owner')
        for model in ('category', 'priority', 'task')
    ]
