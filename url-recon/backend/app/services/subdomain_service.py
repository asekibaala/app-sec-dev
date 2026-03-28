import asyncio
import subprocess
import shutil
import httpx
import dns.resolver
from app.models.subdomains import SubdomainsResult, Subdomain


# ─────────────────────────────────────────────
# Wordlist — used by our built-in DNS bruteforce
# ─────────────────────────────────────────────
WORDLIST = [
    "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2",
    "smtp", "secure", "vpn", "m", "shop", "ftp", "api", "dev", "staging",
    "test", "portal", "admin", "app", "cdn", "media", "static", "assets",
    "img", "images", "beta", "demo", "old", "new", "preview", "dashboard",
    "login", "auth", "sso", "wiki", "docs", "support", "help", "forum",
    "status", "monitor", "metrics", "grafana", "jenkins", "git", "gitlab",
    "jira", "confluence", "slack", "office", "exchange", "autodiscover",
    "mysql", "db", "database", "redis", "mongo", "postgres", "backup",
    "files", "download", "uploads", "s3", "storage", "intranet", "internal",
]

DNS_CONCURRENCY = 20


# ─────────────────────────────────────────────
# Method 1 — DNS bruteforce (built-in, always runs)
# ─────────────────────────────────────────────

async def _resolve_subdomain(
    subdomain: str,
    domain: str,
    semaphore: asyncio.Semaphore,
) -> Subdomain | None:
    """
    Resolves a single subdomain candidate via DNS.
    The semaphore caps how many queries run simultaneously
    to avoid rate-limiting from DNS resolvers.
    Returns a Subdomain if it resolves, None if it doesn't exist.
    """
    fqdn = f"{subdomain}.{domain}"
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            answers = await loop.run_in_executor(
                None,
                lambda: dns.resolver.resolve(fqdn, "A")
            )
            return Subdomain(name=fqdn, ip=str(answers[0]))
        except dns.resolver.NXDOMAIN:
            return None
        except dns.resolver.NoAnswer:
            # Exists but no A record — still worth recording
            return Subdomain(name=fqdn, ip=None)
        except Exception:
            return None


async def _run_dns_bruteforce(domain: str) -> list[Subdomain]:
    """
    Fires all wordlist entries concurrently, controlled by
    the semaphore. Returns only the subdomains that resolved.
    """
    semaphore = asyncio.Semaphore(DNS_CONCURRENCY)
    tasks = [
        _resolve_subdomain(word, domain, semaphore)
        for word in WORDLIST
    ]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


# ─────────────────────────────────────────────
# Method 2 — Certificate Transparency via crt.sh
# ─────────────────────────────────────────────

async def _run_crtsh(domain: str) -> list[Subdomain]:
    """
    Queries crt.sh — a public Certificate Transparency log aggregator.

    Every SSL certificate issued by a trusted CA is logged publicly.
    This means subdomains appear in CT logs the moment a certificate
    is issued for them — even if they're not in any wordlist and even
    if they've since been taken offline.

    crt.sh exposes a JSON API we query directly. No API key needed.
    This is entirely passive — we make one HTTPS request to crt.sh,
    not to the target domain at all.

    We deduplicate using a set because the same subdomain often
    appears many times — once per certificate issued for it.
    We also filter out wildcard entries like *.example.com since
    those aren't specific subdomains we can enumerate further.
    """
    found = []
    seen = set()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # crt.sh JSON API — returns all certs matching the domain
            response = await client.get(
                f"https://crt.sh/?q=%.{domain}&output=json"
            )
            response.raise_for_status()
            data = response.json()

        for entry in data:
            # Each entry can contain multiple names separated by newlines
            name_value = entry.get("name_value", "")
            names = name_value.split("\n")

            for name in names:
                name = name.strip().lower()

                # Skip wildcards — not actionable subdomains
                if name.startswith("*"):
                    continue

                # Skip the root domain itself
                if name == domain:
                    continue

                # Skip anything not belonging to our target domain
                if not name.endswith(f".{domain}"):
                    continue

                # Deduplicate
                if name in seen:
                    continue

                seen.add(name)

                # Attempt to resolve each discovered subdomain
                # to get its current IP address
                try:
                    loop = asyncio.get_event_loop()
                    answers = await loop.run_in_executor(
                        None,
                        lambda n=name: dns.resolver.resolve(n, "A")
                    )
                    ip = str(answers[0])
                except Exception:
                    # CT log entry exists but subdomain no longer resolves
                    # Still worth recording — it may reveal attack surface
                    ip = None

                found.append(Subdomain(name=name, ip=ip))

    except Exception:
        # crt.sh is unavailable or returned bad data — return empty
        # The other methods will still run
        pass

    return found


