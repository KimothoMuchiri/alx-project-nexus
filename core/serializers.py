from rest_framework import serializers

# since they are read-only Security Dashboard API,wer require only shape the JSON

class CountryRequestStatSerializer(serializers.Serializer):
    country = serializers.CharField(allow_null=True, allow_blank=True)
    count = serializers.IntegerField()


class IPRequestStatSerializer(serializers.Serializer):
    ip_address = serializers.CharField()
    count = serializers.IntegerField()


class SecurityDashboardSerializer(serializers.Serializer):
    total_requests = serializers.IntegerField()
    requests_per_country = CountryRequestStatSerializer(many=True)
    top_ips = IPRequestStatSerializer(many=True)
    blacklisted_count = serializers.IntegerField()
    suspicious_count = serializers.IntegerField()
