# dashboard/views_upload.py
import os
import uuid
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@login_required
def api_get_presigned_url(request):
    """
    Generate presigned URL for direct R2 upload (bypass Vercel 4.5MB limit)
    Used for files >4.3MB
    """
    
    filename = request.GET.get('filename', 'invoice.pdf')
    content_type = request.GET.get('content_type', 'application/pdf')
    
    try:
        # Create S3 client for Cloudflare R2
        s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('AWS_S3_ENDPOINT_URL'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        
        # Generate unique key for file
        unique_id = uuid.uuid4()
        key = f"invoices/{unique_id}/{filename}"
        
        # Generate presigned POST URL (supports files up to 100MB)
        presigned_post = s3_client.generate_presigned_post(
            Bucket=os.getenv('AWS_STORAGE_BUCKET_NAME'),
            Key=key,
            Fields={
                "Content-Type": content_type
            },
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, 100 * 1024 * 1024]  # 1 byte to 100MB
            ],
            ExpiresIn=3600  # URL valid for 1 hour
        )
        
        return JsonResponse({
            "ok": True,
            "upload_url": presigned_post['url'],
            "fields": presigned_post['fields'],
            "file_key": key
        })
        
    except ClientError as e:
        return JsonResponse({
            "ok": False,
            "msg": f"Failed to generate upload URL: {str(e)}"
        }, status=500)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "msg": f"Error: {str(e)}"
        }, status=500)