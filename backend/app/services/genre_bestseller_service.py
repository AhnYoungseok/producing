from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from app.db.database import SQLiteStore, make_id
from app.services.hit_song_researcher import build_analysis_from_research_profile, build_structured_profile, confidence_field
from app.services.report_generator import generate_full_report
from app.services.statistics_service import build_hit_song_statistics


GENRE_BESTSELLER_CATALOG: dict[str, list[dict[str, Any]]] = {
    "K-pop Ballad": [
        {
            "title": "너였다면",
            "artist": "정승환",
            "country": "KR",
            "release_year": 2016,
            "bpm": 72,
            "key": "A major",
            "chord_progression": "Verse: I - V - vi - IV\nPre-Chorus: ii - V - iii - vi\nChorus: IV - V - iii - vi\nBridge: ii - V - I - vi",
            "mood": ["그리움", "절제", "감정 고조"],
            "lyric_theme": "이별 후 남은 그리움",
            "hook_type": "lyric + melody hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 55,
            "arrangement": "piano-first gradual layering with strings and full-band final chorus",
            "vocal": "restrained verse, open chorus, emotional final lift",
            "mixing": "front vocal, wide strings, controlled low end",
            "hit_factor": "후렴 첫 구간의 직접적인 감정 문장과 보컬 고조",
            "takeaway": "초반 절제, 후렴 집중, 마지막 확장을 새 곡 구조로 일반화한다.",
        },
        {
            "title": "그대라는 시",
            "artist": "태연",
            "country": "KR",
            "release_year": 2019,
            "bpm": 76,
            "key": "D major",
            "chord_progression": "Verse: I - V - vi - IV\nPre-Chorus: ii - V - I\nChorus: IV - V - iii - vi",
            "mood": ["따뜻함", "서정", "그리움"],
            "lyric_theme": "상대를 시처럼 기억하는 사랑",
            "hook_type": "title phrase hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 48,
            "arrangement": "warm piano, pad, strings, restrained drums",
            "vocal": "clean emotional tone with elegant chorus lift",
            "mixing": "bright vocal center, soft wide ambience",
            "hit_factor": "제목 이미지와 후렴 정서가 자연스럽게 결합",
            "takeaway": "제목을 이미지화해 후렴의 기억 장치로 재설계한다.",
        },
        {
            "title": "밤편지",
            "artist": "아이유",
            "country": "KR",
            "release_year": 2017,
            "bpm": 74,
            "key": "G major",
            "chord_progression": "Verse: I - V - vi - IV\nChorus: IV - V - I - vi",
            "mood": ["담담함", "회상", "따뜻함"],
            "lyric_theme": "조용한 고백과 그리움",
            "hook_type": "intimate lyric hook",
            "structure": ["Verse", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 60,
            "arrangement": "acoustic guitar and vocal intimacy",
            "vocal": "close, conversational, breath-led delivery",
            "mixing": "dry intimate vocal with minimal space",
            "hit_factor": "작은 사운드 안에서 선명한 장면과 말투가 남음",
            "takeaway": "큰 편곡 대신 구체적 이미지와 가까운 보컬 거리감으로 몰입을 만든다.",
        },
        {
            "title": "Love Poem",
            "artist": "아이유",
            "country": "KR",
            "release_year": 2019,
            "bpm": 80,
            "key": "Eb major",
            "chord_progression": "Verse: I - V - vi - IV\nPre-Chorus: ii - V - iii - vi\nChorus: IV - V - I - vi",
            "mood": ["위로", "희망", "확장"],
            "lyric_theme": "누군가를 위한 위로",
            "hook_type": "vocal lift hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 58,
            "arrangement": "piano, strings, choir-like final expansion",
            "vocal": "clear verse, wide chorus, final high emotional lift",
            "mixing": "large ballad space with centered vocal",
            "hit_factor": "마지막 후렴에서 메시지와 보컬 스케일이 함께 확장",
            "takeaway": "마지막 후렴을 단순 반복하지 않고 하모니와 레이어로 의미를 키운다.",
        },
        {
            "title": "숨",
            "artist": "박효신",
            "country": "KR",
            "release_year": 2016,
            "bpm": 68,
            "key": "Bb major",
            "chord_progression": "Verse: I - iii - IV - V\nPre-Chorus: ii - V - iii - vi\nChorus: IV - V - I - vi",
            "mood": ["위로", "고요함", "카타르시스"],
            "lyric_theme": "숨을 고르는 듯한 회복",
            "hook_type": "vocal emotion hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 62,
            "arrangement": "wide piano ballad with cinematic build",
            "vocal": "deep controlled tone, dynamic chorus release",
            "mixing": "vocal-forward, wide reverb, polished master",
            "hit_factor": "보컬의 호흡과 다이내믹 자체가 후크 역할",
            "takeaway": "멜로디보다 호흡, 다이내믹, 공간 확장을 중심 장치로 설계한다.",
        },
        {
            "title": "첫눈처럼 너에게 가겠다",
            "artist": "에일리",
            "country": "KR",
            "release_year": 2017,
            "bpm": 70,
            "key": "E major",
            "chord_progression": "Verse: I - V - vi - IV\nChorus: IV - V - iii - vi",
            "mood": ["운명", "그리움", "폭발"],
            "lyric_theme": "운명적 사랑과 이별의 여운",
            "hook_type": "chorus power hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 52,
            "arrangement": "dramatic ballad build with strings and drums",
            "vocal": "power vocal chorus and final adlib lift",
            "mixing": "large vocal scale, cinematic reverb",
            "hit_factor": "드라마 서사와 파워 보컬 후렴의 결합",
            "takeaway": "후렴에서 보컬 스케일이 열리는 순간을 곡의 기억점으로 만든다.",
        },
        {
            "title": "응급실",
            "artist": "izi",
            "country": "KR",
            "release_year": 2005,
            "bpm": 78,
            "key": "C major",
            "chord_progression": "Verse: I - V - vi - IV\nChorus: IV - V - iii - vi",
            "mood": ["이별", "직접성", "노래방형"],
            "lyric_theme": "이별 후 후회와 절박함",
            "hook_type": "singalong chorus hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 50,
            "arrangement": "band ballad with clear chorus lift",
            "vocal": "direct and singable emotional delivery",
            "mixing": "mid-forward band ballad mix",
            "hit_factor": "따라 부르기 쉬운 후렴과 직접적인 감정 표현",
            "takeaway": "복잡한 은유보다 한 번에 따라 부를 수 있는 감정 문장을 만든다.",
        },
        {
            "title": "취중진담",
            "artist": "전람회",
            "country": "KR",
            "release_year": 1996,
            "bpm": 66,
            "key": "F major",
            "chord_progression": "Verse: I - iii - vi - IV\nChorus: IV - V - I - vi",
            "mood": ["고백", "담담함", "진정성"],
            "lyric_theme": "술기운을 빌린 고백",
            "hook_type": "story lyric hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Outro"],
            "first_chorus_time": 64,
            "arrangement": "classic piano ballad with sparse layering",
            "vocal": "plainspoken and sincere delivery",
            "mixing": "natural vocal and piano-centered mix",
            "hit_factor": "상황 설정이 곧 후크가 되는 스토리텔링",
            "takeaway": "강한 콘셉트 상황을 먼저 잡고, 후렴은 그 상황의 결론으로 만든다.",
        },
        {
            "title": "그날처럼",
            "artist": "장덕철",
            "country": "KR",
            "release_year": 2017,
            "bpm": 74,
            "key": "Db major",
            "chord_progression": "Verse: vi - IV - I - V\nChorus: IV - V - iii - vi",
            "mood": ["회상", "후회", "대중성"],
            "lyric_theme": "과거의 사랑을 떠올리는 회상",
            "hook_type": "title memory hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 54,
            "arrangement": "modern ballad layering with vocal harmony",
            "vocal": "soft verse and stacked chorus vocals",
            "mixing": "streaming-friendly vocal ballad mix",
            "hit_factor": "제목과 회상 정서가 후렴에서 반복적으로 각인",
            "takeaway": "제목을 기억 장치로 쓰되 새 장면과 새 문장으로 바꾼다.",
        },
        {
            "title": "모든 날, 모든 순간",
            "artist": "폴킴",
            "country": "KR",
            "release_year": 2018,
            "bpm": 82,
            "key": "C major",
            "chord_progression": "Verse: I - V - vi - IV\nChorus: IV - V - I - vi",
            "mood": ["따뜻함", "사랑", "일상성"],
            "lyric_theme": "일상 속 사랑의 확신",
            "hook_type": "title repetition hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 45,
            "arrangement": "soft pop ballad with acoustic and strings",
            "vocal": "warm and conversational vocal",
            "mixing": "clean intimate vocal with soft stereo bed",
            "hit_factor": "제목 반복과 일상적 감정의 높은 공감도",
            "takeaway": "청자가 자기 이야기로 받아들일 수 있는 쉬운 핵심 문장을 설계한다.",
        },
    ],
    "Global Pop": [
        {
            "title": "Shape of You",
            "artist": "Ed Sheeran",
            "country": "UK",
            "release_year": 2017,
            "bpm": 96,
            "key": "C# minor",
            "chord_progression": "Verse: i - iv - VI - VII\nChorus: i - iv - VI - VII",
            "mood": ["리듬", "섹시함", "반복성"],
            "lyric_theme": "끌림과 관계의 시작",
            "hook_type": "rhythm + lyric hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 42,
            "arrangement": "minimal marimba-like loop and tight percussion",
            "vocal": "rhythmic conversational pop delivery",
            "mixing": "dry hook-forward vocal with tight low end",
            "hit_factor": "짧은 리듬 모티브와 반복 가능한 후렴",
            "takeaway": "복잡한 코드보다 한 번에 인식되는 리듬 셀을 새롭게 설계한다.",
        },
        {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "country": "CA",
            "release_year": 2019,
            "bpm": 171,
            "key": "F minor",
            "chord_progression": "Verse: i - VI - III - VII\nChorus: i - VI - III - VII",
            "mood": ["질주감", "레트로", "긴장"],
            "lyric_theme": "밤의 갈망과 집착",
            "hook_type": "synth riff hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 43,
            "arrangement": "retro synth arpeggio, driving drums, bright lead hook",
            "vocal": "urgent high-register pop vocal",
            "mixing": "bright synth-forward streaming master",
            "hit_factor": "레트로 신스 리프와 고속 드라이브감",
            "takeaway": "시대적 사운드를 복제하지 말고 에너지 추진 구조만 새 사운드로 바꾼다.",
        },
        {
            "title": "Rolling in the Deep",
            "artist": "Adele",
            "country": "UK",
            "release_year": 2010,
            "bpm": 105,
            "key": "C minor",
            "chord_progression": "Verse: i - VII - VI - VII\nChorus: VI - VII - i",
            "mood": ["분노", "소울", "폭발"],
            "lyric_theme": "배신과 감정의 반격",
            "hook_type": "vocal chant hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 50,
            "arrangement": "stomp groove, blues-soul guitar, choir lift",
            "vocal": "powerful soul belt with controlled grit",
            "mixing": "punchy midrange and vocal-forward energy",
            "hit_factor": "강한 보컬 구호형 후크와 리듬 추진력",
            "takeaway": "감정이 강한 곡은 짧고 외치기 쉬운 후렴 구절이 효과적이다.",
        },
        {
            "title": "Uptown Funk",
            "artist": "Mark Ronson ft. Bruno Mars",
            "country": "US",
            "release_year": 2014,
            "bpm": 115,
            "key": "D minor",
            "chord_progression": "Verse: i vamp\nChorus: i - IV groove vamp",
            "mood": ["파티", "펑크", "자신감"],
            "lyric_theme": "자신감과 무대감",
            "hook_type": "groove + chant hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 45,
            "arrangement": "funk brass stabs, bass groove, call-and-response",
            "vocal": "charismatic rhythmic lead with gang responses",
            "mixing": "tight drums, punchy brass, dry vocal presence",
            "hit_factor": "콜앤리스폰스와 리듬 후크의 즉시성",
            "takeaway": "멜로디보다 그루브와 응답 구조를 새롭게 설계할 수 있다.",
        },
        {
            "title": "Bad Guy",
            "artist": "Billie Eilish",
            "country": "US",
            "release_year": 2019,
            "bpm": 135,
            "key": "G minor",
            "chord_progression": "Verse: i groove vamp\nChorus: i - VI",
            "mood": ["미니멀", "장난기", "어두움"],
            "lyric_theme": "캐릭터와 태도의 전복",
            "hook_type": "bass + vocal rhythm hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Breakdown", "Outro"],
            "first_chorus_time": 38,
            "arrangement": "minimal bass, sparse percussion, negative space",
            "vocal": "whisper-close vocal with rhythmic phrasing",
            "mixing": "dry intimate vocal and oversized bass contrast",
            "hit_factor": "공간을 비운 미니멀 사운드와 캐릭터성",
            "takeaway": "소리를 많이 넣기보다 한 가지 사운드 후크를 극명하게 만든다.",
        },
        {
            "title": "Levitating",
            "artist": "Dua Lipa",
            "country": "UK",
            "release_year": 2020,
            "bpm": 103,
            "key": "B minor",
            "chord_progression": "Verse: i - VII - VI - VII\nChorus: i - VII - VI - VII",
            "mood": ["디스코", "상승감", "댄스"],
            "lyric_theme": "사랑과 상승감",
            "hook_type": "disco chorus hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 46,
            "arrangement": "disco bass, claps, bright synth layers",
            "vocal": "confident pop vocal with stacked hooks",
            "mixing": "polished dance-pop width and tight low end",
            "hit_factor": "포스트코러스까지 이어지는 반복 후크",
            "takeaway": "후렴 뒤에 한 번 더 각인되는 짧은 포스트후크를 설계한다.",
        },
        {
            "title": "Stay",
            "artist": "The Kid LAROI & Justin Bieber",
            "country": "US",
            "release_year": 2021,
            "bpm": 170,
            "key": "C# major",
            "chord_progression": "Verse: I - V - vi - IV\nChorus: I - V - vi - IV",
            "mood": ["긴급함", "팝펑크", "반복"],
            "lyric_theme": "관계 속 후회와 붙잡음",
            "hook_type": "high-register title hook",
            "structure": ["Intro", "Chorus", "Verse", "Chorus", "Verse", "Final Chorus"],
            "first_chorus_time": 5,
            "arrangement": "fast synth pulse and pop-punk energy",
            "vocal": "urgent high hook with tight doubles",
            "mixing": "loud, bright, compact streaming pop mix",
            "hit_factor": "초반 즉시 후렴 진입과 짧은 러닝타임",
            "takeaway": "짧은 곡에서는 인트로를 줄이고 첫 10초 안에 핵심 후크를 제시한다.",
        },
        {
            "title": "As It Was",
            "artist": "Harry Styles",
            "country": "UK",
            "release_year": 2022,
            "bpm": 174,
            "key": "A major",
            "chord_progression": "Verse: I - V - vi - IV\nChorus: I - V - vi - IV",
            "mood": ["쓸쓸함", "업템포", "회상"],
            "lyric_theme": "변화와 상실감",
            "hook_type": "synth motif + title hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 32,
            "arrangement": "bright synth bell motif with bittersweet drive",
            "vocal": "understated vocal over energetic track",
            "mixing": "clean nostalgic pop with clear motif upfront",
            "hit_factor": "밝은 템포와 쓸쓸한 정서의 대비",
            "takeaway": "가사 정서와 편곡 에너지를 반대로 배치해 입체감을 만든다.",
        },
        {
            "title": "Drivers License",
            "artist": "Olivia Rodrigo",
            "country": "US",
            "release_year": 2021,
            "bpm": 72,
            "key": "Bb major",
            "chord_progression": "Verse: I - V - vi - IV\nChorus: IV - I - V - vi",
            "mood": ["상실", "청춘", "고조"],
            "lyric_theme": "이별 후 질투와 상실",
            "hook_type": "story + bridge climax hook",
            "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 63,
            "arrangement": "piano ballad into cinematic bridge explosion",
            "vocal": "intimate verse to explosive bridge vocal",
            "mixing": "wide emotional bridge and centered vocal",
            "hit_factor": "스토리텔링과 브리지 클라이맥스의 폭발",
            "takeaway": "브리지를 곡의 감정 최고점으로 설계할 수 있다.",
        },
        {
            "title": "Flowers",
            "artist": "Miley Cyrus",
            "country": "US",
            "release_year": 2023,
            "bpm": 118,
            "key": "A minor",
            "chord_progression": "Verse: i - VII - VI - V\nChorus: VI - VII - i",
            "mood": ["자기회복", "디스코팝", "자신감"],
            "lyric_theme": "이별 후 자기 사랑",
            "hook_type": "self-empowerment chorus hook",
            "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
            "first_chorus_time": 47,
            "arrangement": "disco-pop groove with clean bass and guitar",
            "vocal": "confident midrange vocal with singalong chorus",
            "mixing": "radio-friendly vocal and groove balance",
            "hit_factor": "자기회복 메시지와 따라 부르기 쉬운 후렴",
            "takeaway": "상실의 감정을 자기 회복 메시지로 전환하면 대중성이 커진다.",
        },
    ],
}


