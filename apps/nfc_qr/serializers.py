from rest_framework import serializers

from apps.nfc_qr.models import NfcCard


class NfcCardSerializer(serializers.ModelSerializer):
    write_payload = serializers.CharField(read_only=True)

    class Meta:
        model = NfcCard
        fields = [
            "id", "uid", "serial_number", "material", "vcard", "order",
            "status", "activated_at", "write_payload", "created_at",
        ]
        read_only_fields = ["id", "status", "activated_at", "write_payload", "created_at"]


class NfcAssignSerializer(serializers.Serializer):
    vcard_id = serializers.UUIDField()


class NfcRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NfcCard
        fields = ["uid", "serial_number", "material"]
