# users/enums.py
from django.db import models

class RiskProfileChoices(models.TextChoices):
    CONSERVATIVE = "CONSERVATIVE", "안정형"
    MODERATE_CONSERVATIVE = "MODERATE_CONSERVATIVE", "안정추구형"
    BALANCED = "BALANCED", "중립형"
    GROWTH = "GROWTH", "적극투자형"
    AGGRESSIVE = "AGGRESSIVE", "공격투자형"