BULK_RESEARCH_GENRE_TEMPLATES: list[dict[str, Any]] = [
    {"genre": "K-pop Ballad", "country": "KR", "bpm_min": 64, "bpm_max": 88, "moods": ["longing", "restraint", "emotional lift"]},
    {"genre": "Global Pop", "country": "US", "bpm_min": 88, "bpm_max": 126, "moods": ["confident", "catchy", "bright"]},
    {"genre": "Dance Pop", "country": "US", "bpm_min": 112, "bpm_max": 132, "moods": ["energetic", "glossy", "release"]},
    {"genre": "R&B", "country": "US", "bpm_min": 70, "bpm_max": 102, "moods": ["sensual", "smooth", "late-night"]},
    {"genre": "Hip-hop", "country": "US", "bpm_min": 76, "bpm_max": 104, "moods": ["direct", "rhythmic", "confident"]},
    {"genre": "Rock", "country": "UK", "bpm_min": 92, "bpm_max": 148, "moods": ["anthemic", "driving", "raw"]},
    {"genre": "Acoustic Ballad", "country": "US", "bpm_min": 68, "bpm_max": 96, "moods": ["intimate", "warm", "story-led"]},
    {"genre": "EDM", "country": "SE", "bpm_min": 120, "bpm_max": 140, "moods": ["festival", "euphoric", "drop-focused"]},
    {"genre": "Latin Pop", "country": "CO", "bpm_min": 88, "bpm_max": 118, "moods": ["rhythmic", "romantic", "danceable"]},
    {"genre": "J-pop", "country": "JP", "bpm_min": 92, "bpm_max": 154, "moods": ["melodic", "dramatic", "bright"]},
]

