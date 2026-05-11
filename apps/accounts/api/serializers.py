from rest_framework import serializers
from accounts.models import User


class UserSerializer(serializers.ModelSerializer[User]):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "father_name",
            "grandfather_name",
            "email",
            "phone_number",
            "address",
            "password",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "verified_at", "created_at", "updated_at"]


    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)