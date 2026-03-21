import ssl
import socket
import asyncio
from datetime import datetime
from OpenSSL import crypto
from app.models.ssl import SSLResult


def _compute_grade(expiry_days: int, expired: bool,
                   self_signed: bool, protocols: list[str]) -> str:
    """
    Computes a single letter grade from the certificate analysis.
    Rules applied in order — first match wins:
        F  — expired, self-signed, or connection failed entirely
        B  — weak protocols detected (TLS 1.0 or TLS 1.1)
        C  — certificate expiring within 30 days
        A  — valid, strong protocols, 30+ days remaining
        A+ — valid, TLS 1.3 only, 60+ days remaining
    """
    if expired or self_signed:
        return "F"

    weak_protocols = {"TLSv1", "TLSv1.1"}
    has_weak = bool(weak_protocols.intersection(set(protocols)))
    if has_weak:
        return "B"

    if expiry_days < 30:
        return "C"

    if expiry_days >= 60 and protocols == ["TLSv1.3"]:
        return "A+"

    return "A"


def _get_supported_protocols(hostname: str, port: int) -> list[str]:
    """
    Probes the server to find which TLS protocol versions it accepts.
    We test each protocol version individually by attempting a
    handshake — if the handshake succeeds, the protocol is supported.

    This is deliberately low-level because the high-level ssl module
    doesn't expose which protocols a server supports — it just picks
    the best one automatically. We need to know all of them.
    """
    supported = []

    # Map human-readable names to ssl module constants
    protocol_map = {
        "TLSv1":   ssl.PROTOCOL_TLS_CLIENT,
        "TLSv1.1": ssl.PROTOCOL_TLS_CLIENT,
        "TLSv1.2": ssl.PROTOCOL_TLS_CLIENT,
        "TLSv1.3": ssl.PROTOCOL_TLS_CLIENT,
    }

    for name in ["TLSv1.2", "TLSv1.3"]:
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Set the maximum and minimum version to isolate this protocol
            if name == "TLSv1.2":
                context.maximum_version = ssl.TLSVersion.TLSv1_2
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            elif name == "TLSv1.3":
                context.minimum_version = ssl.TLSVersion.TLSv1_3

            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname):
                    supported.append(name)
        except Exception:
            # Protocol not supported — move on to the next one
            pass

    return supported


def _run_ssl(domain: str, port: int = 443) -> SSLResult:
    """
    Main SSL analysis function. Opens a connection, pulls the
    certificate using pyOpenSSL, extracts all fields, then
    calls the grading function with the results.

    We use pyOpenSSL on top of the stdlib ssl module because
    it gives us direct access to the raw X509 certificate object,
    which lets us extract issuer, subject, and expiry cleanly.
    """
    try:
        # Create a raw SSL context — we disable verification
        # deliberately because we WANT to see bad certs
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                # Get the raw DER-encoded certificate bytes
                der_cert = ssock.getpeercert(binary_form=True)

        # Parse the raw bytes into an X509 object using pyOpenSSL
        x509 = crypto.load_certificate(crypto.FILETYPE_ASN1, der_cert)

        # Extract the issuer organisation name
        issuer = x509.get_issuer().organizationName or "Unknown"

        # Extract the subject common name (the domain the cert is for)
        subject = x509.get_subject().commonName or "Unknown"

        # Parse the expiry date — pyOpenSSL returns bytes in ASN1
        # format: b'20260101120000Z' — we decode and parse it
        expiry_str = x509.get_notAfter().decode("utf-8")
        expiry_date = datetime.strptime(expiry_str, "%Y%m%d%H%M%SZ")
        expiry_days = (expiry_date - datetime.utcnow()).days
        expired = expiry_days < 0

        # A cert is self-signed when the issuer and subject are identical
        self_signed = x509.get_issuer().CN == x509.get_subject().CN

        # Probe which TLS protocol versions the server supports
        protocols = _get_supported_protocols(domain, port)

        grade = _compute_grade(expiry_days, expired, self_signed, protocols)

        return SSLResult(
            grade=grade,
            issuer=issuer,
            subject=subject,
            expiry_date=expiry_date.strftime("%Y-%m-%d"),
            expiry_days=expiry_days,
            expired=expired,
            self_signed=self_signed,
            protocols=protocols,
        )

    except Exception as e:
        # Connection failed entirely — grade F, surface the error
        return SSLResult(grade="F", error=str(e))


async def run_ssl(domain: str, port: int = 443) -> SSLResult:
    """
    Async wrapper — moves the blocking SSL operations into
    a thread pool so FastAPI's event loop stays responsive.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_ssl, domain, port)
    return result