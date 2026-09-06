from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_exchangerequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangerequest',
            name='amount_to_pay',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Price difference to be paid if replacement item is more expensive.', max_digits=10),
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='payment_status',
            field=models.CharField(choices=[('not_required', 'Not Required'), ('pending', 'Pending Payment'), ('paid', 'Paid')], db_index=True, default='not_required', max_length=20),
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='exchangerequest',
            name='razorpay_signature',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
