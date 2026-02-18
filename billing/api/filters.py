import django_filters
from ..models import Invoice, Provider


class InvoiceFilter(django_filters.FilterSet):
    invoice_no = django_filters.CharFilter(lookup_expr="icontains")
    issued_on = django_filters.DateFromToRangeFilter()
    provider = django_filters.NumberFilter()

    class Meta:
        model = Invoice
        fields = ["invoice_no", "issued_on"]


class ProviderFilter(django_filters.FilterSet):
    has_barrels_to_bill = django_filters.BooleanFilter(
        method="filter_has_barrels_to_bill"
    )

    def filter_has_barrels_to_bill(self, queryset, name, value):
        if value is True:
            return queryset.filter(barrels__billed=False).distinct()
        elif value is False:
            return queryset.exclude(barrels__billed=False)
        return queryset

    class Meta:
        model = Provider
        fields = ["has_barrels_to_bill"]
