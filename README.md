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

업스트림 Release zip의 `Release/Unity` 폴더와 같은 구성입니다. 소스 수정 없이 업스트림 csproj를 그대로 빌드합니다.

- `Runtime/Facepunch.Steamworks.{Win64,Win32,Posix}.dll` — 업스트림 csproj를 `net46` Release로 빌드한 결과 (+ pdb, xml)
- `Runtime/redistributable_bin` — `steam_api` 네이티브 라이브러리
- 플랫폼별 DLL 선택 등 모든 `.meta`는 업스트림 `UnityPlugin` 폴더의 것을 그대로 사용

## 업스트림 동기화

GitHub Actions의 **Sync upstream** 워크플로가 매일 00:00 UTC(수동 실행도 가능)에 업스트림의 최신 Release 태그를 `package.json`의 `version`과 비교합니다. 버전이 다를 때만 패키지를 다시 생성해 `main`에 커밋하고 같은 이름의 태그를 붙입니다.

로컬에서 직접 생성하려면 (.NET SDK 필요):

```bash
git clone --depth 1 --branch <tag> https://github.com/Facepunch/Facepunch.Steamworks.git upstream
python3 "Tools~/build_package.py" upstream .
```

## 라이선스

MIT. 원본 저작권은 Facepunch Studios에 있습니다. [LICENSE.md](LICENSE.md) 참고.
