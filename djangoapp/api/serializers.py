from rest_framework import serializers
import calendar
from datetime import datetime
import uuid


class ImageSerializer(serializers.Serializer):

    product_choices = [
        # AER_DB Group
        ('59,188', 'Aerosol optical thickness at 1610 nm, Deep Blue algorithm'),

        # CARBON Group
        ('64,255', 'Phytoplankton Carbon'),

        # CHL Group
        ('5,6', 'Chlorophyll concentration'),

        # POC Group
        ('10,36', 'Particulate Organic Carbon'),
    ]

    res_choices = [
        ('0.1-deg', '0.1-deg'),
        ('4km', '4km'),
        ('9km', '9km'),
    ]

    period_choices = [
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ]

    product = serializers.ChoiceField(choices=product_choices)
    year = serializers.IntegerField(
        min_value=2024, max_value=datetime.now().year)
    month = serializers.CharField(max_length=2)
    day = serializers.CharField(max_length=2, required=False)
    res = serializers.ChoiceField(choices=res_choices, default='4km')
    period = serializers.ChoiceField(choices=period_choices)

    def validate(self, data):
        period = data.get('period')
        day = data.get('day')
        month = data.get('month')
        year = data.get('year')

        if period == 'daily' and day is None:
            raise serializers.ValidationError(
                "Day is required for the daily period.")

        if not month.isdigit() or not (1 <= int(month) <= 12):
            raise serializers.ValidationError(
                "Month must be a valid number between 01 and 12.")

        if day and (not day.isdigit() or not (1 <= int(day) <= 31)):
            raise serializers.ValidationError(
                "Day must be a valid number between 01 and 31.")

        try:
            if day:
                datetime(year=int(year), month=int(month), day=int(day))
        except ValueError:
            raise serializers.ValidationError(
                "Invalid date combination provided.")

        return data


class ChatMessageSerializer(serializers.Serializer):
    chat_uuid = serializers.UUIDField()
    message = serializers.CharField(max_length=1000)

    def validate_chat_uuid(self, value):
        try:
            uuid.UUID(str(value))
        except ValueError:
            raise serializers.ValidationError(
                "chat_uuid must be a valid UUID.")
        return value

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("message cannot be empty.")
        return value
