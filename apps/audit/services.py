from .models import AuditAction, AuditEvent


def get_client_ip(request) -> str | None:
    """User कुन ठाउँ वा WiFi/Network बाट आएको हो, उसको IP Address पत्ता लगाउँछ (जस्तै: 192.168.1.5 वा 27.34.20.15) """
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request) -> str:
    """Extracts client user-agent string truncated to 500 characters."""
    if not request:
        return ''
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def log_audit_event(
    action: str,
    actor=None,
    request=None,
    target_type: str = '',
    target_id: str = '',
    description: str = '',
    extra_data: dict | None = None,
) -> AuditEvent:
    """
    Records an immutable audit event.
    Automatically captures actor, IP address, and browser metadata.
    Complies with PRD FR-20 and US-11.
    """
    ip_address = get_client_ip(request) if request else None
    user_agent = get_user_agent(request) if request else ''

    # Extract authenticated actor from request if not explicitly provided
    if actor is None and request and hasattr(request, 'user') and request.user.is_authenticated:
        actor = request.user

    actor_email = getattr(actor, 'email', '') if actor else ''

    return AuditEvent.objects.create(
        actor=actor,
        actor_email=actor_email,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=extra_data or {},
    )

