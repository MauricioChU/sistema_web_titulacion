from django_mongodb_backend.fields.auto import ObjectIdAutoField
from rest_framework import serializers


class MongoModelSerializer(serializers.ModelSerializer):
    """ModelSerializer tuned for django_mongodb_backend ObjectId primary keys."""

    serializer_field_mapping = dict(serializers.ModelSerializer.serializer_field_mapping)
    serializer_field_mapping[ObjectIdAutoField] = serializers.CharField

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super().build_relational_field(field_name, relation_info)
        if field_class is serializers.PrimaryKeyRelatedField:
            field_kwargs.setdefault("pk_field", serializers.CharField())
        return field_class, field_kwargs