COMMON_KEYS = [
    "C major",
    "G major",
    "D major",
    "A major",
    "E major",
    "F major",
    "Bb major",
    "A minor",
    "E minor",
    "F# minor",
    "C# minor",
    "D minor",
]

COMMON_PROGRESSIONS = [
    ("I - V - vi - IV", "ii - V - iii - vi", "IV - V - iii - vi", "ii - V - I - vi"),
    ("vi - IV - I - V", "IV - V - iii - vi", "I - V - vi - IV", "ii - V - vi - IV"),
    ("I - iii - IV - V", "ii - V - I", "IV - V - I - vi", "vi - IV - V - I"),
    ("i - VI - III - VII", "iv - VI - VII", "i - VI - III - VII", "VI - VII - i"),
    ("I - vi - IV - V", "iii - vi - ii - V", "I - V - IV - I", "IV - V - vi - V"),
]

COMMON_HOOK_TYPES = [
    "lyric + melody hook",
    "title repetition hook",
    "rhythm hook",
    "sound hook",
    "vocal lift hook",
    "call-and-response hook",
    "chorus chant hook",
    "two-bar motif hook",
]


def supported_bestseller_genres() -> list[dict[str, Any]]:
    return [
        {
            "genre": genre,
            "song_count": len(songs),
            "source": "MVP curated all-time hit-song research seed",
            "note": "라이브 차트가 아니라 앱 MVP용 큐레이션 데이터입니다.",
        }
        for genre, songs in GENRE_BESTSELLER_CATALOG.items()
    ]


