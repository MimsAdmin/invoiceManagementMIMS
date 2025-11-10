from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_alter_invoice_status'),
    ]

    operations = [
        # Index on date field - used in date range filters and sorting
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['date'], name='idx_invoice_date'),
        ),
        
        # Index on date DESC - for newest first sorting
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['-date'], name='idx_invoice_date_desc'),
        ),
        
        # Index on status - used in status filtering and charts
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['status'], name='idx_invoice_status'),
        ),
        
        # Index on remark FK - used in almost every query
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['remark'], name='idx_invoice_remark'),
        ),
        
        # Index on product - used in product filtering
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['product'], name='idx_invoice_product'),
        ),
        
        # Index on from_party - used in sender filtering
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['from_party'], name='idx_invoice_from'),
        ),
        
        # Index on to_party - used in receiver filtering and charts
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['to_party'], name='idx_invoice_to'),
        ),
        
        # Composite index for common filter combinations
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['status', 'date'], name='idx_status_date'),
        ),
        
        # Composite index for remark + date (used in charts)
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['remark', 'date'], name='idx_remark_date'),
        ),
    ]

