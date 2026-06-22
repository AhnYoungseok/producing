# Hit Song Lab

Hit Song Lab은 히트곡의 창작 원리를 데이터로 축적하고 통계화하여, 사용자가 자신만의 새 노래를 설계하도록 돕는 대화형 AI 작곡 연구소입니다.

핵심 흐름은 다음과 같습니다.

```text
YouTube Reference Analysis
-> Reference Song Analysis 프로필 생성
-> 곡별 프로듀서 관점 특징 저장
-> 장르/국가/시대/BPM/감정별 통계화
-> 공통 패턴 요약
-> Composer Coach에서 새 노래 설계
```

## 핵심 원칙

- YouTube 링크는 레퍼런스곡을 식별하고 허용된 메타데이터를 수집하는 시작점입니다.
- 실제 음악적 특징은 공개 음악 데이터, 사용자가 입력한 가사/코드/메모, Data Confidence, 프로듀서 관점 추론을 함께 사용해 정리합니다.
- 신호 기반 BPM, Key, chroma, energy, loudness 분석은 사용자가 권한을 가진 오디오 파일을 별도로 제공했을 때만 수행합니다.
- 기존 곡의 멜로디, 가사, 식별 가능한 편곡을 그대로 복제하지 않습니다.
- 최종 결과는 표절이 아니라 창작 원리의 일반화여야 합니다.

앱의 안내 문구:

```text
Hit Song Lab은 기존 곡을 복제하기 위한 도구가 아닙니다.
히트곡의 창작 원리를 분석하고, 사용자가 자신만의 새로운 음악을 만들도록 돕는 창작 보조 도구입니다.
```

## 주요 기능

- YouTube Reference Analysis: 링크 기반 레퍼런스곡 등록
- Reference Song Analysis: 제목, 채널, 썸네일, 길이, 게시일 등 메타데이터 기반 연구 프로필 생성
- Chord and Structure Analysis: 사용자가 입력한 코드 진행, 곡 구조, 후크 위치, 가사 테마 저장
- Producer Research Mode: 컨셉, 구조, 화성, 멜로디/후크, 가사, 리듬, 편곡, 보컬, 믹싱, 히트 포인트 분석
- Hit Song Research Mode: 여러 곡의 특징을 누적해 공통 패턴과 창작 적용 원리 요약
- Song Feature Database: BPM, Key, 장르, 국가, 발매연도, 코드 진행, 후크 유형, 감정 키워드, 편곡 특징 저장
- Chart/Statistics Dashboard: 평균 BPM, BPM 분포, Key 분포, 후크 유형, 제목 사용 위치, 편곡/보컬/히트 포인트 Top 10 시각화
- Pattern Lab: 여러 곡을 선택해 공통 패턴 추출
- Composer Coach: 분석 데이터를 바탕으로 컨셉, 감정선, 구조, 가사, 코드, 멜로디, 후크, 편곡, 보컬, 믹싱 방향 설계
- Local Library Export: PC 저장소에 CSV/JSON으로 장르별 곡 데이터 축적
- Auto Reference Batch: 백엔드가 켜져 있는 동안 중복 없는 실제 히트곡 레퍼런스를 10분마다 10곡씩 자동 누적
- Hook Lab: 가사 후크 단서, 멜로디 간격/리듬, 후크 위치, 가사 전문 입력 상태 확인

## 기술 스택

- Frontend: Next.js, TypeScript, Tailwind CSS, React Hook Form
- Backend: FastAPI, Python, SQLite
- Audio module: ffmpeg, librosa, numpy, scipy
- Metadata/research modules: YouTube metadata service, MusicBrainz, optional Last.fm, optional Spotify
- AI/report layer: template-based MVP with `ai_service.py` extension point

## 프로젝트 구조

```text
hit-song-lab/
  frontend/
    app/
    components/
    lib/
    types/
  backend/
    app/
      api/
      services/
      models/
      db/
      storage/
    tests/
  docs/
  sample_data/
  README.md
```

## 설치 준비

- Python 3.10+
- Node.js 20+
- ffmpeg

ffmpeg 확인:

```bash
ffmpeg -version
```

## 백엔드 실행

Windows:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8100
```

macOS/Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8100
```

## 프론트엔드 실행

Windows:

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev -- --port 3100
```

macOS/Linux:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev -- --port 3100
```

## 환경 변수

Backend `.env`:

```bash
APP_NAME=Hit Song Lab API
APP_ENV=development
DATABASE_URL=sqlite:///./data/hit_song_lab.db
STORAGE_DIR=./storage
EXPORT_DIR=./exports/hit_song_library
FRONTEND_ORIGIN=http://localhost:3100
MAX_UPLOAD_MB=50
AUDIO_SAMPLE_RATE=22050

AUTO_REFERENCE_BATCH_ENABLED=true
AUTO_REFERENCE_BATCH_INTERVAL_SECONDS=600
AUTO_REFERENCE_BATCH_SIZE=10
AUTO_REFERENCE_BATCH_RUN_ON_STARTUP=true

LASTFM_API_KEY=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
```