def import_genre_bestsellers(store: SQLiteStore, genre: str, limit: int = 10) -> dict[str, Any]:
    if genre not in GENRE_BESTSELLER_CATALOG:
        supported = ", ".join(sorted(GENRE_BESTSELLER_CATALOG))
        raise ValueError(f"지원하지 않는 장르입니다. 지원 장르: {supported}")

    selected = GENRE_BESTSELLER_CATALOG[genre][: max(1, min(limit, 10))]
    existing = store.list_songs()
    created: list[dict[str, Any]] = []
    reused: list[dict[str, Any]] = []
    analyses: list[dict[str, Any]] = []

    for rank, entry in enumerate(selected, start=1):
        existing_song = _find_existing_song(existing, entry["title"], entry["artist"], genre)
        profile = _profile_from_entry(entry, genre, rank)
        analysis = _analysis_from_entry(profile, entry, genre, rank)

        if existing_song:
            store.update_song_research_profile(existing_song["id"], profile)
            song_id = existing_song["id"]
            reused.append(store.get_song(song_id) or existing_song)
        else:
            song_id = make_id("song")
            song = store.create_song(
                {
                    "id": song_id,
                    "title": entry["title"],
                    "artist": entry["artist"],
                    "genre": genre,
                    "release_year": entry.get("release_year"),
                    "country": entry.get("country"),
                    "youtube_url": _youtube_search_url(entry),
                    "youtube_metadata": profile["youtube_metadata"],
                    "research_profile": profile,
                    "duration": None,
                    "bpm": entry.get("bpm"),
                    "key": entry.get("key"),
                    "file_name": None,
                }
            )
            created.append(song)

        analyses.append(store.save_analysis(song_id, analysis))

    all_songs = store.list_songs()
    all_analyses = store.get_analyses_for_songs([song["id"] for song in all_songs])
    genre_songs = [song for song in all_songs if song.get("genre") == genre]
    genre_analyses = store.get_analyses_for_songs([song["id"] for song in genre_songs])
    return {
        "genre": genre,
        "requested_limit": limit,
        "imported_count": len(selected),
        "created_count": len(created),
        "reused_count": len(reused),
        "songs": [store.get_song(analysis["song_id"]) for analysis in analyses],
        "ranking_basis": "MVP curated all-time hit-song research seed; replaceable with Billboard/Spotify/Last.fm sources later.",
        "youtube_policy": "YouTube is used only as a reference/search starting point. No YouTube audio is downloaded, extracted, separated, converted, captured, or analyzed.",
        "genre_statistics": build_hit_song_statistics(genre_songs, genre_analyses),
        "library_statistics": build_hit_song_statistics(all_songs, all_analyses),
    }


