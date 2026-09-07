# Generated manually because the project did not yet have order follow-up migrations.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("commerce", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="shipping_address",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="order",
            name="coupon",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="commerce.coupon"),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_status",
            field=models.CharField(choices=[("INITIATED", "Initiated"), ("SUCCESS", "Success"), ("FAILED", "Failed")], default="INITIATED", max_length=20),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_transaction_id",
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="order",
            name="payu_payment_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="order",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
