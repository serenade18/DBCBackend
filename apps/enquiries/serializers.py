from rest_framework import serializers

from apps.enquiries.models import Enquiry


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["id", "vcard", "name", "email", "phone", "message", "status", "created_at"]
        read_only_fields = ["id", "vcard", "created_at"]


class EnquiryStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["status"]


class PublicEnquirySubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["name", "email", "phone", "message"]