def import_bulk_research_seeds(store: SQLiteStore, target_count: int = 1000, batch_size: int = 1000) -> dict[str, Any]:
    """Bulk synthetic seeds are disabled.

    Hit Song Lab statistics must be based on unique reference songs. Repeating a
    small template set under numbered names would inflate chart statistics, so
    this endpoint now behaves as a no-op and preserves the current library.
    """

    all_songs = store.list_songs()
    all_analyses = store.get_analyses_for_songs([song["id"] for song in all_songs])
    bulk_total = sum(1 for song in all_songs if (song.get("artist") or "") == "Hit Song Lab Research Seed")
    return {
        "requested_target_count": target_count,
        "requested_batch_size": batch_size,
        "created_count": 0,
        "reused_count": 0,
        "bulk_seed_total": bulk_total,
        "library_song_count": len(all_songs),
        "songs": [],
        "ranking_basis": "Bulk synthetic seed creation is disabled. Add unique real hit-song references only.",
        "youtube_policy": "YouTube is only a reference starting point. No YouTube audio is downloaded, extracted, separated, converted, captured, or analyzed.",
        "library_statistics": build_hit_song_statistics(all_songs, all_analyses),
        "disabled_reason": "Disabled: repeating songs or numbered variants are not allowed in the analysis database.",
    }


