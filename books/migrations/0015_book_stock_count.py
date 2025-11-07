from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0014_populate_assignment_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='stock_count',
            field=models.PositiveIntegerField(default=1, verbose_name='تعداد نسخه'),
        ),
    ]
