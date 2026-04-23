"""Carga datos de ejemplo para desarrollo.

Uso:
    python manage.py seed_demo

Crea (idempotente — no duplica si ya existen):
    - Usuarios: admin / coordinador1 / tecnico1 / tecnico2
    - 2 Clientes, 3 Cuentas, 2 Tecnicos, 3 Pedidos de muestra
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


def _get_or_create_group(name: str):
    group, _ = Group.objects.get_or_create(name=name)
    return group


def _make_user(username: str, password: str, *, is_staff=False, is_superuser=False, group: str | None = None):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@prointel.pe",
            "is_staff": is_staff,
            "is_superuser": is_superuser,
        },
    )
    if created:
        user.set_password(password)
        user.save()
    if group:
        user.groups.add(_get_or_create_group(group))
    return user, created


class Command(BaseCommand):
    help = "Carga datos demo: usuarios, clientes, tecnicos y pedidos de ejemplo."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== seed_demo ==="))
        with transaction.atomic():
            self._seed_users()
            self._seed_clientes_cuentas()
            self._seed_tecnicos()
            self._seed_pedidos()
        self.stdout.write(self.style.SUCCESS("Listo. Datos demo cargados."))

    # ------------------------------------------------------------------ #
    def _seed_users(self):
        _get_or_create_group("coordinadores")
        _get_or_create_group("tecnicos")

        _, c = _make_user("admin", "admin1234", is_staff=True, is_superuser=True)
        self._log("admin", c)

        _, c = _make_user("coordinador1", "coord1234", group="coordinadores")
        self._log("coordinador1", c)

        _, c = _make_user("tecnico1", "tec1234", group="tecnicos")
        self._log("tecnico1", c)

        _, c = _make_user("tecnico2", "tec1234", group="tecnicos")
        self._log("tecnico2", c)

    def _seed_clientes_cuentas(self):
        from apps.clientes.models import Cliente
        from apps.cuentas.models import Cuenta

        c1, created = Cliente.objects.get_or_create(
            documento="20123456789",
            defaults={"nombre": "Banco del Sur S.A.", "correo": "contacto@bancosur.pe", "telefono": "014000001"},
        )
        self._log("Cliente: Banco del Sur", created)

        c2, created = Cliente.objects.get_or_create(
            documento="20987654321",
            defaults={"nombre": "Seguros Andinos SAC", "correo": "it@segurosandinos.pe", "telefono": "014000002"},
        )
        self._log("Cliente: Seguros Andinos", created)

        cuentas = [
            {
                "nombre": "Oficina Miraflores",
                "cliente": c1,
                "numero": "BS-001",
                "direccion": "Av. Larco 123",
                "distrito": "Miraflores",
                "latitud": -12.1191,
                "longitud": -77.0310,
            },
            {
                "nombre": "Oficina San Isidro",
                "cliente": c1,
                "numero": "BS-002",
                "direccion": "Calle Los Libertadores 456",
                "distrito": "San Isidro",
                "latitud": -12.0975,
                "longitud": -77.0435,
            },
            {
                "nombre": "Sede Central",
                "cliente": c2,
                "numero": "SA-001",
                "direccion": "Jr. Union 789",
                "distrito": "Cercado",
                "latitud": -12.0464,
                "longitud": -77.0428,
            },
        ]
        for data in cuentas:
            _, created = Cuenta.objects.get_or_create(
                cliente=data["cliente"],
                numero=data["numero"],
                defaults={k: v for k, v in data.items() if k not in {"cliente", "numero"}},
            )
            self._log(f"Cuenta {data['nombre']}", created)

    def _seed_tecnicos(self):
        from apps.tecnicos.models import Tecnico

        tecnicos_data = [
            {
                "username": "tecnico1",
                "nombre": "Carlos Paredes",
                "especialidad": "Redes",
                "zona": "Miraflores",
                "latitud_base": -12.1210,
                "longitud_base": -77.0295,
            },
            {
                "username": "tecnico2",
                "nombre": "Maria Quispe",
                "especialidad": "Camaras",
                "zona": "San Isidro",
                "latitud_base": -12.0980,
                "longitud_base": -77.0420,
            },
        ]
        for data in tecnicos_data:
            username = data.pop("username")
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                continue
            _, created = Tecnico.objects.get_or_create(user=user, defaults=data)
            self._log(f"Tecnico {data['nombre']}", created)

    def _seed_pedidos(self):
        from apps.clientes.models import Cliente
        from apps.cuentas.models import Cuenta
        from apps.pedidos.models import Pedido
        from apps.tecnicos.models import Tecnico

        try:
            cliente = Cliente.objects.get(documento="20123456789")
            cuenta1 = Cuenta.objects.get(cliente=cliente, numero="BS-001")
            cuenta2 = Cuenta.objects.filter(cliente=cliente, numero="BS-002").first()
        except (Cliente.DoesNotExist, Cuenta.DoesNotExist):
            self.stdout.write(self.style.WARNING("Faltan clientes/cuentas, omitiendo pedidos."))
            return

        tecnico = Tecnico.objects.first()

        pedidos = [
            {
                "titulo": "Instalacion de switch gestionado",
                "descripcion": "Reemplazar switch legacy por Cisco 2960X en rack principal.",
                "tipo_servicio": "Infraestructura",
                "zona": "Miraflores",
                "prioridad": Pedido.Prioridad.ALTA,
                "cliente": cliente,
                "cuenta": cuenta1,
                "tecnico_asignado": tecnico,
            },
            {
                "titulo": "Revision de camaras CCTV",
                "descripcion": "Limpieza y calibracion de 12 camaras del piso 3.",
                "tipo_servicio": "Seguridad",
                "zona": "Miraflores",
                "prioridad": Pedido.Prioridad.MEDIA,
                "cliente": cliente,
                "cuenta": cuenta1,
                "tecnico_asignado": None,
            },
            {
                "titulo": "Soporte UPS sala de servidores",
                "descripcion": "Cambio de baterias UPS APC 3000VA.",
                "tipo_servicio": "Energia",
                "zona": "San Isidro",
                "prioridad": Pedido.Prioridad.CRITICA,
                "cliente": cliente,
                "cuenta": cuenta2,
                "tecnico_asignado": None,
            },
        ]
        for data in pedidos:
            existing = Pedido.objects.filter(titulo=data["titulo"], cliente=data["cliente"]).first()
            if not existing:
                Pedido.objects.create(**data)
                self._log(f"Pedido: {data['titulo']}", True)
            else:
                self._log(f"Pedido: {data['titulo']}", False)

    # ------------------------------------------------------------------ #
    def _log(self, label: str, created: bool):
        if created:
            self.stdout.write(f"  {self.style.SUCCESS('+')} {label}")
        else:
            self.stdout.write(f"  {self.style.WARNING('=')} {label} (ya existe)")
