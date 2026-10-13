#!/usr/bin/env python3
"""Facepunch.Steamworks 업스트림 소스를 UPM 패키지 구조로 변환한다.

사용법: build_package.py <upstream_dir> <package_root> <upstream_tag>

- upstream 소스(.cs)를 Runtime/Source 로 복사
- Unity 용 패치 적용 (플랫폼 define, C# 10 file-scoped namespace)
- 네이티브 steam_api 라이브러리를 Runtime/Plugins 로 복사
- 모든 에셋에 결정적 GUID 의 .meta 생성 (git 패키지는 immutable 이라 .meta 필수)
- package.json version 을 업스트림 버전으로 갱신
"""

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

PACKAGE_NAME = "com.peudomi.steamworks"

# 업스트림 Platform.cs 는 csproj 의 PLATFORM_* define 에 의존한다.
# Unity 에서는 csproj 가 없으니 UNITY_* define 으로 대신 정의한다.
PLATFORM_DEFINES = """\
// [Steamworks.Unity] Unity 플랫폼 define 으로 업스트림 PLATFORM_* define 을 대체
#if UNITY_EDITOR_WIN || (UNITY_STANDALONE_WIN && !UNITY_EDITOR)
#define PLATFORM_WIN64
#else
#define PLATFORM_POSIX
#endif

"""

FILE_SCOPED_NS = re.compile(r"^namespace\s+([\w.]+)\s*;\s*$", re.MULTILINE)

NATIVE_PLUGINS = {
    # upstream 상대경로 -> (패키지 내 경로, 에디터 OS, 에디터 CPU, 스탠드얼론 타깃, 스탠드얼론 CPU)
    "UnityPlugin/redistributable_bin/win64/steam_api64.dll":
        ("Runtime/Plugins/Windows/x86_64/steam_api64.dll", "Windows", "x86_64", "Win64", "x86_64"),
    "UnityPlugin/redistributable_bin/osx/libsteam_api.dylib":
        ("Runtime/Plugins/macOS/libsteam_api.dylib", "OSX", "AnyCPU", "OSXUniversal", "AnyCPU"),
    "UnityPlugin/redistributable_bin/linux64/libsteam_api.so":
        ("Runtime/Plugins/Linux/x86_64/libsteam_api.so", "Linux", "x86_64", "Linux64", "x86_64"),
}

STANDALONE_TARGETS = ["Linux64", "OSXUniversal", "Win", "Win64"]


def guid_for(rel_path: str) -> str:
    return hashlib.md5(f"{PACKAGE_NAME}/{rel_path}".encode()).hexdigest()


def plugin_meta(guid, editor_os, editor_cpu, target, target_cpu):
    exclude = "\n".join(
        f"        Exclude {t}: {0 if t == target else 1}" for t in STANDALONE_TARGETS
    )
    standalone = "".join(
        f"""  - first:
      Standalone: {t}
    second:
      enabled: {1 if t == target else 0}
      settings:
        CPU: {target_cpu if t == target else 'None'}
"""
        for t in STANDALONE_TARGETS
    )
    return f"""fileFormatVersion: 2
guid: {guid}
PluginImporter:
  externalObjects: {{}}
  serializedVersion: 2
  iconMap: {{}}
  executionOrder: {{}}
  defineConstraints: []
  isPreloaded: 0
  isOverridable: 0
  isExplicitlyReferenced: 0
  validateReferences: 1
  platformData:
  - first:
      : Any
    second:
      enabled: 0
      settings:
        Exclude Editor: 0
{exclude}
  - first:
      Any:
    second:
      enabled: 0
      settings: {{}}
  - first:
      Editor: Editor
    second:
      enabled: 1
      settings:
        CPU: {editor_cpu}
        DefaultValueInitialized: true
        OS: {editor_os}
{standalone}  userData:
  assetBundleName:
  assetBundleVariant:
"""