def _bulk_seed_entry(seed_number: int) -> dict[str, Any]:
    genre_template = BULK_RESEARCH_GENRE_TEMPLATES[(seed_number - 1) % len(BULK_RESEARCH_GENRE_TEMPLATES)]
    base_genres = list(GENRE_BESTSELLER_CATALOG.values())
    base_entry = base_genres[(seed_number - 1) % len(base_genres)][(seed_number - 1) % len(base_genres[(seed_number - 1) % len(base_genres)])]
    bpm_span = genre_template["bpm_max"] - genre_template["bpm_min"] + 1
    bpm = genre_template["bpm_min"] + ((seed_number * 7) % bpm_span)
    verse, pre_chorus, chorus, bridge = COMMON_PROGRESSIONS[(seed_number - 1) % len(COMMON_PROGRESSIONS)]
    hook_type = COMMON_HOOK_TYPES[(seed_number - 1) % len(COMMON_HOOK_TYPES)]
    structure_options = [
        ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Final Chorus"],
        ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus", "Outro"],
        ["Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Dance Break", "Final Chorus"],
        ["Intro", "Verse", "Hook", "Verse", "Hook", "Bridge", "Final Hook"],
    ]
    first_chorus_time = 32 + ((seed_number * 5) % 42)
    return {
        "title": f"HSL Bulk Reference Seed {seed_number:04d} - {base_entry['title']}",
        "artist": "Hit Song Lab Research Seed",
        "country": genre_template["country"],
        "release_year": 1980 + ((seed_number * 3) % 45),
        "genre": genre_template["genre"],
        "bpm": bpm,
        "key": COMMON_KEYS[(seed_number - 1) % len(COMMON_KEYS)],
        "chord_progression": f"Verse: {verse}\nPre-Chorus: {pre_chorus}\nChorus: {chorus}\nBridge: {bridge}",
        "mood": genre_template["moods"],
        "lyric_theme": _theme_for_seed(seed_number, genre_template["genre"]),
        "hook_type": hook_type,
        "structure": structure_options[(seed_number - 1) % len(structure_options)],
        "first_chorus_time": first_chorus_time,
        "arrangement": _arrangement_for_seed(seed_number, genre_template["genre"]),
        "vocal": _vocal_for_seed(seed_number, genre_template["genre"]),
        "mixing": _mixing_for_seed(seed_number, genre_template["genre"]),
        "hit_factor": _hit_factor_for_seed(seed_number, hook_type),
        "takeaway": _takeaway_for_seed(seed_number, genre_template["genre"]),
    }


