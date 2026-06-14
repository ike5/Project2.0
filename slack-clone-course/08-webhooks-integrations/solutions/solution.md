# Challenge 08 — Reference Solution

### 1. Reject forgeries (signed inbound)
```python
# webhooks/views.py
from .utils import verify, SIGNATURE_HEADER

class SignedIncomingView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, token):
        hook = IncomingWebhook.objects.filter(token=token, active=True).first()
        if not hook:
            return Response(status=404)
        sig = request.META.get("HTTP_" + SIGNATURE_HEADER.upper().replace("-", "_"))
        if not verify(hook.token, request.body, sig):   # raw bytes!
            return Response({"detail": "bad signature"}, status=401)
        ...
```
Tampering with the body changes the HMAC → `401`.

### 2. Don't loop
Mark webhook-origin messages and skip them in the signal. Simplest: add a flag on the
instance and check it.
```python
# webhooks/views.py IncomingWebhookView, after creating the message:
message._from_incoming_webhook = True

# webhooks/signals.py
@receiver(post_save, sender=Message, dispatch_uid="webhooks_message_created")
def on_message_saved(sender, instance, created, **kwargs):
    if created and not getattr(instance, "_from_incoming_webhook", False):
        fire_message_created(instance)
```
> A durable alternative is a `source` column on `Message` (`user` / `incoming_webhook`)
> and filtering on it — survives re-fetches, unlike an instance attribute.

### 3. `/weather` slash command
```python
# intercept in MessageViewSet.perform_create (or the consumer) BEFORE saving:
body = serializer.validated_data["body"]
if body.startswith("/weather"):
    city = body[len("/weather"):].strip() or "London"
    text = fetch_weather(city)            # real API or stub
    Message.objects.create(channel=channel, author=bot_user, body=f"☀️ {city}: {text}")
    raise serializers.ValidationError({"slash": "handled"})  # or return a 200 marker
```

### 4. Delivery dashboard
```python
# webhooks/views.py — on OutgoingWebhookViewSet
@action(detail=True, methods=["get"])
def deliveries(self, request, pk=None):
    hook = self.get_object()
    rows = hook.deliveries.order_by("-id")[:50].values(
        "status_code", "attempt", "succeeded", "created_at")
    return Response(list(rows))
```

### 5. Why sign the raw body
> The signature is an HMAC over the **exact bytes** of the request body. If the
> receiver re-serialized the parsed JSON before verifying, any difference — key order,
> whitespace, unicode escaping, float formatting — would produce a different byte
> string and a different HMAC, so a legitimate request would fail to verify. Signing
> and verifying the **raw body** guarantees both sides hash identical bytes, so the
> check reflects authenticity, not serialization quirks.
