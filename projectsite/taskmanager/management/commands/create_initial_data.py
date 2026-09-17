from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from taskmanager.models import Task, Note, SubTask, Category, Priority


class Command(BaseCommand):
    help = "Generate fake Hangarin data"

    def handle(self, *args, **kwargs):
        fake = Faker()

        categories = list(Category.objects.all())
        priorities = list(Priority.objects.all())

        if not categories:
            self.stdout.write(
                self.style.ERROR(
                    "No categories found. Add the categories first."
                )
            )
            return

        if not priorities:
            self.stdout.write(
                self.style.ERROR(
                    "No priorities found. Add the priorities first."
                )
            )
            return

        for i in range(10):

            task = Task.objects.create(
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=3),
                status=fake.random_element(
                    elements=[
                        "Pending",
                        "In Progress",
                        "Completed"
                    ]
                ),
                deadline=timezone.make_aware(
                    fake.date_time_this_month()
                ),
                category=fake.random_element(categories),
                priority=fake.random_element(priorities)
            )

            Note.objects.create(
                task=task,
                content=fake.paragraph(nb_sentences=2)
            )

            for j in range(3):
                SubTask.objects.create(
                    parent_task=task,
                    title=fake.sentence(nb_words=5),
                    status=fake.random_element(
                        elements=[
                            "Pending",
                            "In Progress",
                            "Completed"
                        ]
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Fake Hangarin data generated successfully!"
            )
        )