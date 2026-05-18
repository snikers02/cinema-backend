# Generated manually for ReactionStat (plugins.reactions)

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ReactionStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_id', models.UUIDField()),
                ('emoji', models.CharField(max_length=10)),
                ('count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'unique_together': {('room_id', 'emoji')},
            },
        ),
    ]
