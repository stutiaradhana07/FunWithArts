from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workshops', '0006_alter_booking_options_alter_booking_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='workshop',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workshops.workshop'),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_type',
            field=models.CharField(choices=[('workshop', 'Workshop'), ('home_tuition', 'Home Tuition')], default='workshop', max_length=20),
        ),
        migrations.AddField(
            model_name='booking',
            name='sessions',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='booking',
            name='customer_name',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='booking',
            name='customer_phone',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='booking',
            name='customer_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]