Frontend `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8100/api
```

## 데이터베이스와 저장소

SQLite DB는 백엔드 시작 시 자동 생성됩니다.

```text
backend/data/hit_song_lab.db
```

곡 데이터 export 위치:

```text
backend/exports/hit_song_library/all_songs.csv
backend/exports/hit_song_library/all_songs.json
backend/exports/hit_song_library/genre_index.csv
backend/exports/hit_song_library/by_genre/<genre>.csv
backend/exports/hit_song_library/by_genre/<genre>.json
```

이 파일들은 Excel, Google Sheets, GitHub 저장소 관리에 바로 활용할 수 있는 형태입니다.

## 주요 API

- `POST /api/research/youtube`: YouTube Reference Analysis 프로필 생성
- `GET /api/youtube/metadata?url=...`: 허용된 YouTube 메타데이터 미리보기
- `POST /api/research/next-reference-batch`: 중복 없는 신규 레퍼런스곡 10곡 수동 추가
- `GET /api/research/auto-batch/status`: 자동 누적 작업 상태 확인
- `POST /api/research/auto-batch/run-now`: 자동 누적 배치를 즉시 1회 실행
- `POST /api/analyze`: 권한 오디오 파일 기반 신호 분석
- `GET /api/songs`: Song Library 목록
- `GET /api/songs/{song_id}`: 곡 상세
- `GET /api/songs/{song_id}/analysis`: 곡 분석 결과
- `GET /api/library/statistics`: 차트/통계/패턴 요약 데이터
- `POST /api/library/export`: 장르별 CSV/JSON export
- `POST /api/patterns/extract`: 선택 곡 공통 패턴 추출
- `POST /api/projects`: 새 곡 프로젝트 생성
- `POST /api/projects/{project_id}/blueprint`: 신곡 제작 설계도 생성
- `POST /api/composer/{project_id}/chat`: 대화형 Composer Coach 진행

## Reference Analysis 예시

```bash
curl -X POST http://localhost:8100/api/research/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=example",
    "lyrics_text": "사용자가 직접 입력한 가사",
    "chord_progression": "Verse: I - V - vi - IV / Chorus: IV - V - iii - vi",
    "analysis_notes": "72 BPM, A major, chorus starts around 50s, final chorus adds adlibs"
  }'
```

## 데이터 신뢰도

각 음악 특징은 Data Confidence를 가집니다.

- `high`: 신뢰 가능한 구조화 API 또는 사용자가 명확히 제공한 정보
- `medium`: 여러 출처 또는 메타데이터와 사용자 메모의 조합으로 추론한 정보
- `low`: 제한된 제목/설명/메모를 바탕으로 한 초기 추정

## 테스트

Backend:

```bash
cd backend
set AUTO_REFERENCE_BATCH_ENABLED=false
.venv\Scripts\python.exe -m pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## 현재 작업 문서

- `PROJECT_STATUS.md`: 현재 구현 상태와 실행 방법
- `TODO.md`: 우선순위별 다음 할 일
- `ISSUES.md`: 발견한 문제, 위험 요소, 저작권/YouTube 주의사항
- `CHANGELOG.md`: 최근 수정 내역
- `NEXT_STEPS.md`: 돌아왔을 때 바로 이어서 할 작업
- `docs/analysis_schema.md`: 히트곡 분석 항목 스키마
- `sample_data/songs.json`: 실제 데이터로 교체 가능한 예시 데이터 구조

## 자동 누적 주의

`AUTO_REFERENCE_BATCH_ENABLED=true`이면 백엔드 서버 시작 시 10곡을 즉시 추가하고, 이후 `AUTO_REFERENCE_BATCH_INTERVAL_SECONDS`마다 10곡씩 추가합니다.
학교 PC에서 데이터가 자동으로 늘어나는 것을 원하지 않으면 `backend/.env`에서 다음처럼 끄세요.

```bash
AUTO_REFERENCE_BATCH_ENABLED=false
```

이 자동 누적은 로컬 서버와 PC가 켜져 있을 때만 동작합니다. PC를 꺼도 계속 실행하려면 GitHub Actions나 클라우드 서버로 옮겨야 합니다.

## MVP 범위

- YouTube 링크 기반 레퍼런스곡 등록
- 곡 식별 및 메타데이터 저장
- 사용자가 입력한 가사, 코드 진행, 메모 저장
- 템플릿 기반 프로듀서 관점 12섹션 분석 리포트
- Data Confidence가 포함된 곡별 특징 DB
- 장르별 CSV/JSON export
- 통계 차트와 패턴 요약
- 신곡 프로젝트와 Composer Coach 설계도 생성

## 향후 확장 계획

- `reference_audio_analysis`
- `music_information_retrieval`
- `chord_structure_analyzer`
- Spotify/MusicBrainz/Last.fm 연동 강화
- 섹션별 에너지 그래프
- 코드 진행 시각화
- 가사 감정선 그래프
- 레퍼런스곡 묶음 추천
- 발라드/K-pop/글로벌 팝 특화 모드
- PDF 리포트 export
