"""Read-only proof that the public release is the exact verified build artifact.

No signing key is read, generated, or rotated. Cryptographic verification runs
in the pinned Windows build; this independent workflow checks its successful
step and compares public bytes with that build's authenticated artifact.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VERSION = "18.371.0"
BUILD_RUN = 44845753178
BUILD_SHA = "a78d08ecd57aa31288c4bef90e50a1e9aea8ba6f"
BUILD_BRANCH = "fix/desktop-18371-career-transitions"
BUILD_WORKFLOW = ".github/workflows/build-desktop-updater-18371.yml"
CRYPTO_STEP = "Cryptographically verify installer and gate publication"
ARTIFACT_STEP = "Upload verified signed installer and integrity reports"
ARTIFACT_NAME = "FutBR-Manager-18.371-Windows-Fast-Signed-Updater"
INSTALLER_NAME = "FutBR-Manager-18.371-Windows.exe"
HOST = "download.futbrmanager.com.br"
BASE = "https://" + HOST + "/updates/"
FEED = BASE + "latest.json"
INSTALLER = BASE + INSTALLER_NAME
SIGNATURE = INSTALLER + ".sig"
MIN_INSTALLER_BYTES = 40_000_000
MAX_INSTALLER_BYTES = 200_000_000
WAIT_SECONDS = 35 * 60
POLL_SECONDS = 30
JOB_METADATA_WAIT_SECONDS = 120


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_report(path, report):
    Path(path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report), flush=True)


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Unexpected redirect from the authenticated GitHub API")


def github_json(path):
    # The only authenticated requests go to this fixed API origin. The token is
    # provided only to wait-build, never to any public CDN request.
    request = urllib.request.Request("https://api.github.com" + path, headers={
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FutBR-Public-Release-Verification/18.371",
    })
    with urllib.request.build_opener(NoRedirects()).open(request, timeout=30) as response:
        data = response.read(2_000_001)
        require(response.status == 200 and len(data) <= 2_000_000,
                "Unexpected GitHub API response")
        return json.loads(data)


def wait_build(output):
    repository = os.environ["GITHUB_REPOSITORY"]
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository),
            "Unexpected GitHub repository identifier")
    prefix = "/repos/" + repository + "/actions/runs/" + str(BUILD_RUN)
    deadline = time.monotonic() + WAIT_SECONDS
    while True:
        run = github_json(prefix)
        require(run.get("id") == BUILD_RUN and run.get("head_sha") == BUILD_SHA,
                "The build run is not the pinned source commit")
        require(run.get("head_branch") == BUILD_BRANCH and run.get("path") == BUILD_WORKFLOW,
                "The build run has an unexpected branch or workflow")
        require(run.get("repository", {}).get("full_name") == repository,
                "The build belongs to a different repository")
        print(json.dumps({"buildRun": BUILD_RUN, "status": run.get("status"),
                          "conclusion": run.get("conclusion")}), flush=True)
        if run.get("status") == "completed":
            require(run.get("conclusion") == "success",
                    "The exact Windows build did not complete successfully")
            break
        require(time.monotonic() < deadline, "Timed out waiting for the exact Windows build")
        time.sleep(min(POLL_SECONDS, max(0, deadline - time.monotonic())))

    attempt = run.get("run_attempt")
    require(isinstance(attempt, int) and attempt > 0, "Missing successful build attempt")
    # The run endpoint can report completion before the jobs endpoint reflects
    # the final step conclusions. Wait for that metadata; never skip the gate.
    job_deadline = time.monotonic() + JOB_METADATA_WAIT_SECONDS
    while True:
        jobs = github_json(prefix + "/attempts/" + str(attempt) + "/jobs?per_page=100")
        observed_jobs = jobs.get("jobs", [])
        complete = jobs.get("total_count") == len(observed_jobs)
        successful = [job for job in observed_jobs if job.get("conclusion") == "success"]
        gated = []
        for job in successful:
            steps = job.get("steps", [])
            crypto = [step for step in steps if step.get("name") == CRYPTO_STEP]
            upload = [step for step in steps if step.get("name") == ARTIFACT_STEP]
            if (len(crypto) == len(upload) == 1
                    and crypto[0].get("conclusion") == upload[0].get("conclusion") == "success"
                    and crypto[0]["number"] < upload[0]["number"]):
                gated.append(job)
        if complete and len(gated) == 1:
            break
        require(time.monotonic() < job_deadline,
                "No complete job list with one successful cryptographic gate after waiting for metadata consistency")
        print(json.dumps({"buildJobMetadataPending": True,
                          "jobsObserved": len(observed_jobs), "jobsExpected": jobs.get("total_count"),
                          "matchingSuccessfulJobs": len(gated)}), flush=True)
        time.sleep(min(10, max(0, job_deadline - time.monotonic())))
    artifacts = github_json(prefix + "/artifacts?per_page=100")
    require(artifacts.get("total_count") == len(artifacts.get("artifacts", [])),
            "Incomplete build artifact list")
    matches = [item for item in artifacts["artifacts"] if item.get("name") == ARTIFACT_NAME]
    require(len(matches) == 1 and matches[0].get("expired") is False,
            "The verified build artifact is missing, ambiguous, or expired")
    artifact = matches[0]
    require(artifact.get("workflow_run", {}).get("id") == BUILD_RUN,
            "Artifact run does not match the pinned build")
    require(artifact.get("workflow_run", {}).get("head_sha") == BUILD_SHA,
            "Artifact commit does not match the pinned build")
    write_report(output, {
        "ok": True, "version": VERSION, "repository": repository,
        "buildRun": BUILD_RUN, "buildSha": BUILD_SHA, "buildAttempt": attempt,
        "buildWorkflow": BUILD_WORKFLOW, "buildConclusion": "success",
        "buildCryptographicStepSucceeded": True, "buildJobId": gated[0]["id"],
        "verifiedArtifactUploadedAfterCryptographicStep": True,
        "artifactName": ARTIFACT_NAME, "artifactId": artifact["id"],
        "artifactDigest": artifact.get("digest"),
    })


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


def open_official(url, accept):
    wanted = require_official_url(url)
    request = urllib.request.Request(url, headers={
        "User-Agent": "FutBR-Public-Release-Verification/18.371",
        "Cache-Control": "no-cache", "Accept-Encoding": "identity", "Accept": accept,
    })
    response = urllib.request.build_opener(OfficialRedirectsOnly()).open(request, timeout=60)
    try:
        require_official_url(response.geturl(), wanted.path)
        require(response.status == 200, "Expected HTTP 200 for the public release")
        require(response.headers.get("Content-Encoding", "identity").lower() in ("", "identity"),
                "Unexpected encoded public response")
        return response
    except Exception:
        response.close()
        raise


def read_small(url, limit, accept):
    with open_official(url, accept) as response:
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


def digest_installer(stream):
    digest = hashlib.sha256()
    size = 0
    first_bytes = b""
    while True:
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
    report = json.loads(read_local(directory / "updater-18371-signature-tests.json", 131072))
    require(report.get("version") == VERSION and all(report.get(key) is True for key in (
        "ok", "installedUpdaterTrustMatchesSignature", "installerSha256Verified",
        "manifestSignatureExact", "publicKeyDerivedFromConfiguredSigner")),
        "Missing successful updater trust report in the verified build artifact")
    release = json.loads(read_local(directory / "desktop-update-release-18371.json", 131072))
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


def wait_public_manifest(expected):
    deadline = time.monotonic() + WAIT_SECONDS
    while True:
        try:
            body = read_small(FEED, 131072, "application/json")
            manifest = json.loads(body)
            version = manifest.get("version")
            print(json.dumps({"publicFeedVersion": version, "expected": VERSION}), flush=True)
            if version == VERSION:
                require(body == expected, "Public 18.371 manifest differs from the verified build artifact")
                return body
            require(isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+", version),
                    "Public feed contains an unexpected version")
            require(tuple(map(int, version.split("."))) < (18, 371, 0),
                    "Public feed has already moved past the pinned release")
        except urllib.error.HTTPError as error:
            if error.code not in (404, 429, 500, 502, 503, 504):
                raise
            print(json.dumps({"publicFeedHttpRetry": error.code}), flush=True)
        except (urllib.error.URLError, TimeoutError) as error:
            print(json.dumps({"publicFeedNetworkRetry": type(error).__name__}), flush=True)
        require(time.monotonic() < deadline, "Timed out waiting for the public 18.371 feed")
        time.sleep(min(POLL_SECONDS, max(0, deadline - time.monotonic())))


def verify_public(source_path, artifact_dir, output):
    source = json.loads(Path(source_path).read_text(encoding="utf-8"))
    require(source.get("ok") is True and source.get("buildRun") == BUILD_RUN
            and source.get("buildSha") == BUILD_SHA and source.get("buildConclusion") == "success"
            and source.get("buildCryptographicStepSucceeded") is True
            and source.get("verifiedArtifactUploadedAfterCryptographicStep") is True
            and source.get("artifactName") == ARTIFACT_NAME,
            "Missing authenticated evidence of the exact successful Windows build")
    manifest_bytes, sig_bytes, expected, artifact_size = trusted_artifact(Path(artifact_dir))
    wait_public_manifest(manifest_bytes)
    public_sig = read_small(SIGNATURE, 16384, "application/octet-stream")
    require(public_sig == sig_bytes, "Public .sig bytes differ from the verified build artifact")
    with open_official(INSTALLER, "application/octet-stream") as response:
        declared = response.headers.get("Content-Length")
        require(declared is None or int(declared) == artifact_size,
                "Public installer Content-Length differs from the verified build")
        digest, public_size = digest_installer(response)
    require(public_size == artifact_size and digest == expected,
            "Public executable size or SHA-256 differs from the verified signed build")
    # Recheck the feed after downloading to avoid claiming a release that was
    # replaced while its executable was being read.
    require(read_small(FEED, 131072, "application/json") == manifest_bytes,
            "Public feed changed during verification")
    report = {
        **source, "feed": FEED, "installer": INSTALLER, "signatureUrl": SIGNATURE,
        "httpStatus": 200, "officialOriginOnly": True,
        "publicManifestBytesMatchBuild": True, "publicSignatureBytesMatchBuild": True,
        "completeInstallerDownloaded": True, "installerBytes": public_size,
        "sha256": digest, "sha256MatchesVerifiedSignedBuild": True,
        "sha256MatchesArtifactChecksumAndReleaseReport": True,
        "publicFeedStableDuringDownload": True,
        "newCryptographicVerificationPerformed": False,
        "verificationBasis": "Exact public bytes match the artifact uploaded after successful Minisign verification in the pinned Windows build",
    }
    write_report(output, report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## FutBR 18.371 public release verified\n\n"
                          f"- Build run: `{BUILD_RUN}`, commit `{BUILD_SHA}`.\n"
                          f"- Installer: {INSTALLER}\n"
                          f"- Bytes: `{public_size}`.\n"
                          f"- SHA-256: `{digest}`.\n"
                          "- Feed, signature and complete executable match the verified build artifact.\n"
                          "- Cryptographic verification succeeded in the source build; this workflow verifies public distribution equivalence.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    wait = subparsers.add_parser("wait-build")
    wait.add_argument("--output", required=True)
    verify = subparsers.add_parser("verify-public")
    verify.add_argument("--source", required=True)
    verify.add_argument("--artifact-dir", required=True)
    verify.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.command == "wait-build":
            wait_build(args.output)
        else:
            verify_public(args.source, args.artifact_dir, args.output)
    except Exception as error:
        write_report(args.output, {
            "ok": False, "version": VERSION, "buildRun": BUILD_RUN,
            "buildSha": BUILD_SHA, "stage": args.command,
            "errorType": type(error).__name__, "error": str(error),
        })
        raise


if __name__ == "__main__":
    main()
