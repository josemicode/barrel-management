from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Barrel, Invoice, Provider
from .filters import InvoiceFilter
from .serializers import (
    BarrelSerializer,
    InvoiceLineCreateSerializer,
    InvoiceLineNestedSerializer,
    InvoiceSerializer,
    ProviderDetailSerializer,
    ProviderSerializer,
)


class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.all().order_by("id")
    serializer_class = ProviderSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProviderDetailSerializer
        return super().get_serializer_class()


class BarrelViewSet(viewsets.ModelViewSet):
    queryset = Barrel.objects.select_related("provider").all().order_by("id")
    serializer_class = BarrelSerializer
    # Requirement: barrels endpoint without filters on billed/unbilled
    filter_backends = []


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = (
        Invoice.objects.prefetch_related("lines").all().order_by("-issued_on", "-id")
    )
    serializer_class = InvoiceSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = InvoiceFilter

    def get_serializer_class(self):
        if self.action == "add_line":
            return InvoiceLineCreateSerializer
        return super().get_serializer_class()

    @extend_schema(
        request=InvoiceLineCreateSerializer,
        responses={
            201: InvoiceLineNestedSerializer,
            400: OpenApiResponse(description="Validation error: barrel already billed"),
        },
    )
    @action(detail=True, methods=["post"], url_path="add-line")
    def add_line(self, request, *args, **kwargs):
        invoice = self.get_object()
        serializer = InvoiceLineCreateSerializer(
            data=request.data,
            context={"invoice": invoice},
        )
        serializer.is_valid(raise_exception=True)
        try:
            line = serializer.save()
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)})

        output = InvoiceLineNestedSerializer(line)
        return Response(output.data, status=status.HTTP_201_CREATED)
