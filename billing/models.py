from __future__ import annotations

from decimal import Decimal
from random import choices
from tokenize import Number

from django.core.validators import MinValueValidator
from django.db import models, transaction


class BarrelQuerySet(models.QuerySet):
    def unbilled(self):
        return self.filter(billed=False)

    def total_liters(self) -> float:
        result = self.aggregate(total=models.Sum("liters"))
        return float(result["total"] or 0)


class Provider(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    tax_id = models.CharField(max_length=64)

    def __str__(self) -> str:
        return f"{self.name} ({self.tax_id})"

    def liters_to_bill(self) -> float:
        return self.barrels.unbilled().total_liters()


class Barrel(models.Model):
    class OilType(models.TextChoices):
        EVOO = "EVOO", "Extra Virgin Olive Oil"
        EVO = "EVO", "Virgin Olive Oil"
        ROO = "ROO", "Refined Olive Oil"
        OPO = "OPO", "Olive Pomace Oil"

    provider = models.ForeignKey(
        Provider, related_name="barrels", on_delete=models.CASCADE
    )
    number = models.CharField(max_length=64)
    oil_type = models.CharField(max_length=128, choices=OilType.choices)
    liters = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    billed = models.BooleanField(default=False)

    objects = BarrelQuerySet.as_manager()

    class Meta:
        unique_together = ("provider", "number")

    def __str__(self) -> str:
        return f"Barrel {self.number} ({self.oil_type})"


class Invoice(models.Model):
    invoice_no = models.CharField(max_length=64, unique=True)
    issued_on = models.DateField()
    
    provider = models.ForeignKey(Provider, related_name="invoices", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.invoice_no

    def calculate_total(self) -> int:
        return sum(line.liters * line.unit_price for line in self.lines.all())

    @transaction.atomic
    def add_line_for_barrel(
        self,
        barrel: Barrel,
        liters: int,
        unit_price_per_liter: Decimal,
        description: str,
    ) -> "InvoiceLine":
        
        if barrel.provider != self.provider:
            raise ValueError(
                f"Cannot add barrel {barrel.number}: "
                f"it belongs to provider '{barrel.provider.name}', "
                f"but the invoice is for '{self.provider.name}'."
            )
            
        if liters <= 0:
            raise ValueError("liters must be > 0")
        if unit_price_per_liter <= 0:
            raise ValueError("unit_price must be > 0")

        # Business rule from the prompt:
        if barrel.liters != liters:
            raise ValueError("liters must equal barrel.liters to bill the full barrel")

        new_line = InvoiceLine.objects.create(
            invoice=self,
            barrel=barrel,
            liters=liters,
            unit_price=unit_price_per_liter,
            description=description,
        )
        barrel.billed = True
        barrel.save(update_fields=["billed"])
        return new_line


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="lines", on_delete=models.CASCADE)
    barrel = models.ForeignKey(
        Barrel, related_name="invoice_lines", on_delete=models.PROTECT
    )
    liters = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    description = models.CharField(max_length=255)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    def __str__(self) -> str:
        return f"Line {self.id} ({self.liters} L @ {self.unit_price})"