# ─────────────────────────────────────────────
# Method 3 — Gobuster (optional, Kali/Parrot only)
# ─────────────────────────────────────────────

def _gobuster_available() -> bool:
    """
    Checks whether gobuster is installed on this machine.
    shutil.which() searches the system PATH — returns the
    full path to the binary if found, None if not installed.
    This lets the app degrade gracefully on macOS where
    gobuster isn't available without crashing the scan.
    """
    return shutil.which("gobuster") is not None


def _get_gobuster_wordlist() -> str | None:
    """
    Finds the best available wordlist for gobuster.
    Kali and Parrot ship with SecLists at known paths.
    We try each path in order of preference — best wordlist first.
    Returns None if no wordlist is found, which disables gobuster.
    """
    candidates = [
        # Kali Linux — SecLists DNS wordlist
        "/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt",
        # Parrot OS — same SecLists path
        "/usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt",
        # Fallback — smaller but always present on Kali
        "/usr/share/wordlists/dirb/common.txt",
    ]
    for path in candidates:
        import os
        if os.path.exists(path):
            return path
    return None


async def _run_gobuster(domain: str) -> list[Subdomain]:
    """
    Runs gobuster dns mode as a subprocess.

    gobuster is a compiled Go binary — much faster than Python
    DNS bruteforce. On Kali it ships with SecLists wordlists
    containing millions of real-world subdomain names.

    We run it with asyncio.create_subprocess_exec() so it
    doesn't block the FastAPI event loop while it runs.
    Output is captured line by line — gobuster prints each
    found subdomain as it discovers it, one per line.

    Format of gobuster dns output:
        Found: api.example.com

    We parse each line, extract the subdomain, and resolve
    its IP address the same way as the other methods.
    """
    if not _gobuster_available():
        return []

    wordlist = _get_gobuster_wordlist()
    if not wordlist:
        return []

    found = []
    seen = set()

    try:
        # Build the gobuster command
        # -d  = target domain
        # -w  = wordlist path
        # -t  = threads (10 is safe, won't overwhelm resolvers)
        # --no-color = clean output for parsing
        # -q  = quiet mode, only print results
        cmd = [
            "gobuster", "dns",
            "-d", domain,
            "-w", wordlist,
            "-t", "10",
            "--no-color",
            "-q",
        ]

        # Launch gobuster as an async subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        # Read output line by line as gobuster finds subdomains
        stdout, _ = await asyncio.wait_for(
            process.communicate(),
            timeout=60,  # Hard cap — don't let gobuster run forever
        )

        for line in stdout.decode().splitlines():
            line = line.strip()

            # gobuster dns output format: "Found: subdomain.domain.com"
            if not line.startswith("Found:"):
                continue

            name = line.replace("Found:", "").strip().lower()

            if name in seen:
                continue
            seen.add(name)

            # Resolve to IP
            try:
                loop = asyncio.get_event_loop()
                answers = await loop.run_in_executor(
                    None,
                    lambda n=name: dns.resolver.resolve(n, "A")
                )
                ip = str(answers[0])
            except Exception:
                ip = None

            found.append(Subdomain(name=name, ip=ip))

    except asyncio.TimeoutError:
        # Gobuster hit the time limit — return whatever we have so far
        pass
    except Exception:
        pass

    return found


# ─────────────────────────────────────────────
# Orchestrator — runs all three methods together
# ─────────────────────────────────────────────

async def run_subdomains(domain: str) -> SubdomainsResult:
    """
    Runs all three discovery methods concurrently using
    asyncio.gather() — DNS bruteforce, crt.sh CT logs, and
    gobuster (if available).

    Results from all three are merged and deduplicated.
    If the same subdomain is found by multiple methods,
    we keep whichever entry has a resolved IP address.
    Final list is sorted alphabetically for consistent output.
    """
    # Fire all three methods simultaneously
    dns_results, crtsh_results, gobuster_results = await asyncio.gather(
        _run_dns_bruteforce(domain),
        _run_crtsh(domain),
        _run_gobuster(domain),
    )

    # Merge all results — deduplicate by subdomain name
    # Prefer entries with a resolved IP over entries without
    merged: dict[str, Subdomain] = {}

    for subdomain in dns_results + crtsh_results + gobuster_results:
        name = subdomain.name

        if name not in merged:
            merged[name] = subdomain
        elif subdomain.ip and not merged[name].ip:
            # We already have this subdomain but without an IP —
            # replace it with this entry that has one
            merged[name] = subdomain

    found = sorted(merged.values(), key=lambda s: s.name)

    return SubdomainsResult(
        subdomains=found,
        total=len(found),
    )
