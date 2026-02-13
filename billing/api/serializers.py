from decimal import Decimal, Overflow
from mailbox import Error
from typing import override

from django.utils.translation import override
from rest_framework import serializers

from ..models import Barrel, Invoice, InvoiceLine, Provider


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ["id", "name", "address", "tax_id", "has_barrels_to_bill"]

        def has_barrels_to_bill(self, obj: Provider) -> bool:
            return obj.has_barrels_to_bill


class ProviderDetailSerializer(ProviderSerializer):
    # devuelve SOLO los ids de los barrel relacionados
    barrels = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(ProviderSerializer.Meta):
        fields = ProviderSerializer.Meta.fields + ["barrels"]


class BarrelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrel
        fields = ["id", "provider", "number", "oil_type", "liters", "billed"]


class InvoiceLineNestedSerializer(serializers.ModelSerializer):
    # Requirement: return invoice lines WITHOUT the barrel object included.
    # We expose barrel_id only (not nested barrel details).
    barrel_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = InvoiceLine
        fields = ["id", "barrel_id", "liters", "description", "unit_price"]


class InvoiceLineCreateSerializer(serializers.Serializer):
    barrel = serializers.PrimaryKeyRelatedField(queryset=Barrel.objects.all())
    liters = serializers.IntegerField(min_value=1)
    description = serializers.CharField(max_length=255)
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    def create(self, validated_data: dict) -> InvoiceLine:
        invoice = self.context["invoice"]
        barrel: Barrel = validated_data["barrel"]

        if barrel.billed:
            raise serializers.ValidationError(
                {"barrel": "Oops... barrel already billed!"}
            )

        return invoice.add_line_for_barrel(
            barrel=barrel,
            liters=validated_data["liters"],
            unit_price_per_liter=validated_data["unit_price"],
            description=validated_data["description"],
        )


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineNestedSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ["id", "invoice_no", "issued_on", "lines", "total_amount"]

    def get_total_amount(self, obj) -> Decimal:
        return sum(line.liters * line.unit_price for line in obj.lines.all())
