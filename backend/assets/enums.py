# assets/enums.py
from django.db import models

class AssetType(models.TextChoices):
    STOCKS_KR     = "STOCKS_KR",    "Stocks_KR"
    STOCKS_GLB    = "STOCKS_GLB",   "Stocks_GLB"
    BONDS_KR      = "BONDS_KR",     "Bonds_KR"
    BONDS_GLB     = "BONDS_GLB",    "Bonds_GLB"
    FUNDS         = "FUNDS",        "Funds"
    ALTERNATIVES  = "ALTERNATIVES", "Alternatives"
    CASH          = "CASH",         "Cash"