from django.db import migrations, models


def populate_pages_read(apps, schema_editor):
    BookAssignment = apps.get_model('books', 'BookAssignment')
    for assignment in BookAssignment.objects.select_related('book').all():
        if assignment.is_completed and assignment.book and assignment.book.page_count:
            assignment.pages_read = assignment.book.page_count
        else:
            assignment.pages_read = 0
        assignment.save(update_fields=['pages_read'])


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0010_book_page_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookassignment',
            name='pages_read',
            field=models.PositiveIntegerField(default=0, verbose_name='تعداد صفحات مطالعه شده'),
        ),
        migrations.RunPython(populate_pages_read, migrations.RunPython.noop),
    ]