def _profile_from_entry(entry: dict[str, Any], genre: str, rank: int) -> dict[str, Any]:
    youtube_metadata = {
        "source": "curated_youtube_reference_search",
        "url": _youtube_search_url(entry),
        "video_id": None,
        "title": f"{entry['artist']} - {entry['title']} official",
        "channel_name": entry["artist"],
        "description": (
            f"Curated hit-song reference seed for {genre}. Rank {rank}. "
            "Metadata/research only; no YouTube audio is downloaded or analyzed."
        ),
        "thumbnail_url": None,
        "duration": None,
        "published_date": None,
        "view_count": None,
        "metadata_status": "curated_seed",
        "policy": "Metadata/search reference only. YouTube audio is not downloaded, extracted, isolated, converted, streamed, or analyzed.",
    }
    identification = {
        "title": confidence_field(entry["title"], "medium", "curated bestseller seed"),
        "artist": confidence_field(entry["artist"], "medium", "curated bestseller seed"),
        "release_year": confidence_field(entry.get("release_year"), "medium", "curated bestseller seed"),
        "genre": confidence_field(genre, "medium", "curated bestseller seed"),
        "country": confidence_field(entry.get("country"), "medium", "curated bestseller seed"),
        "video_type": confidence_field("YouTube Reference Search", "low", "curated seed, not a fetched YouTube video"),
    }
    public_data = {
        "curated_seed": {
            "status": "available",
            "source": "MVP curated all-time hit-song research seed",
            "rank": rank,
            "ranking_basis": "representative hit-song study set, not a live sales chart",
        },
        "musicbrainz": {"status": "not_queried"},
        "lastfm": {"status": "not_configured"},
        "spotify": {"status": "not_configured"},
    }
    profile = build_structured_profile(
        youtube_metadata=youtube_metadata,
        identification=identification,
        public_data=public_data,
        lyrics_text=f"{entry['lyric_theme']} {entry['hit_factor']}",
        chord_progression=entry.get("chord_progression"),
        analysis_notes=f"{entry['bpm']} BPM, {entry['key']}, {entry['hook_type']}, {entry['arrangement']}",
    )
    profile["profile_type"] = "genre_bestseller_hit_song_research"
    profile["bestseller_seed"] = {
        "genre": genre,
        "rank": rank,
        "ranking_basis": "MVP curated all-time hit-song research seed",
        "not_live_chart": True,
    }
    return profile


def _analysis_from_entry(profile: dict[str, Any], entry: dict[str, Any], genre: str, rank: int) -> dict[str, Any]:
    analysis = build_analysis_from_research_profile(profile)
    analysis["concept"].update(
        {
            "concept": f"{entry['title']} - {genre} 대표 히트곡 연구",
            "genre": genre,
            "mood": entry["mood"],
            "target_listener": "genre hit-song listeners",
            "one_sentence_concept": f"{entry['artist']}의 '{entry['title']}'은 {genre} 장르의 대표 히트곡 seed #{rank}로, {entry['lyric_theme']} 정서를 {entry['hook_type']} 중심으로 각인시키는 레퍼런스입니다.",
        }
    )
    analysis["lyrics"].update(
        {
            "lyric_theme": entry["lyric_theme"],
            "core_message": entry["hit_factor"],
            "title_usage": "후렴 또는 핵심 후크와 연결되는 제목/핵심 이미지",
            "emotion_curve": entry["mood"],
        }
    )
    analysis["structure"].update(
        {
            "structure": entry["structure"],
            "first_chorus_time": entry["first_chorus_time"],
            "final_chorus_expansion": "final chorus lift with vocal/arrangement expansion",
        }
    )
    analysis["harmony"].update({"key": entry["key"]})
    analysis["melody"].update(
        {
            "chorus_peak_position": "chorus second half or final chorus",
            "motif_type": entry["hook_type"],
            "singability": "high",
            "creative_principle": "후크의 위치와 반복 원리만 참고하고 원곡 멜로디 윤곽은 사용하지 않습니다.",
        }
    )
    analysis["hook"].update(
        {
            "primary_hook_type": entry["hook_type"],
            "hook_location": "chorus or signature motif",
            "hook_memorability": "high",
            "title_hook_connection": "strong",
        }
    )
    analysis["rhythm"].update({"bpm": entry["bpm"], "groove_type": _groove_for(entry["bpm"], genre)})
    analysis["arrangement"].update(
        {
            "arrangement_build": entry["arrangement"],
            "final_chorus_lift": "expanded vocal/arrangement layer",
            "creative_principle": "악기 조합을 베끼지 말고 에너지 추가/제거 타이밍만 새 곡에 맞게 재설계합니다.",
        }
    )
    analysis["vocal"].update(
        {
            "vocal_tone": entry["vocal"],
            "chorus_delivery": "hook-focused emotional delivery",
            "adlib_usage": "final chorus or climax",
        }
    )
    analysis["mixing"].update(
        {
            "vocal_position": entry["mixing"],
            "mastering_loudness_style": "commercial streaming reference",
        }
    )
    analysis["hit_factor"].update(
        {
            "main_hit_factor": entry["hit_factor"],
            "singalong_level": "high",
            "replay_factor": "high",
        }
    )
    analysis["takeaway"].update(
        {
            "transferable_principles": [
                entry["takeaway"],
                "원곡의 멜로디, 가사, 특정 리프를 복제하지 않고 창작 의사결정 원리만 추출합니다.",
                "같은 장르 Top 10의 공통 패턴을 통계화한 뒤 새 곡 콘셉트에 맞게 변형합니다.",
            ],
            "avoid_copying": [
                "원곡 멜로디 라인을 그대로 사용하지 않습니다.",
                "원곡 가사 문장이나 제목 표현을 차용하지 않습니다.",
                "식별 가능한 리프, 애드리브, 사운드 시그니처를 복제하지 않습니다.",
            ],
        }
    )
    analysis["audio_features"].update(
        {
            "bpm": float(entry["bpm"]),
            "estimated_key": entry["key"],
            "analysis_source": "curated_genre_bestseller_seed_no_youtube_audio",
        }
    )
    metadata = {
        "title": entry["title"],
        "artist": entry["artist"],
        "genre": genre,
        "country": entry.get("country"),
        "release_year": entry.get("release_year"),
        "youtube_url": _youtube_search_url(entry),
        "file_name": None,
    }
    analysis["full_report"] = generate_full_report(analysis, metadata, analysis["audio_features"], research_profile=profile)
    return analysis


