from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# This script is only called after the signed installer and all regression
# reports have been verified. The mutable latest.json is published LAST.
FILES = ("FutBR-Manager-18.351-Windows.exe", "FutBR-Manager-18.351-Windows.exe.sig")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: publish_signed_update_r2_18351.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    artifacts = project / "artifacts"
    manifest_path = artifacts / "latest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != "18.351.0":
        raise RuntimeError("Cannot publish manifest for another version")
    if manifest["platforms"]["windows-x86_64"]["url"].split("/")[-1] != FILES[0]:
        raise RuntimeError("Update URL must match signed installer")
    creds = {
        "account": os.environ.get("R2_ACCOUNT_ID", "").strip(),
        "bucket": os.environ.get("R2_BUCKET", "").strip(),
        "access": os.environ.get("R2_ACCESS_KEY_ID", "").strip(),
        "secret": os.environ.get("R2_SECRET_ACCESS_KEY", "").strip(),
    }
    if not all(creds.values()):
        raise RuntimeError("R2 update publishing requires account, bucket, access and secret")
    import boto3
    client = boto3.client(
        "s3", region_name="auto",
        endpoint_url="https://" + creds["account"] + ".r2.cloudflarestorage.com",
        aws_access_key_id=creds["access"],
        aws_secret_access_key=creds["secret"],
    )
    prefix = os.environ.get("R2_UPDATE_PREFIX", "updates").strip("/")
    for name in FILES:
        path = artifacts / name
        if not path.is_file() or path.stat().st_size < 32:
            raise RuntimeError("Signed update artifact missing: " + name)
        client.upload_file(str(path), creds["bucket"], prefix + "/" + name,
                           ExtraArgs={"ContentType": "application/octet-stream",
                                      "CacheControl": "public, max-age=31536000, immutable"})
        response = client.head_object(Bucket=creds["bucket"], Key=prefix + "/" + name)
        if int(response["ContentLength"]) != path.stat().st_size:
            raise RuntimeError("R2 artifact did not retain expected size: " + name)
        print("Published and verified", name, path.stat().st_size)
    # The public manifest is the last write so clients never see half a release.
    client.put_object(Bucket=creds["bucket"], Key=prefix + "/latest.json",
                      Body=manifest_path.read_bytes(),
                      ContentType="application/json; charset=utf-8",
                      CacheControl="public, max-age=60")
    print("Published version 18.351.0 to R2; verify the public Pages route separately.")


if __name__ == "__main__":
    main()
