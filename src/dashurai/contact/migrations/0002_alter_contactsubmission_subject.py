from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactsubmission',
            name='subject',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