def _find_existing_song(songs: list[dict[str, Any]], title: str, artist: str, genre: str) -> dict[str, Any] | None:
    title_key = title.casefold()
    artist_key = artist.casefold()
    for song in songs:
        if (song.get("title") or "").casefold() == title_key and (song.get("artist") or "").casefold() == artist_key:
            if song.get("genre") in [genre, None, "Unknown"]:
                return song
    return None


def _theme_for_seed(seed_number: int, genre: str) -> str:
    themes = [
        "late-night longing and unresolved memory",
        "self-recovery after a breakup",
        "first attraction and repeated desire",
        "nostalgia for a city, season, or past relationship",
        "confidence, release, and crowd energy",
        "quiet confession before emotional expansion",
        "bittersweet acceptance and mature closure",
        "youthful escape and cinematic freedom",
    ]
    return f"{genre} reference theme: {themes[(seed_number - 1) % len(themes)]}"


def _arrangement_for_seed(seed_number: int, genre: str) -> str:
    options = [
        "sparse verse, fuller chorus, final chorus lift with added harmony and cymbal wash",
        "signature intro motif, tight rhythm bed, chorus layer expansion",
        "piano or guitar-led opening, bass/drums entering at first chorus, wide final section",
        "loop-based production with small changes every eight bars to avoid fatigue",
        "drop or hook section built around a memorable synth/rhythm texture",
        "band-oriented arrangement with dynamic contrast between verse and chorus",
    ]
    return f"{genre}: {options[(seed_number - 1) % len(options)]}"


def _vocal_for_seed(seed_number: int, genre: str) -> str:
    options = [
        "intimate verse delivery, open chorus phrasing, final adlib emphasis",
        "rhythmic conversational verse with singalong chorus hook",
        "controlled low verse and higher-register chorus peak",
        "stacked chorus doubles and background harmony in the final refrain",
        "dry close vocal up front with wider ambience during the hook",
    ]
    return f"{genre}: {options[(seed_number - 1) % len(options)]}"


def _mixing_for_seed(seed_number: int, genre: str) -> str:
    options = [
        "front vocal, controlled low end, wide supporting instruments",
        "punchy rhythm section with bright hook elements and streaming-friendly loudness",
        "warm midrange, moderate reverb, vocal clarity prioritized",
        "wide stereo bed with centered lead vocal and polished top end",
        "tight low-frequency control and chorus-size ambience automation",
    ]
    return f"{genre}: {options[(seed_number - 1) % len(options)]}"


def _hit_factor_for_seed(seed_number: int, hook_type: str) -> str:
    factors = [
        "early identity signal in the first 30 seconds",
        "chorus first two bars connect the title idea with the main emotion",
        "simple repeatable hook that is easy to remember after one listen",
        "clear verse-to-chorus energy lift without overcrowding the vocal",
        "final chorus expands the emotional payoff with new layers",
        "familiar harmonic language with one memorable sound or rhythm twist",
    ]
    return f"{hook_type}: {factors[(seed_number - 1) % len(factors)]}"


def _takeaway_for_seed(seed_number: int, genre: str) -> str:
    takeaways = [
        "Use restraint in the verse and focus the strongest phrase in the chorus opening.",
        "Generalize the hook principle instead of copying melody, lyric, or arrangement riffs.",
        "Design the final chorus as a new emotional event, not only a repeated section.",
        "Let the vocal carry the story while instruments create contrast and scale.",
        "Build memorability with a short motif, title connection, and clear energy curve.",
    ]
    return f"{genre}: {takeaways[(seed_number - 1) % len(takeaways)]}"


def _youtube_search_url(entry: dict[str, Any]) -> str:
    query = f"{entry['artist']} {entry['title']} official"
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"


def _groove_for(bpm: float, genre: str) -> str:
    if bpm < 85:
        return "slow ballad groove" if "Ballad" in genre else "slow emotional groove"
    if bpm < 115:
        return "mid-tempo pop groove"
    if bpm < 145:
        return "danceable pop groove"
    return "fast pop pulse / double-time feel"
