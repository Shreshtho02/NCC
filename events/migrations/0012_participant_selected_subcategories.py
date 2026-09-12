from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0011_remove_campus_ambassador_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='selected_subcategories',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
