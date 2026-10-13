#!/usr/bin/env python3
"""Facepunch.Steamworks 업스트림을 원본 Release 의 Unity 폴더와 동일하게 빌드해 UPM 패키지로 만든다.

사용법: build_package.py <upstream_dir> <package_root>

- Win64 / Win32 / Posix csproj 를 net46 Release 로 빌드 (업스트림 Release zip 의 Unity 폴더와 같은 구성)
- 업스트림 UnityPlugin 폴더(.meta, 네이티브 steam_api 포함)를 Runtime 으로 복사하고 빌드 결과를 넣는다
- package.json version 을 업스트림 버전으로 갱신
- 패키지 루트/Runtime 폴더 .meta 생성 (git 패키지는 immutable 이라 .meta 필수)
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_NAME = "com.peudomi.steamworks"
PLATFORMS = ["Win64", "Win32", "Posix"]
FRAMEWORK = "net46"


def guid_for(rel_path: str) -> str:
    return hashlib.md5(f"{PACKAGE_NAME}/{rel_path}".encode()).hexdigest()


def default_meta(guid, path: Path):
    if path.is_dir():
        return f"fileFormatVersion: 2\nguid: {guid}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
    if path.name == "package.json":
        return f"fileFormatVersion: 2\nguid: {guid}\nPackageManifestImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
    return f"fileFormatVersion: 2\nguid: {guid}\nTextScriptImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"


def build(upstream: Path) -> Path:
    project_dir = upstream / "Facepunch.Steamworks"
    for platform in PLATFORMS:
        csproj = project_dir / f"Facepunch.Steamworks.{platform}.csproj"
        subprocess.run(["dotnet", "restore", str(csproj)], check=True)
    for platform in PLATFORMS:
        csproj = project_dir / f"Facepunch.Steamworks.{platform}.csproj"
        subprocess.run(
            ["dotnet", "build", str(csproj), "--no-restore", "-c", "Release", "-f", FRAMEWORK, "-nologo"],
            check=True,
        )
    return project_dir / "bin" / "Release" / FRAMEWORK


def upstream_version(upstream: Path) -> str:
    targets = (upstream / "Facepunch.Steamworks" / "Facepunch.Steamworks.targets").read_text(encoding="utf-8-sig")
    match = re.search(r"<PackageVersion>([^<]+)</PackageVersion>", targets)
    if not match:
        sys.exit("업스트림 버전을 찾을 수 없습니다.")
    return match.group(1).strip()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    upstream, root = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()

    output = build(upstream)

    runtime = root / "Runtime"
    if runtime.exists():
        shutil.rmtree(runtime)
    shutil.copytree(upstream / "UnityPlugin", runtime)

    # UnityPlugin 에는 빌드 결과물의 .meta 만 커밋되어 있다
    for platform in PLATFORMS:
        for ext in ("dll", "pdb", "xml"):
            name = f"Facepunch.Steamworks.{platform}.{ext}"
            if not (runtime / f"{name}.meta").exists():
                sys.exit(f"업스트림 UnityPlugin 에 {name}.meta 가 없습니다. 구성이 바뀌었는지 확인하세요.")
            shutil.copy2(output / name, runtime / name)

    manifest_path = root / "package.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = upstream_version(upstream)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    shutil.copy2(upstream / "LICENSE", root / "LICENSE.md")

    for path in [root / "package.json", root / "README.md", root / "LICENSE.md", runtime]:
        meta = Path(str(path) + ".meta")
        if not meta.exists():
            meta.write_text(default_meta(guid_for(path.relative_to(root).as_posix()), path), encoding="utf-8")

    missing = [p for p in runtime.rglob("*") if p.suffix != ".meta" and not Path(str(p) + ".meta").exists()]
    if missing:
        sys.exit("다음 에셋에 .meta 가 없습니다:\n" + "\n".join(str(p.relative_to(root)) for p in missing))

    print(f"패키지 생성 완료: {manifest['version']}")


if __name__ == "__main__":
    main()
