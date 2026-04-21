from django.apps import apps as global_apps
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.management import create_contenttypes
from django.db import DEFAULT_DB_ALIAS, router


def _get_builtin_permissions(opts):
    perms = []
    for action in opts.default_permissions:
        perms.append(
            (
                get_permission_codename(action, opts),
                "Can %s %s" % (action, opts.verbose_name_raw),
            )
        )
    return perms


def _get_all_permissions(opts):
    return [*_get_builtin_permissions(opts), *opts.permissions]


def create_permissions_safe(
    app_config,
    verbosity=2,
    interactive=True,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs,
):
    if not app_config.models_module:
        return

    try:
        Permission = apps.get_model("auth", "Permission")
    except LookupError:
        return

    if not router.allow_migrate_model(using, Permission):
        return

    create_contenttypes(
        app_config,
        verbosity=verbosity,
        interactive=interactive,
        using=using,
        apps=apps,
        **kwargs,
    )

    app_label = app_config.label
    try:
        app_config = apps.get_app_config(app_label)
        ContentType = apps.get_model("contenttypes", "ContentType")
    except LookupError:
        return

    models = list(app_config.get_models())
    ctype_manager = ContentType.objects.db_manager(using)

    ctype_by_model = {}
    for model in models:
        ctype = ctype_manager.get_for_model(model, for_concrete_model=False)
        if ctype.pk is None:
            ctype, _ = ctype_manager.get_or_create(
                app_label=model._meta.app_label,
                model=model._meta.model_name,
            )
        ctype_by_model[model] = ctype

    ctype_ids = [ctype.pk for ctype in ctype_by_model.values() if ctype.pk is not None]
    if not ctype_ids:
        return

    all_perms = set(
        Permission.objects.using(using)
        .filter(content_type_id__in=ctype_ids)
        .values_list("content_type", "codename")
    )

    perms = []
    for model in models:
        ctype = ctype_by_model[model]
        if ctype.pk is None:
            continue

        for codename, name in _get_all_permissions(model._meta):
            if (ctype.pk, codename) in all_perms:
                continue

            permission = Permission()
            permission._state.db = using
            permission.codename = codename
            permission.name = name
            permission.content_type = ctype
            perms.append(permission)

    Permission.objects.using(using).bulk_create(perms)

    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '%s'" % perm)
