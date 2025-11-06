# dashboard/views.py
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.db.models import Max, Q, Value
from django.db.models.functions import Lower

from .models import Invoice, InvoiceRemarkCategory, STATUS_CHOICES, CURRENCY_CHOICES
from django.db.models import Count, Sum
from django.http import HttpResponse


# ---------- helpers ----------
def _parse_range_str(s: str):
    # expects "YYYY-MM-DD to YYYY-MM-DD" or "" -> (None, None)
    if not s:
        return (None, None)
    parts = [p.strip() for p in s.split("to")]
    if len(parts) != 2:
        return (None, None)
    try:
        start = datetime.strptime(parts[0], "%Y-%m-%d").date()
        end = datetime.strptime(parts[1], "%Y-%m-%d").date()
        return (start, end)
    except Exception:
        return (None, None)

def _filters_payload():
    """
    Kumpulkan nilai unik dari tabel Invoice (bukan dari master category),
    supaya dropdown selalu otomatis memuat data yang benar. Jika sebuah
    nilai tidak lagi dipakai (karena semua invoice yang memakainya terhapus),
    maka otomatis hilang dari dropdown.
    """
    qs = Invoice.objects.all()
    products = list(qs.order_by(Lower("product")).values_list("product", flat=True).distinct())
    currencies = [c for c, _ in CURRENCY_CHOICES]
    statuses = [s for s, _ in STATUS_CHOICES]
    senders = list(qs.order_by(Lower("from_party")).values_list("from_party", flat=True).distinct())
    receivers = list(qs.order_by(Lower("to_party")).values_list("to_party", flat=True).distinct())
    # remarks berdasarkan invoice (bukan master)
    remarks = list(
        qs.filter(remark__isnull=False)
          .order_by(Lower("remark__name"))
          .values_list("remark__id", "remark__name")
          .distinct()
    )
    return {
        "products": products,
        "currencies": currencies,
        "statuses": statuses,
        "senders": senders,
        "receivers": receivers,
        "remarks": [{"id": rid, "name": nm} for rid, nm in remarks],
    }

# ---------- pages ----------
@login_required
def home(request):
    ctx = {
        "username": request.user.first_name or request.user.username,
        "filters": _filters_payload(),
        "status_choices": [s for s, _ in STATUS_CHOICES],
        "currency_choices": [c for c, _ in CURRENCY_CHOICES],
    }
    return render(request, "dashboard.html", ctx)

@login_required
def log_page(request):
    return render(request, "log.html")

@login_required
def settings_page(request):
    return render(request, "accountSetting.html")

# ---------- API: filters ----------
@login_required
def api_filters(request):
    return JsonResponse(_filters_payload())

# ---------- API: list invoices (filtered) ----------
@login_required
def api_invoices(request):
    qs = Invoice.objects.all()

    product = request.GET.get("product") or ""
    remark_id = request.GET.get("remark_id") or ""
    currency = request.GET.get("currency") or ""
    status = request.GET.get("status") or ""
    from_p = request.GET.get("from") or ""
    to_p = request.GET.get("to") or ""
    dr = request.GET.get("daterange") or ""
    start, end = _parse_range_str(dr)

    if product and product != "ALL":
        qs = qs.filter(product=product)
    if remark_id and remark_id != "ALL" and remark_id.isdigit():
        qs = qs.filter(remark_id=int(remark_id))
    if currency and currency != "ALL":
        qs = qs.filter(currency=currency)
    if status and status != "ALL":
        qs = qs.filter(status=status)
    if from_p and from_p != "ALL":
        qs = qs.filter(from_party=from_p)
    if to_p and to_p != "ALL":
        qs = qs.filter(to_party=to_p)
    if start and end:
        qs = qs.filter(date__range=(start, end))

    data = []
    for inv in qs:
        data.append({
            "id": inv.id,
            "product": inv.product,
            "date": inv.date.strftime("%Y-%m-%d"),
            "remark": inv.remark.name if inv.remark else "-",
            "invoice_number": inv.invoice_number,
            "amount": f"{inv.amount:.2f}",
            "currency": inv.currency,
            "status": inv.status,
            "from_party": inv.from_party,
            "to_party": inv.to_party,
            "download_url": f"/dashboard/download/{inv.pk}/",
        })
    return JsonResponse({"items": data})

@login_required
@require_http_methods(["POST"])
def api_invoice_create(request):

    product = request.POST.get("product", "").strip()
    date_str = request.POST.get("date", "").strip()  # YYYY-MM-DD
    remark_id = request.POST.get("remark_id", "").strip()
    invoice_number = request.POST.get("invoice_number", "").strip()
    amount_str = (request.POST.get("amount", "") or "0").replace(",", ".")
    currency = request.POST.get("currency", "IDR")
    status = request.POST.get("status", "Unpaid")
    from_party = request.POST.get("from_party", "").strip()
    to_party = request.POST.get("to_party", "").strip()

    if not remark_id or remark_id == "-" or remark_id == "0":
        return JsonResponse({"ok": False, "msg": "Please choose invoice remark."}, status=400)

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        amount = Decimal(amount_str)
    except Exception:
        return JsonResponse({"ok": False, "msg": "Invalid data."}, status=400)

    remark = get_object_or_404(InvoiceRemarkCategory, pk=int(remark_id))

    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"ok": False, "msg": "File is required."}, status=400)

    inv = Invoice.objects.create(
        product=product, date=date, remark=remark, invoice_number=invoice_number,
        amount=amount, currency=currency, status=status, from_party=from_party,
        to_party=to_party, file=f
    )
    return JsonResponse({"ok": True, "id": inv.pk})

