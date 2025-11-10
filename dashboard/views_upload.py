# dashboard/views_upload.py
import os, uuid, boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def api_get_presigned_url(request):
    filename = request.GET.get('filename', 'invoice.pdf')
    content_type = request.GET.get('content_type', 'application/pdf')

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('AWS_S3_ENDPOINT_URL'),   # ex: https://<ACCOUNT_ID>.r2.cloudflarestorage.com
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}),
            region_name='auto'
        )

        unique_id = uuid.uuid4()
        key = f"invoices/{unique_id}/{filename}"

        # >>> gunakan presigned URL untuk PUT, bukan POST
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': os.getenv('AWS_STORAGE_BUCKET_NAME'),
                'Key': key,
                'ContentType': content_type,
                # R2 tidak memakai ACL; jangan kirim 'ACL'
            },
            ExpiresIn=3600
        )

        return JsonResponse({
            "ok": True,
            "upload_url": presigned_url,
            "file_key": key,
            "method": "PUT",
            "headers": {"Content-Type": content_type}
        })

    except ClientError as e:
        return JsonResponse({"ok": False, "msg": f"Failed to generate upload URL: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"ok": False, "msg": f"Error: {e}"}, status=500)
