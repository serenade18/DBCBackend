from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.organizations.models import Organization, OrganizationMember, OrganizationRole

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id", "name", "slug", "logo", "description", "website", "email",
            "phone", "country", "timezone", "my_role", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.members.filter(user=request.user, status="active").first()
        return membership.role if membership else None


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMember
        fields = ["id", "organization", "user", "role", "status", "invited_at", "joined_at"]
        read_only_fields = ["id", "organization", "user", "invited_at", "joined_at", "status"]


class MemberInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationRole.choices, default=OrganizationRole.MEMBER)

    def validate_role(self, value):
        if value == OrganizationRole.OWNER:
            raise serializers.ValidationError("Cannot invite a member directly as owner.")
        return value


class MemberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMember
        fields = ["role", "status"]

    def validate_role(self, value):
        if value == OrganizationRole.OWNER:
            raise serializers.ValidationError("Ownership must be transferred explicitly, not set via this field.")
        return value