@login_required
@require_http_methods(["POST"])
def api_invoice_update(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)

    product = request.POST.get("product", inv.product).strip()
    date_str = request.POST.get("date", inv.date.strftime("%Y-%m-%d")).strip()
    remark_id = request.POST.get("remark_id", str(inv.remark_id or "0")).strip()
    invoice_number = request.POST.get("invoice_number", inv.invoice_number).strip()
    amount_str = (request.POST.get("amount", str(inv.amount)) or "0").replace(",", ".")
    currency = request.POST.get("currency", inv.currency)
    status = request.POST.get("status", inv.status)
    from_party = request.POST.get("from_party", inv.from_party).strip()
    to_party = request.POST.get("to_party", inv.to_party).strip()

    if not remark_id or remark_id == "-" or remark_id == "0":
        return JsonResponse({"ok": False, "msg": "Please choose invoice remark."}, status=400)

    inv.product = product
    inv.date = datetime.strptime(date_str, "%Y-%m-%d").date()
    inv.remark = get_object_or_404(InvoiceRemarkCategory, pk=int(remark_id))
    inv.invoice_number = invoice_number
    inv.amount = Decimal(amount_str)
    inv.currency = currency
    inv.status = status
    inv.from_party = from_party
    inv.to_party = to_party

    f = request.FILES.get("file")
    if f:
        inv.file = f
    inv.save()

    return JsonResponse({"ok": True})

@login_required
@require_http_methods(["POST"])
def api_invoice_delete(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    inv.delete()
    return JsonResponse({"ok": True})

@login_required
@require_http_methods(["POST"])
def api_invoice_status(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    new_status = request.POST.get("status")
    legal = [s for s, _ in STATUS_CHOICES]
    if new_status not in legal:
        return JsonResponse({"ok": False, "msg": "Invalid status"}, status=400)
    inv.status = new_status
    inv.save()
    return JsonResponse({"ok": True})

@login_required
def api_remarks_list(request):
    data = list(InvoiceRemarkCategory.objects.order_by("order", "name")
                .values("id", "name", "order"))
    return JsonResponse({"items": data})

@login_required
@require_http_methods(["POST"])
def api_remarks_add(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "msg": "Invalid"}, status=400)

    if InvoiceRemarkCategory.objects.annotate(n=Lower("name")).filter(n=name.lower()).exists():
        return JsonResponse({"ok": False, "msg": "Remark exists or invalid"}, status=400)

    max_order = InvoiceRemarkCategory.objects.aggregate(m=Max("order"))["m"] or 0
    r = InvoiceRemarkCategory.objects.create(name=name, order=max_order + 1)
    return JsonResponse({"ok": True, "id": r.id, "name": r.name})

@login_required
@require_http_methods(["POST"])
def api_remarks_reorder(request):

    order_ids = request.POST.getlist("order[]")
    i = 1
    for rid in order_ids:
        try:
            obj = InvoiceRemarkCategory.objects.get(pk=int(rid))
            obj.order = i
            obj.save(update_fields=["order"])
            i += 1
        except Exception:
            continue
    return JsonResponse({"ok": True})

@login_required
def download_invoice(request, pk: int):
    inv = get_object_or_404(Invoice, pk=pk)
    try:
        resp = FileResponse(inv.file.open("rb"), as_attachment=True, filename=inv.download_filename)
        return resp
    except FileNotFoundError:
        raise Http404("File not found")

@login_required
def api_charts(request):
    qs_status = (
        Invoice.objects.values("status")
        .annotate(n=Count("id"))
        .order_by("status")
    )
    count_by_status = {
        "labels": [x["status"] for x in qs_status],
        "values": [x["n"] for x in qs_status],
    }

    qs_remark = (
        Invoice.objects.values("remark__name")
        .annotate(total=Sum("amount"))
        .order_by("remark__name")
    )
    amount_by_remark = {
        "labels": [x["remark__name"] or "-" for x in qs_remark],
        "values": [float(x["total"] or 0) for x in qs_remark],
    }

    return JsonResponse({
        "count_by_status": count_by_status,
        "amount_by_remark": amount_by_remark,
    })

@login_required
def log(request):
    try:
        return render(request, "dashboard/log.html", {})
    except Exception:
        return HttpResponse("Log page – coming soon.")

@login_required
def settings(request):
    try:
        return render(request, "dashboard/settings.html", {})
    except Exception:
        return HttpResponse("Settings page – coming soon.")