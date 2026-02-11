# assets/models.py
from django.db import models
from .enums import AssetType

class Asset(models.Model):
    code       = models.CharField(max_length=64, unique=True, db_index=True)
    name       = models.CharField(max_length=120)
    asset_type = models.CharField(max_length=32, choices=AssetType.choices)
    currency   = models.CharField(max_length=10, default="KRW")
    meta       = models.JSONField(default=dict, blank=True)
    is_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "asset"
        indexes = [models.Index(fields=["asset_type", "is_enabled"])]

    def __str__(self) -> str:
        return f"{self.code} ({self.asset_type})"