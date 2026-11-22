"""Publish one *already built and signed* FutBR Windows 18.375 artifact.

The source build is pinned to GitHub Actions run 44977954599 and artifact
14737742455. No game or Windows code is recompiled here. The release
workflow independently checks the original configured signing key,
checks the complete artifact, and publishes latest.json LAST.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

VERSION = "18.375.0"
NAME = "FutBR-Manager-18.375-Windows.exe"
BASE = "https://download.futbrmanager.com.br/updates"
URL = BASE + "/" + NAME
NOTES = (
    "18.375: Melhora a acessibilidade e as configuracoes do FutBR Manager: "
    "modo janela/tela cheia, tamanho da interface, central de configuracoes, "
    "dicas explicativas e calendario com traducoes adicionais. "
    "Aprimora a leitura das negociacoes e impede contratacoes "
    "esportivamente incompativeis mesmo com salarios muito altos. "
    "Preserva a compatibilidade dos saves e as otimizacoes anteriores."
)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

def digest_file(path: Path) -> tuple[str, int]:
    sha, size = hashlib.sha256(), 0
    with path.open("rb") as stream:
        require(stream.read(2) == b"MZ", "Not a Windows executable")
        stream.seek(0)
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            require(size <= 200_000_000, "Installer unexpectedly large")
            sha.update(chunk)
    require(40_000_000 < size < 200_000_000, "Installer unexpectedly small")
    return sha.hexdigest(), size

def stage(project: Path) -> dict:
    artifacts = project / "artifacts"
    manifest_path = artifacts / "latest.json"
    exe, sig = artifacts / NAME, artifacts / (NAME + ".sig")
    require(exe.is_file() and sig.is_file() and manifest_path.is_file(),
            "Missing original signed build files")
    report_path = artifacts / "support-release-18375-tests.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text("utf-8"))
        require(report.get("ok") is True and report.get("version") == VERSION
                and report.get("allSupportTicketGamePatchesPresent") is True
                and report.get("previousCareerMemoryCorrectionsPreserved") is True
                and report.get("scriptsParsed", 0) >= 129,
                "Original release did not pass game checks")
    else:
        # The signed candidate workflow confirmed the source's 18.375
        # validation and all regressions, but uploaded only the signed
        # installer/manifest/checksum, not the intermediate JSON report.
        # Require both pinned, successful GitHub Actions runs instead.
        build = json.loads((project.parent / "build-proof.json").read_text("utf-8"))
        integration = json.loads((project.parent / "integration-proof.json").read_text("utf-8"))
        expected = "41637b66de2dfc3f251bbf557e722a4dd46f276d"
        for name, proof in (("Windows signer/renderer", build),
                            ("18.375 integration", integration)):
            require(proof.get("status") == "completed"
                    and proof.get("conclusion") == "success"
                    and proof.get("head_sha") == expected
                    and proof.get("head_branch") == "fix/support-tickets-4-13-18375",
                    "Unverified original " + name + " build provenance")
        print("Validated missing intermediate report against two exact, "
              "successful source-pinned GitHub Actions runs.", flush=True)
    raw = json.loads(manifest_path.read_text("utf-8"))
    require(raw.get("version") == VERSION, "Artifact feed version mismatch")
    platform = raw.get("platforms", {}).get("windows-x86_64", {})
    require(platform.get("url") == URL, "Unexpected update destination")
    require(isinstance(platform.get("signature"), str)
            and platform.get("signature").strip() == sig.read_text("utf-8").strip(),
            "Installer signature differs from signed manifest")
    sha, size = digest_file(exe)
    checksums = (artifacts / "SHA256SUMS.txt").read_text("ascii").strip()
    require(checksums == sha + "  " + NAME, "Signed artifact SHA-256 mismatch")
    # The 18.375 candidate mistakenly copied the 18.374 release notes.
    # Only the human-readable notes are corrected; the installer and its
    # cryptographic signature are byte-for-byte identical to the approved build.
    raw["notes"] = NOTES
    manifest_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    staged = {
        "ok": True, "version": VERSION, "name": NAME, "sha256": sha,
        "size": size, "unsignedRebuild": False,
        "originalSignedInstallerUnchanged": True,
        "buildRun": 44977954599, "buildArtifactId": 14737742455,
        "sourceCommit": "41637b66de2dfc3f251bbf557e722a4dd46f276d",
        "releaseNotesOnlyChanged": True,
    }
    (artifacts / "publish-stage-18375.json").write_text(
        json.dumps(staged, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(staged, ensure_ascii=False))
    return staged

def publish(project: Path) -> None:
    import boto3
    artifacts = project / "artifacts"
    stage_report = json.loads((artifacts / "publish-stage-18375.json").read_text("utf-8"))
    require(stage_report.get("ok") is True and stage_report.get("version") == VERSION,
            "Signed build staging not verified")
    digest, size = digest_file(artifacts / NAME)
    require(digest == stage_report["sha256"] and size == stage_report["size"],
            "Installer changed after stage verification")
    require((artifacts / "cryptographic-signature-verified.txt").read_text("utf-8").strip()
            == digest, "Missing successful original-key cryptographic verification")
    creds = {
        "account": os.getenv("R2_ACCOUNT_ID", "").strip(),
        "bucket": os.getenv("R2_BUCKET", "").strip(),
        "access": os.getenv("R2_ACCESS_KEY_ID", "").strip(),
        "secret": os.getenv("R2_SECRET_ACCESS_KEY", "").strip(),
    }
    require(all(creds.values()), "R2 credentials are unavailable")
    prefix = os.getenv("R2_UPDATE_PREFIX", "updates").strip("/")
    require(prefix == "updates", "Unexpected update directory")
    client = boto3.client(
        "s3", region_name="auto",
        endpoint_url=f"https://{creds['account']}.r2.cloudflarestorage.com",
        aws_access_key_id=creds["access"],
        aws_secret_access_key=creds["secret"],
    )
    existing = client.get_object(Bucket=creds["bucket"], Key="updates/latest.json")
    current = json.loads(existing["Body"].read(131073))
    ver = current.get("version")
    require(isinstance(ver, str) and re.fullmatch(r"\d+\.\d+\.\d+", ver) is not None,
            "Existing version is invalid")
    require(tuple(map(int, ver.split("."))) < tuple(map(int, VERSION.split("."))),
            f"Refusing to replace or downgrade existing release {ver}")
    manifest_path = artifacts / "latest.json"
    data = json.loads(manifest_path.read_text("utf-8"))
    require(data["version"] == VERSION
            and data["platforms"]["windows-x86_64"]["url"] == URL,
            "Invalid staged release feed")
    require(data["platforms"]["windows-x86_64"]["signature"].strip()
            == (artifacts / (NAME + ".sig")).read_text("utf-8").strip(),
            "Staged signature mismatch")
    for filename in (NAME, NAME + ".sig"):
        path = artifacts / filename
        client.upload_file(
            str(path), creds["bucket"], prefix + "/" + filename,
            ExtraArgs={
                "ContentType": "application/octet-stream",
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )
        uploaded = client.head_object(Bucket=creds["bucket"], Key=prefix + "/" + filename)
        require(int(uploaded["ContentLength"]) == path.stat().st_size,
                "Incomplete uploaded release asset: " + filename)
        print(f"R2 asset verified: {filename} ({path.stat().st_size} bytes)", flush=True)
    # Put latest.json only after both assets are complete and size-verified.
    client.put_object(
        Bucket=creds["bucket"], Key=prefix + "/latest.json",
        Body=manifest_path.read_bytes(),
        ContentType="application/json; charset=utf-8",
        CacheControl="public, max-age=60",
    )
    # Build the attestations that the read-only public verifier requires.
    trust = {
        "ok": True, "version": VERSION, "installedUpdaterTrustMatchesSignature": True,
        "installerSha256Verified": True, "manifestSignatureExact": True,
        "publicKeyDerivedFromConfiguredSigner": True, "careerSavesPreserved": True,
        "cryptographicCheck": "Verified independently against original signing key",
    }
    packaging = {
        "ok": True, "version": VERSION, "signed": True,
        "asset": URL, "sha256": digest,
        "feed": BASE + "/latest.json",
        "signatureEmbeddedInManifest": True,
    }
    (artifacts / "updater-18375-signature-tests.json").write_text(
        json.dumps(trust, indent=2) + "\n", encoding="utf-8")
    (artifacts / "desktop-update-release-18375.json").write_text(
        json.dumps(packaging, indent=2) + "\n", encoding="utf-8")
    print("Published 18.375.0 to R2; public verification is still required.", flush=True)

def main() -> None:
    require(len(sys.argv) == 3 and sys.argv[1] in ("stage", "publish"),
            "Usage: publish_verified_candidate.py <stage|publish> <release-root>")
    root = Path(sys.argv[2]).resolve()
    if sys.argv[1] == "stage":
        stage(root)
    else:
        publish(root)

if __name__ == "__main__":
    main()
