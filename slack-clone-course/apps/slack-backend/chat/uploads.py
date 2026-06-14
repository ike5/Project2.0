"""
Upload + search endpoints.

Uploads use the presigned-URL pattern:
  1. client asks Django for a presigned PUT URL (knows nothing about credentials),
  2. client PUTs the bytes straight to MinIO/S3,
  3. client registers the Attachment metadata with Django,
  4. client posts a message referencing the attachment.

Search uses Postgres full-text search over message bodies, scoped to the user's
workspaces.
"""
import uuid

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from workspaces.models import Membership

from . import storage
from .models import Attachment, Message
from .serializers import MessageSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    """POST {filename, content_type} → {key, upload_url}. Client PUTs bytes to upload_url."""
    filename = request.data.get("filename")
    content_type = request.data.get("content_type", "application/octet-stream")
    if not filename:
        return Response({"filename": "required"}, status=400)
    # Namespaced, unguessable key so users can't collide or guess each other's files.
    key = f"u/{request.user.id}/{uuid.uuid4().hex}/{filename}"
    return Response({"key": key, "upload_url": storage.presign_put(key, content_type)})


class AttachmentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ("id", "message", "key", "filename", "content_type", "size", "download_url")
        read_only_fields = ("id", "download_url")

    def get_download_url(self, obj):
        return storage.presign_get(obj.key)


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        return Attachment.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search(request):
    """GET /api/search/?q=term[&workspace=ID] → ranked message matches you can see."""
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return Response({"results": []})

    my_ws = Membership.objects.filter(user=request.user).values_list("workspace_id", flat=True)
    vector = SearchVector("body")
    query = SearchQuery(q, search_type="websearch")
    qs = Message.objects.filter(channel__workspace_id__in=my_ws)

    workspace = request.query_params.get("workspace")
    if workspace:
        qs = qs.filter(channel__workspace_id=workspace)

    qs = (
        qs.annotate(rank=SearchRank(vector, query))
        .filter(rank__gt=0)
        .select_related("author")
        .order_by("-rank", "-id")[:50]
    )
    return Response({"results": MessageSerializer(qs, many=True).data})
