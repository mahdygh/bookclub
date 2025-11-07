from django.db import migrations


def populate_assignment_fields(apps, schema_editor):
    BookAssignment = apps.get_model('books', 'BookAssignment')
    for assignment in BookAssignment.objects.select_related('book').all():
        book = assignment.book
        if book:
            assignment.reading_score_base = assignment.reading_score_base or book.reading_score
            assignment.quiz_score_base = assignment.quiz_score_base or book.quiz_score
            if assignment.is_completed and book.page_count and assignment.pages_read == 0:
                assignment.pages_read = book.page_count
        assignment.save(update_fields=['reading_score_base', 'quiz_score_base', 'pages_read'])


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0013_notification'),
    ]

    operations = [
        migrations.RunPython(populate_assignment_fields, migrations.RunPython.noop),
    ]

