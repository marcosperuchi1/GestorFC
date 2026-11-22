"""Compare public release bytes with this run's cryptographically verified build.

This read-only distribution check runs after the existing Minisign gate and R2
publication. It never reads signing credentials or performs new cryptography.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VERSION = "18.381.0"
INSTALLER_NAME = "FutBR-Manager-18.381-Windows.exe"
HOST = "download.futbrmanager.com.br"
BASE = "https://" + HOST + "/updates/"
FEED = BASE + "latest.json"
INSTALLER = BASE + INSTALLER_NAME
SIGNATURE = INSTALLER + ".sig"
MIN_INSTALLER_BYTES = 40_000_000
MAX_INSTALLER_BYTES = 200_000_000
WAIT_SECONDS = 300
POLL_SECONDS = 15


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def require_official_url(url, expected_path=None):
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == "https" and parsed.hostname == HOST
            and parsed.port in (None, 443) and parsed.username is None
            and parsed.password is None and not parsed.query and not parsed.fragment,
            "Refusing an unexpected public release origin")
    require(expected_path is None or parsed.path == expected_path,
            "Refusing an unexpected public resource redirect")
    return parsed


class OfficialRedirectsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        current = require_official_url(req.full_url)
        target = urllib.parse.urljoin(req.full_url, newurl)
        require_official_url(target, current.path)
        return super().redirect_request(req, fp, code, msg, headers, target)


def open_official(url, accept, deadline):
    wanted = require_official_url(url)
    remaining = deadline - time.monotonic()
    require(remaining > 0, "Public release verification exceeded five minutes")
    request = urllib.request.Request(url, headers={
        "User-Agent": "FutBR-Public-Release-Verification/18.381",
        "Cache-Control": "no-cache", "Accept-Encoding": "identity", "Accept": accept,
    })
    response = urllib.request.build_opener(OfficialRedirectsOnly()).open(
        request, timeout=min(30, remaining))
    try:
        require_official_url(response.geturl(), wanted.path)
        require(response.status == 200, "Expected HTTP 200 for the public release")
        require(response.headers.get("Content-Encoding", "identity").lower() in ("", "identity"),
                "Unexpected encoded public response")
        return response
    except Exception:
        response.close()
        raise


def read_small(url, limit, accept, deadline):
    with open_official(url, accept, deadline) as response:
        body = response.read(limit + 1)
        require(len(body) <= limit, "Oversized public metadata response")
        declared = response.headers.get("Content-Length")
        require(declared is None or int(declared) == len(body), "Truncated public metadata response")
        return body


def read_local(path, limit):
    with path.open("rb") as source:
        data = source.read(limit + 1)
    require(len(data) <= limit, "Oversized verified artifact metadata: " + path.name)
    return data


def digest_installer(stream, deadline=None):
    digest, size, first_bytes = hashlib.sha256(), 0, b""
    while True:
        if deadline is not None:
            require(time.monotonic() < deadline, "Public release verification exceeded five minutes")
        block = stream.read(1024 * 1024)
        if not block:
            break
        if size == 0:
            first_bytes = block[:2]
        size += len(block)
        require(size <= MAX_INSTALLER_BYTES, "Installer exceeds the expected size range")
        digest.update(block)
    require(MIN_INSTALLER_BYTES <= size <= MAX_INSTALLER_BYTES, "Unexpected installer size")
    require(first_bytes == b"MZ", "Installer is not a Windows executable")
    return digest.hexdigest(), size


def trusted_artifact(directory):
    report = json.loads(read_local(directory / "updater-18381-signature-tests.json", 131072))
    require(report.get("version") == VERSION and all(report.get(key) is True for key in (
        "ok", "installedUpdaterTrustMatchesSignature", "installerSha256Verified",
        "manifestSignatureExact", "publicKeyDerivedFromConfiguredSigner", "careerSavesPreserved")),
        "Missing successful updater trust report from the preceding cryptographic gate")
    manifest_bytes = read_local(directory / "latest.json", 131072)
    manifest = json.loads(manifest_bytes)
    require(manifest.get("version") == VERSION, "Verified artifact has the wrong version")
    platform = manifest.get("platforms", {}).get("windows-x86_64", {})
    require(platform.get("url") == INSTALLER, "Verified artifact has an unexpected installer URL")
    signature = platform.get("signature")
    require(isinstance(signature, str) and len(signature) >= 32, "Missing build signature")
    require(bool(base64.b64decode(signature, validate=True)), "Malformed build signature")
    sig_bytes = read_local(directory / (INSTALLER_NAME + ".sig"), 16384)
    require(sig_bytes in (signature.encode() + b"\n", signature.encode() + b"\r\n"),
            "The verified artifact signature does not match its manifest")
    release = json.loads(read_local(directory / "desktop-update-release-18381.json", 131072))
    require(release.get("ok") is True and release.get("version") == VERSION
            and release.get("signed") is True and release.get("asset") == INSTALLER,
            "Missing signed release packaging report")
    checksum = read_local(directory / "SHA256SUMS.txt", 4096).decode("ascii").strip()
    match = re.fullmatch(r"([0-9a-f]{64})  " + re.escape(INSTALLER_NAME), checksum)
    require(match is not None, "Unexpected installer checksum manifest")
    with (directory / INSTALLER_NAME).open("rb") as source:
        digest, size = digest_installer(source)
    require(digest == match[1] == release.get("sha256"),
            "Artifact executable, checksum manifest and packaging report disagree")
    return manifest_bytes, sig_bytes, digest, size


def verify_public(directory):
    manifest_bytes, sig_bytes, expected, artifact_size = trusted_artifact(directory)
    deadline, attempts = time.monotonic() + WAIT_SECONDS, 0
    while True:
        attempts += 1
        try:
            public_feed = read_small(FEED, 131072, "application/json", deadline)
            version = json.loads(public_feed).get("version")
            print(json.dumps({"publicFeedVersion": version, "expected": VERSION,
                              "attempt": attempts}), flush=True)
            if version != VERSION:
                require(isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+", version),
                        "Public feed contains an unexpected version")
                require(tuple(map(int, version.split("."))) < tuple(map(int, VERSION.split("."))),
                        "Public feed has already moved past this release")
            else:
                require(public_feed == manifest_bytes, "Public manifest differs from this verified build")
                public_sig = read_small(SIGNATURE, 16384, "application/octet-stream", deadline)
                require(public_sig == sig_bytes, "Public .sig bytes differ from this verified build")
                with open_official(INSTALLER, "application/octet-stream", deadline) as response:
                    declared = response.headers.get("Content-Length")
                    require(declared is None or int(declared) == artifact_size,
                            "Public installer Content-Length differs from the verified build")
                    digest, public_size = digest_installer(response, deadline)
                require(public_size == artifact_size and digest == expected,
                        "Public executable size or SHA-256 differs from the verified signed build")
                require(read_small(FEED, 131072, "application/json", deadline) == manifest_bytes,
                        "Public feed changed during verification")
                return {
                    "ok": True, "version": VERSION, "feed": FEED, "installer": INSTALLER,
                    "signatureUrl": SIGNATURE, "httpStatus": 200, "officialOriginOnly": True,
                    "priorUpdaterTrustReportVerified": True,
                    "publicManifestBytesMatchBuild": True, "publicSignatureBytesMatchBuild": True,
                    "completeInstallerDownloaded": True, "installerBytes": public_size,
                    "sha256": digest, "sha256MatchesVerifiedSignedBuild": True,
                    "sha256MatchesArtifactChecksumAndReleaseReport": True,
                    "publicFeedStableDuringDownload": True, "attempts": attempts,
                    "newCryptographicVerificationPerformed": False,
                    "verificationBasis": "Public bytes match this run's local artifacts after the preceding successful Minisign gate",
                }
        except urllib.error.HTTPError as error:
            if error.code not in (404, 429, 500, 502, 503, 504):
                raise
            print(json.dumps({"publicHttpRetry": error.code, "attempt": attempts}), flush=True)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            print(json.dumps({"publicNetworkRetry": type(error).__name__, "attempt": attempts}), flush=True)
        remaining = deadline - time.monotonic()
        require(remaining > 0, "Timed out waiting for the public 18.381 release within five minutes")
        time.sleep(min(POLL_SECONDS, remaining))


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_public_update_18381.py <project-dir>")
    artifacts = Path(sys.argv[1]).resolve() / "artifacts"
    output = artifacts / "public-updater-18381-tests.json"
    try:
        report = verify_public(artifacts)
    except Exception as error:
        report = {"ok": False, "version": VERSION, "errorType": type(error).__name__,
                  "error": str(error), "newCryptographicVerificationPerformed": False}
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report), flush=True)
        raise
    report.update({"buildRun": os.environ.get("GITHUB_RUN_ID"), "buildSha": os.environ.get("GITHUB_SHA")})
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report), flush=True)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## FutBR 18.381 public release verified\n\n"
                          f"- Installer: {INSTALLER}\n"
                          f"- Bytes: `{report['installerBytes']}`.\n"
                          f"- SHA-256: `{report['sha256']}`.\n"
                          "- Public feed, signature and complete executable match this run's verified build.\n")


if __name__ == "__main__":
    main()
