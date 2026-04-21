from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


DEFAULT_COORDS = (-12.0464, -77.0428)

ACCOUNT_COORDS_BY_NUMBER = {
    "CUE-1001": (-12.1211, -77.0297),
    "CUE-1002": (-12.0749, -76.9512),
    "CUE-2001": (-12.1405, -76.9910),
    "CUE-3001": (-12.0962, -77.0307),
    "CUE-5001": (-12.1211, -77.0297),
    "CUE-6001": (-12.1405, -76.9910),
    "CUE-7001": (-12.0962, -77.0307),
}

DISTRICT_COORDS = {
    "miraflores": (-12.1211, -77.0297),
    "san isidro": (-12.0962, -77.0307),
    "surco": (-12.1405, -76.9910),
    "la molina": (-12.0749, -76.9512),
}


def _resolve_coords(cuenta):
    numero = (cuenta.numero or "").strip().upper()
    if numero in ACCOUNT_COORDS_BY_NUMBER:
        return ACCOUNT_COORDS_BY_NUMBER[numero]

    direccion = ""
    if getattr(cuenta, "cliente_id", None) and getattr(cuenta, "cliente", None):
        direccion = (cuenta.cliente.direccion or "").strip().lower()

    for district, coords in DISTRICT_COORDS.items():
        if district in direccion:
            return coords

    return DEFAULT_COORDS


def populate_account_coordinates(apps, schema_editor):
    Cuenta = apps.get_model("cuentas", "Cuenta")

    for cuenta in Cuenta.objects.select_related("cliente").all():
        if cuenta.latitud is not None and cuenta.longitud is not None:
            continue

        lat, lon = _resolve_coords(cuenta)
        cuenta.latitud = lat
        cuenta.longitud = lon
        cuenta.save(update_fields=["latitud", "longitud"])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cuenta",
            name="latitud",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="cuenta",
            name="longitud",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.RunPython(populate_account_coordinates, noop_reverse),
        migrations.AlterField(
            model_name="cuenta",
            name="latitud",
            field=models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]),
        ),
        migrations.AlterField(
            model_name="cuenta",
            name="longitud",
            field=models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]),
        ),
    ]
