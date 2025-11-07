# dashboard/urls.py
from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("log/", views.log, name="log"),
    path("settings/", views.settings, name="settings"),

    # data table & filters
    path("api/invoices/", views.api_invoices, name="api-invoices"),
    path("api/invoice/create/", views.api_invoice_create, name="api-invoice-create"),
    path("api/invoice/<int:pk>/update/", views.api_invoice_update, name="api-invoice-update"),
    path("api/invoice/<int:pk>/delete/", views.api_invoice_delete, name="api-invoice-delete"),
    path("api/invoice/<int:pk>/status/", views.api_invoice_status, name="api-invoice-status"),
    path("api/filters/", views.api_filters, name="api-filters"),
    
    # Export to Excel
    path("api/export/excel/", views.api_export_excel, name="api-export-excel"),

    # remarks
    path("api/remarks/", views.api_remarks_list, name="api-remarks-list"),
    path("api/remarks/add/", views.api_remarks_add, name="api-remarks-add"),
    path("api/remarks/<int:pk>/delete/", views.api_remarks_delete, name="api-remarks-delete"),  # NEW
    path("api/remarks/reorder/", views.api_remarks_reorder, name="api-remarks-reorder"),

    # download
    path("download/<int:pk>/", views.download_invoice, name="download-invoice"),

    # charts
    path("api/charts/", views.api_charts, name="api-charts"),
]