from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from billing.models import Barrel, Invoice, Provider


class Command(BaseCommand):
    help = "Seed demo data (providers, barrels, invoices)"

    def handle(self, *args, **options):
        Provider.objects.all().delete()

        p = Provider.objects.create(
            name="Acme Oils",
            address="123 Industrial Ave",
            tax_id="TAX-123",
        )
        b1 = Barrel.objects.create(
            provider=p, number="B-001", oil_type="EVO", liters=200, billed=False
        )
        b2 = Barrel.objects.create(
            provider=p, number="B-002", oil_type="EVOO", liters=150, billed=False
        )

        inv = Invoice.objects.create(
            invoice_no="INV-0001", issued_on=date.today(), provider=p
        )
        inv.add_line_for_barrel(
            barrel=b1,
            liters=200,
            unit_price_per_liter=Decimal("3.50"),
            description="Olive oil barrel B-001",
        )

        self.stdout.write(self.style.SUCCESS("Demo data created."))
