from ipaddress import ip_address, IPv4Address, IPv6Address


def get_client_ip(request):
    """
    Extract client IP, respecting X-Forwarded-For behind proxies.
    In production, ensure proxy chain is trusted.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # "client, proxy1, proxy2"
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


def anonymize_ip(ip_str):
    """
    Truncate IPv4/IPv6 addresses for GDPR-style anonymization.
    """
    try:
        ip_obj = ip_address(ip_str)
    except ValueError:
        return ip_str  # fall back to original

    if isinstance(ip_obj, IPv4Address):
        parts = ip_str.split(".")
        return ".".join(parts[:3] + ["0"])
    elif isinstance(ip_obj, IPv6Address):
        # Zero out the last segments
        return ip_str.rsplit(":", 2)[0] + "::"
    return ip_str
