# 교보도서관 캡쳐 매크로

macOS에서 교보도서관 앱의 페이지를 자동으로 캡쳐하여 PDF로 변환하는 CLI 도구입니다.

---

## 빠른 시작 (내 컴퓨터용)

### 1단계: 페이지 캡쳐

```bash
# 교보도서관 앱을 열고 1페이지로 이동한 후 실행
capture-pdf button -p [페이지수] -b 2763,1769 --confirm 2268,1022
```

**예시 (530페이지 캡쳐):**
```bash
capture-pdf button -p 530 -b 2763,1769 --confirm 2268,1022
```

### 2단계: PDF 변환

```bash
# 캡쳐된 이미지를 PDF로 변환 (원본 화질 유지)
capture-pdf compile -i ~/Desktop/book -o ~/Desktop/book.pdf --pattern "*.jpeg" --sort time
```

---

## 기능

- 앱 캡쳐 버튼 자동 클릭 (마우스 시뮬레이션)
- 경고 안내창 자동 확인
- 키보드 시뮬레이션을 통한 자동 페이지 넘김
- 캡쳐된 이미지들을 고화질 PDF로 병합
- 생성 시간 기준 페이지 정렬

## 요구사항

- macOS 12+ (Monterey, Ventura, Sonoma, Sequoia)
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python 패키지 관리자)
- 시스템 권한:
  - **손쉬운 사용 권한**: 시스템 환경설정 > 개인정보 보호 및 보안 > 손쉬운 사용

## 설치

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 설정
cd ~/my_project/capture_pdf
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e .
```

---

## 명령어 상세

### button - 캡쳐 버튼 클릭 모드 (권장)

```bash
capture-pdf button [옵션]
```

| 옵션 | 단축키 | 설명 | 내 설정 |
|------|--------|------|---------|
| `--pages` | `-p` | 캡쳐할 페이지 수 (필수) | - |
| `--button` | `-b` | 캡쳐 버튼 좌표 (필수) | `2763,1769` |
| `--confirm` | - | 확인 버튼 좌표 | `2268,1022` |
| `--delay` | `-d` | 페이지 전환 후 대기(초) | `1.0` |
| `--capture-delay` | `-c` | 캡쳐 버튼 클릭 후 대기(초) | `0.5` |

**동작 순서:**
1. 캡쳐 버튼 클릭 (2763, 1769)
2. 확인 버튼 클릭 (2268, 1022) - 안내창 닫기
3. 오른쪽 화살표 키 - 다음 페이지
4. 반복...

### compile - PDF 변환

```bash
capture-pdf compile [옵션]
```

| 옵션 | 단축키 | 설명 | 권장값 |
|------|--------|------|--------|
| `--input` | `-i` | 이미지 폴더 (필수) | `~/Desktop/book` |
| `--output` | `-o` | 출력 PDF 경로 (필수) | - |
| `--pattern` | - | 파일 패턴 | `*.jpeg` |
| `--sort` | - | 정렬 방식 (name/time/time-desc) | `time` |

> img2pdf를 사용하여 **원본 이미지를 그대로 PDF에 임베딩**합니다. 재압축 없이 100% 원본 화질이 유지됩니다.

### screenshot - 직접 스크린샷 모드

```bash
capture-pdf screenshot -p [페이지수] -o [출력파일] -r [x,y,w,h]
```

직접 화면을 캡쳐하는 모드입니다. button 모드를 권장합니다.

---

## 버튼 좌표 찾는 방법

### 방법 1: 명령어 실행 후 마우스 이동

```bash
sleep 3 && uv run python -c "from Quartz import CGEventCreate, CGEventGetLocation; e=CGEventCreate(None); loc=CGEventGetLocation(e); print(f'x={int(loc.x)}, y={int(loc.y)}')"
```

**사용법:**
1. 위 명령어 실행
2. 3초 안에 원하는 버튼 위에 마우스 올려놓기
3. 좌표 출력 확인

### 방법 2: macOS 기본 도구 (DigitalColor Meter)

1. Spotlight (Cmd + Space) → "DigitalColor Meter" 검색
2. 앱 실행 후 마우스를 원하는 위치로 이동
3. 창 제목에 표시되는 좌표 확인 (Location: x, y)

### 좌표 예시

| 버튼 | 좌표 (내 설정) |
|------|----------------|
| 캡쳐 버튼 | `2763,1769` |
| 확인 버튼 | `2268,1022` |

> ⚠️ 좌표는 화면 해상도와 앱 위치에 따라 다릅니다. 직접 확인하세요.

---

## 실행 전 체크리스트

- [ ] 교보도서관 앱에서 **1페이지** 표시
- [ ] 화면 보호기/잠자기 **비활성화** (시스템 환경설정 > 잠금화면)
- [ ] 손쉬운 사용 권한 허용
- [ ] 명령어 실행 후 **3초 내에 앱 창 클릭**

---

## 예상 소요 시간

| 페이지 수 | 예상 시간 (딜레이 1초) |
|-----------|------------------------|
| 100 | 약 3분 |
| 300 | 약 8분 |
| 530 | 약 13분 |

---

## 문제 해결

### "Accessibility permission not granted" 오류
→ 시스템 환경설정 > 개인정보 보호 및 보안 > 손쉬운 사용 > 터미널 체크

### 페이지가 제대로 넘어가지 않음
→ `--delay` 값을 늘려보세요 (예: `-d 1.5` 또는 `-d 2.0`)

### 캡쳐 버튼이 클릭되지 않음
→ 좌표 확인 후 `--button` 값 수정

### 확인 버튼이 클릭되지 않음
→ 좌표 확인 후 `--confirm` 값 수정

---

## 주의사항

- 본 도구는 **개인 학습 목적**으로만 사용하세요
- 캡쳐한 콘텐츠를 공유하거나 배포하는 것은 **저작권법 위반**입니다

---

## 개발

```bash
# 개발 의존성 설치
uv add --dev pytest pytest-mock ruff

# 테스트 실행
uv run pytest

# 린터 실행
uv run ruff check .
```

## 라이선스

MIT License
