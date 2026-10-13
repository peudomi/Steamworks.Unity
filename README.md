# Steamworks.Unity

[Facepunch.Steamworks](https://github.com/Facepunch/Facepunch.Steamworks)를 Unity Package Manager에서 git URL로 바로 설치할 수 있도록 소스 패키지로 재구성한 레포입니다.

## 설치

Package Manager → `+` → **Install package from git URL...**

```
https://github.com/peudomi/Steamworks.Unity.git
```

특정 업스트림 버전에 고정하려면 태그를 붙입니다.

```
https://github.com/peudomi/Steamworks.Unity.git#2.5.2
```

> Steamworks.NET과 함께 설치할 수 없습니다. 둘 다 `Steamworks` 네임스페이스와 `steam_api` 네이티브 라이브러리를 사용합니다.

## 구성

- `Runtime/Source` — 업스트림 `Facepunch.Steamworks/` C# 소스 (어셈블리 `Facepunch.Steamworks`)
- `Runtime/Plugins` — `steam_api` 네이티브 라이브러리 (Windows x64, macOS Universal, Linux x64)

업스트림 대비 변경점은 Unity 컴파일을 위한 자동 패치뿐입니다.

- `Utility/Platform.cs` — `PLATFORM_*` define을 `UNITY_*` define으로 대체
- C# 10 file-scoped namespace → 블록 namespace (Unity는 C# 9까지 지원)

## 업스트림 동기화

GitHub Actions의 **Sync upstream** 워크플로가 매일 00:00 UTC(수동 실행도 가능)에 업스트림의 최신 Release 태그를 `package.json`의 `version`과 비교합니다. 버전이 다를 때만 패키지를 다시 생성해 `main`에 커밋하고 같은 이름의 태그를 붙입니다.

로컬에서 직접 생성하려면:

```bash
git clone --depth 1 --branch <tag> https://github.com/Facepunch/Facepunch.Steamworks.git upstream
python3 "Tools~/build_package.py" upstream . <tag>
```

## 라이선스

MIT. 원본 저작권은 Facepunch Studios에 있습니다. [LICENSE.md](LICENSE.md) 참고.
