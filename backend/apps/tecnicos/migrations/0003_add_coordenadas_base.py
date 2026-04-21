from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


DEFAULT_COORDS = (-12.0464, -77.0428)

ZONE_COORDS = {
    "miraflores": (-12.1211, -77.0297),
    "san isidro": (-12.0962, -77.0307),
    "surco": (-12.1405, -76.9910),
    "la molina": (-12.0749, -76.9512),
}


def _resolve_coords(tecnico):
    zona = (tecnico.zona or "").strip().lower()
    for known_zone, coords in ZONE_COORDS.items():
        if known_zone in zona:
            return coords
    return DEFAULT_COORDS


def populate_tecnico_coordinates(apps, schema_editor):
    # Historical migration state may expose legacy id types; use runtime model
    # to keep ObjectId primary keys readable during backfill.
    from apps.tecnicos.models import Tecnico

    for tecnico in Tecnico.objects.all():
        if tecnico.latitud_base is not None and tecnico.longitud_base is not None:
            continue

        lat, lon = _resolve_coords(tecnico)
        Tecnico.objects.filter(id=tecnico.id).update(latitud_base=lat, longitud_base=lon)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("tecnicos", "0002_tecnico_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="tecnico",
            name="latitud_base",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tecnico",
            name="longitud_base",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.RunPython(populate_tecnico_coordinates, noop_reverse),
        migrations.AlterField(
            model_name="tecnico",
            name="latitud_base",
            field=models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]),
        ),
        migrations.AlterField(
            model_name="tecnico",
            name="longitud_base",
            field=models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]),
        ),
    ]
