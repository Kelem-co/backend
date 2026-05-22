from academics.models import Grade
from academics.models import Section
from announcements.models import Announcement
from announcements.models import AnnouncementGrade
from announcements.models import AnnouncementSection
from django.db import transaction
from rest_framework import serializers

from media.api.serializers import MediaFileReferenceField


class AnnouncementSerializer(serializers.ModelSerializer):
    attachment = MediaFileReferenceField(required=False, allow_null=True)
    targeted_grades = serializers.PrimaryKeyRelatedField(
        queryset=Grade.objects.all(),
        many=True,
        required=False,
    )
    targeted_sections = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Announcement
        fields = [
            "id",
            "organization",
            "branch",
            "subject",
            "message",
            "attachment",
            "scheduled_at",
            "is_urgent",
            "status",
            "target_roles",
            "targeted_grades",
            "targeted_sections",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        # Ensure that grades and sections belong to the announcement's branch
        branch = data.get("branch")
        if not branch and self.instance:
            branch = self.instance.branch

        if not branch:
            raise serializers.ValidationError({"branch": "Branch is required."})

        grades = data.get("targeted_grades", [])
        for grade in grades:
            if grade.branch != branch:
                raise serializers.ValidationError(
                    {
                        "targeted_grades": f"Grade {grade.name} does not belong to the selected branch.",  # noqa: E501
                    },
                )

        sections = data.get("targeted_sections", [])
        for section in sections:
            if section.branch != branch:
                raise serializers.ValidationError(
                    {
                        "targeted_sections": f"Section {section.name} does not belong to the selected branch.",  # noqa: E501
                    },
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        grades = validated_data.pop("targeted_grades", [])
        sections = validated_data.pop("targeted_sections", [])

        announcement = Announcement.objects.create(**validated_data)

        # Create junction entries
        for grade in grades:
            AnnouncementGrade.objects.create(announcement=announcement, grade=grade)
        for section in sections:
            AnnouncementSection.objects.create(
                announcement=announcement,
                section=section,
            )

        return announcement

    @transaction.atomic
    def update(self, instance, validated_data):
        grades = validated_data.pop("targeted_grades", None)
        sections = validated_data.pop("targeted_sections", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update junction entries if provided
        if grades is not None:
            instance.targeted_grades.all().delete()
            for grade in grades:
                AnnouncementGrade.objects.create(announcement=instance, grade=grade)

        if sections is not None:
            instance.targeted_sections.all().delete()
            for section in sections:
                AnnouncementSection.objects.create(
                    announcement=instance,
                    section=section,
                )

        return instance