def default_meta(guid, path: Path):
    if path.is_dir():
        return f"fileFormatVersion: 2\nguid: {guid}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
    ext = path.suffix.lower()
    if ext == ".cs":
        return f"fileFormatVersion: 2\nguid: {guid}\nMonoImporter:\n  externalObjects: {{}}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n  icon: {{instanceID: 0}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
    if ext == ".asmdef":
        return f"fileFormatVersion: 2\nguid: {guid}\nAssemblyDefinitionImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
    if path.name == "package.json":
        return f"fileFormatVersion: 2\nguid: {guid}\nPackageManifestImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
    if ext in (".md", ".txt", ".json"):
        return f"fileFormatVersion: 2\nguid: {guid}\nTextScriptImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
    return f"fileFormatVersion: 2\nguid: {guid}\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n"


def copy_sources(upstream: Path, runtime: Path):
    src_root = upstream / "Facepunch.Steamworks"
    dst_root = runtime / "Source"
    for src in sorted(src_root.rglob("*.cs")):
        rel = src.relative_to(src_root)
        if rel.parts[0] in ("bin", "obj"):
            continue
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8-sig")

        if rel.as_posix() == "Utility/Platform.cs":
            if "#if PLATFORM_WIN64" not in text:
                sys.exit("Platform.cs 구조가 바뀌었습니다. 패치를 확인하세요.")
            text = PLATFORM_DEFINES + text

        # Unity 는 C# 9 까지라 file-scoped namespace 를 블록 namespace 로 바꾼다
        if FILE_SCOPED_NS.search(text):
            if len(FILE_SCOPED_NS.findall(text)) != 1:
                sys.exit(f"{rel}: file-scoped namespace 가 여러 개입니다.")
            text = FILE_SCOPED_NS.sub(r"namespace \1\n{", text).rstrip() + "\n}\n"

        dst.write_text(text, encoding="utf-8")


def copy_natives(upstream: Path, root: Path):
    for src_rel, (dst_rel, editor_os, editor_cpu, target, target_cpu) in NATIVE_PLUGINS.items():
        src = upstream / src_rel
        if not src.exists():
            sys.exit(f"네이티브 라이브러리를 찾을 수 없습니다: {src_rel}")
        dst = root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        meta = plugin_meta(guid_for(dst_rel), editor_os, editor_cpu, target, target_cpu)
        Path(str(dst) + ".meta").write_text(meta, encoding="utf-8")


def write_metas(root: Path):
    targets = [root / "package.json", root / "README.md", root / "LICENSE.md", root / "Runtime"]
    targets += sorted((root / "Runtime").rglob("*"))
    for path in targets:
        if path.suffix == ".meta" or not path.exists():
            continue
        meta = Path(str(path) + ".meta")
        if meta.exists():
            continue
        rel = path.relative_to(root).as_posix()
        meta.write_text(default_meta(guid_for(rel), path), encoding="utf-8")


def upstream_version(upstream: Path) -> str:
    targets = (upstream / "Facepunch.Steamworks" / "Facepunch.Steamworks.targets").read_text(encoding="utf-8-sig")
    match = re.search(r"<PackageVersion>([^<]+)</PackageVersion>", targets)
    if not match:
        sys.exit("업스트림 버전을 찾을 수 없습니다.")
    return match.group(1).strip()


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    upstream, root, tag = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]

    runtime = root / "Runtime"
    if runtime.exists():
        shutil.rmtree(runtime)
    if Path(str(runtime) + ".meta").exists():
        Path(str(runtime) + ".meta").unlink()
    runtime.mkdir()

    copy_sources(upstream, runtime)
    copy_natives(upstream, root)

    (runtime / "Facepunch.Steamworks.asmdef").write_text(json.dumps({
        "name": "Facepunch.Steamworks",
        "rootNamespace": "Steamworks",
        "references": [],
        "includePlatforms": [],
        "excludePlatforms": [],
        "allowUnsafeCode": True,
        "overrideReferences": False,
        "precompiledReferences": [],
        "autoReferenced": True,
        "defineConstraints": [],
        "versionDefines": [],
        "noEngineReferences": False,
    }, indent=4) + "\n", encoding="utf-8")

    # 업스트림 csproj 의 NoWarn 과 맞춘다
    (runtime / "csc.rsp").write_text("-nowarn:0618,0219,1591\n", encoding="utf-8")

    manifest_path = root / "package.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["version"] = upstream_version(upstream)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    shutil.copy2(upstream / "LICENSE", root / "LICENSE.md")

    write_metas(root)
    print(f"패키지 생성 완료: {manifest['version']} (upstream {tag})")


if __name__ == "__main__":
    main()
