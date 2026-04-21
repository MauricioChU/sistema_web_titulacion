from django.db import migrations, models


def populate_pedido_codes(apps, schema_editor):
    # Historical migration state may expose legacy id types; use runtime model
    # to keep ObjectId primary keys readable during backfill.
    from apps.pedidos.models import Pedido

    counter = 1
    for pedido in Pedido.objects.order_by("created_at", "id"):
        codigo = f"A{counter:04d}"
        counter += 1
        Pedido.objects.filter(id=pedido.id).update(codigo=codigo)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0002_flujo_tecnico"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="codigo",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=20, null=True),
        ),
        migrations.RunPython(populate_pedido_codes, noop_reverse),
        migrations.AlterField(
            model_name="pedido",
            name="codigo",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=20, unique=True),
        ),
    ]
