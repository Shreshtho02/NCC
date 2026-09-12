from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_eventseg_subcategories'),
    ]

    operations = [
        migrations.DeleteModel(name='CampusAmbassador'),
        migrations.DeleteModel(name='CABatch'),
    ]
