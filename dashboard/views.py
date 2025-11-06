# dashboard/views.py
from datetime import datetime
from decimal import Decimal
import io

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.db.models import Max, Q, Value, Count, Sum
from django.db.models.functions import Lower

from .models import Invoice, InvoiceRemarkCategory, STATUS_CHOICES, CURRENCY_CHOICES

# Import untuk Excel export
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


# Currency conversion rates (base: IDR)
CURRENCY_RATES = {
    'IDR': 1.0,
    'USD': 15800.0,  # 1 USD = 15800 IDR
    'SGD': 11700.0,  # 1 SGD = 11700 IDR
}

def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another"""
    if from_currency == to_currency:
        return amount
    # Convert to IDR first, then to target currency
    amount_in_idr = amount * CURRENCY_RATES.get(from_currency, 1.0)
    return amount_in_idr / CURRENCY_RATES.get(to_currency, 1.0)


# ---------- helpers ----------
def _parse_range_str(s: str):
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
    qs = Invoice.objects.all()
    products = list(qs.order_by(Lower("product")).values_list("product", flat=True).distinct())
    currencies = [c for c, _ in CURRENCY_CHOICES]
    statuses = [s for s, _ in STATUS_CHOICES]
    senders = list(qs.order_by(Lower("from_party")).values_list("from_party", flat=True).distinct())
    receivers = list(qs.order_by(Lower("to_party")).values_list("to_party", flat=True).distinct())
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

# ---------- API: Export to Excel ----------
@login_required
def api_export_excel(request):
    if not EXCEL_AVAILABLE:
        return JsonResponse({"error": "openpyxl not installed"}, status=500)
    
    # Get filtered queryset (same logic as api_invoices)
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

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoice Summary"
    
    # Header style (blue background, white text)
    header_fill = PatternFill(start_color="102B86", end_color="102B86", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Headers (Product to To, exclude Action and Download)
    headers = ["Product", "Date", "Invoice Remarks", "Invoice Number", "Amount", "Currency", "Status", "From", "To"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
    
    # Data rows
    for row_num, inv in enumerate(qs, 2):
        ws.cell(row=row_num, column=1, value=inv.product)
        ws.cell(row=row_num, column=2, value=inv.date.strftime("%Y-%m-%d"))
        ws.cell(row=row_num, column=3, value=inv.remark.name if inv.remark else "-")
        ws.cell(row=row_num, column=4, value=inv.invoice_number)
        ws.cell(row=row_num, column=5, value=float(inv.amount))
        ws.cell(row=row_num, column=6, value=inv.currency)
        ws.cell(row=row_num, column=7, value=inv.status)
        ws.cell(row=row_num, column=8, value=inv.from_party)
        ws.cell(row=row_num, column=9, value=inv.to_party)
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width
    
    # Save to BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Create response
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="InvoiceSummaryFile.xlsx"'
    
    return response

@login_required
@require_http_methods(["POST"])
def api_invoice_create(request):
    product = request.POST.get("product", "").strip()
    date_str = request.POST.get("date", "").strip()
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
def api_remarks_delete(request, pk):
    """Delete remark only if no invoices are using it"""
    remark = get_object_or_404(InvoiceRemarkCategory, pk=pk)
    
    # Check if any invoices are using this remark
    usage_count = Invoice.objects.filter(remark=remark).count()
    
    if usage_count > 0:
        return JsonResponse({
            "ok": False, 
            "msg": f"Cannot delete. {usage_count} invoice(s) are using this remark."
        }, status=400)
    
    remark.delete()
    return JsonResponse({"ok": True})

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
    """Get chart data with optional currency conversion"""
    target_currency = request.GET.get('currency', 'IDR')
    
    qs_status = (
        Invoice.objects.values("status")
        .annotate(n=Count("id"))
        .order_by("status")
    )
    count_by_status = {
        "labels": [x["status"] for x in qs_status],
        "values": [x["n"] for x in qs_status],
    }

    # Amount by remark with currency conversion
    invoices = Invoice.objects.all()
    amount_by_remark = {}
    for inv in invoices:
        remark_name = inv.remark.name if inv.remark else "-"
        converted_amount = convert_currency(float(inv.amount), inv.currency, target_currency)
        amount_by_remark[remark_name] = amount_by_remark.get(remark_name, 0) + converted_amount
    
    # Amount by month with currency conversion
    amount_by_month = {}
    for inv in invoices:
        month = inv.date.strftime("%Y-%m")
        converted_amount = convert_currency(float(inv.amount), inv.currency, target_currency)
        amount_by_month[month] = amount_by_month.get(month, 0) + converted_amount
    
    # Top receivers with currency conversion
    amount_by_receiver = {}
    for inv in invoices:
        converted_amount = convert_currency(float(inv.amount), inv.currency, target_currency)
        amount_by_receiver[inv.to_party] = amount_by_receiver.get(inv.to_party, 0) + converted_amount

    return JsonResponse({
        "count_by_status": count_by_status,
        "amount_by_remark": {
            "labels": list(amount_by_remark.keys()),
            "values": list(amount_by_remark.values()),
        },
        "amount_by_month": {
            "labels": sorted(amount_by_month.keys()),
            "values": [amount_by_month[k] for k in sorted(amount_by_month.keys())],
        },
        "amount_by_receiver": {
            "labels": list(amount_by_receiver.keys()),
            "values": list(amount_by_receiver.values()),
        },
        "currency": target_currency,
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