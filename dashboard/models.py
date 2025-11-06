# dashboard/models.py
from django.db import models
from django.db.models.functions import Lower

CURRENCY_CHOICES = (
    ("IDR", "IDR"),
    ("USD", "USD"),
    ("SGD", "SGD"),
)

STATUS_CHOICES = (
    ("Unpaid", "Unpaid"),
    ("Progress", "Progress"),
    ("Paid by MIMS Recoverable", "Paid by MIMS Recoverable"),
    ("Paid by MIMS Expense", "Paid by MIMS Expense"),
    ("Paid by Fund", "Paid by Fund")

)

class InvoiceRemarkCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"), name="uniq_remark_name_ci"
            )
        ]
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


def invoice_upload_path(instance, filename):
    return f"invoices/{instance.date:%Y/%m/%d}/{filename}"

class Invoice(models.Model):
    product = models.CharField(max_length=200)
    date = models.DateField()
    remark = models.ForeignKey(
        InvoiceRemarkCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    invoice_number = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="IDR")
    status = models.CharField(max_length=60, choices=STATUS_CHOICES, default="Unpaid")
    from_party = models.CharField(max_length=200)
    to_party = models.CharField(max_length=200)
    file = models.FileField(upload_to=invoice_upload_path, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.product} - {self.invoice_number}"

    @property
    def download_filename(self) -> str:
        # [date]-[product]-[status]-[invoice remarks]-[from->to].pdf
        r = (self.remark.name if self.remark else "-").replace(" ", "_")
        p = self.product.replace(" ", "_")
        f = self.from_party.replace(" ", "_")
        t = self.to_party.replace(" ", "_")
        base = f"{self.date:%Y%m%d}-{p}-{self.status}-{r}-{f}_to_{t}"
        return f"{base}{self.file.name[self.file.name.rfind('.'):]}"
