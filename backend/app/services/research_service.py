from __future__ import annotations

from typing import Any


REFERENCE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "ref_kpop_ballad_01",
        "title": "너였다면",
        "artist": "정승환",
        "genre": "K-pop Ballad",
        "country": "KR",
        "release_year": 2016,
        "bpm": 72,
        "key": "A major",
        "mood": ["그리움", "고조", "절제"],
        "hook_type": "lyric + melody hook",
        "structure": "Verse - Pre-Chorus - Chorus - Verse - Chorus - Bridge - Final Chorus",
        "why_it_matters": "절제된 벌스에서 후렴으로 갈수록 보컬 감정과 편곡 밀도가 커지는 발라드형 설계가 뚜렷합니다.",
        "creative_principle": "초반에는 말을 건네듯 낮게 시작하고, 후렴 후반에서 최고점을 배치해 감정 보상을 만듭니다.",
        "avoid_copying": ["후렴 멜로디 윤곽을 그대로 사용하지 않습니다.", "가사 핵심 문장을 차용하지 않습니다."],
    },
    {
        "id": "ref_kpop_ballad_02",
        "title": "그대라는 시",
        "artist": "태연",
        "genre": "K-pop Ballad",
        "country": "KR",
        "release_year": 2019,
        "bpm": 76,
        "key": "D major",
        "mood": ["따뜻함", "그리움", "서정"],
        "hook_type": "title phrase hook",
        "structure": "Intro - Verse - Chorus - Verse - Chorus - Bridge - Final Chorus",
        "why_it_matters": "제목과 정서를 후렴에서 자연스럽게 연결해 기억성을 만드는 팝 발라드 문법이 강합니다.",
        "creative_principle": "후렴 첫 줄에 제목과 연결되는 짧은 이미지를 배치하면 청자가 곡의 감정을 빠르게 붙잡을 수 있습니다.",
        "avoid_copying": ["제목 표현과 후렴 가사 이미지를 직접 빌리지 않습니다.", "특정 보컬 애드리브를 복제하지 않습니다."],
    },
    {
        "id": "ref_kpop_ballad_03",
        "title": "밤편지",
        "artist": "아이유",
        "genre": "Acoustic Ballad",
        "country": "KR",
        "release_year": 2017,
        "bpm": 74,
        "key": "G major",
        "mood": ["담담함", "회상", "따뜻함"],
        "hook_type": "intimate lyric hook",
        "structure": "Verse - Verse - Chorus - Bridge - Final Chorus",
        "why_it_matters": "큰 드라마보다 가까운 말투와 이미지로 감정을 오래 남기는 방식이 돋보입니다.",
        "creative_principle": "소리의 크기보다 구체적인 장면과 보컬 거리감을 활용해 친밀한 몰입을 설계합니다.",
        "avoid_copying": ["가사의 편지 형식과 구체 문장을 그대로 따라 하지 않습니다.", "기타/보컬 질감을 동일하게 모사하지 않습니다."],
    },
    {
        "id": "ref_global_pop_01",
        "title": "Someone Like You",
        "artist": "Adele",
        "genre": "Pop Ballad",
        "country": "UK",
        "release_year": 2011,
        "bpm": 68,
        "key": "A major",
        "mood": ["상실", "고백", "폭발"],
        "hook_type": "chorus confession hook",
        "structure": "Verse - Pre-Chorus - Chorus - Verse - Chorus - Bridge - Final Chorus",
        "why_it_matters": "피아노 중심의 단순한 편곡 위에 보컬 서사와 후렴 반복이 곡 전체의 힘을 만듭니다.",
        "creative_principle": "악기 수를 줄여도 제목과 연결되는 직접적인 후렴 문장이 강하면 큰 스케일을 만들 수 있습니다.",
        "avoid_copying": ["피아노 패턴과 후렴 선율을 복제하지 않습니다.", "가사 상황을 그대로 가져오지 않습니다."],
    },
    {
        "id": "ref_global_pop_02",
        "title": "All of Me",
        "artist": "John Legend",
        "genre": "Pop Ballad",
        "country": "US",
        "release_year": 2013,
        "bpm": 63,
        "key": "Ab major",
        "mood": ["헌신", "따뜻함", "직접성"],
        "hook_type": "title repetition hook",
        "structure": "Verse - Pre-Chorus - Chorus - Verse - Chorus - Bridge - Final Chorus",
        "why_it_matters": "쉬운 제목 반복과 안정적인 코드 감각으로 대중적인 발라드 친화성을 확보합니다.",
        "creative_principle": "복잡한 은유보다 한 문장으로 정리되는 감정 약속을 후렴에 반복 배치합니다.",
        "avoid_copying": ["제목 반복 방식의 멜로디를 직접 차용하지 않습니다.", "피아노 보이싱을 그대로 재현하지 않습니다."],
    },
    {
        "id": "ref_kpop_mid_01",
        "title": "Love Poem",
        "artist": "아이유",
        "genre": "K-pop Ballad",
        "country": "KR",
        "release_year": 2019,
        "bpm": 80,
        "key": "Eb major",
        "mood": ["위로", "확장", "희망"],
        "hook_type": "vocal lift hook",
        "structure": "Intro - Verse - Pre-Chorus - Chorus - Verse - Chorus - Bridge - Final Chorus",
        "why_it_matters": "마지막 후렴에서 보컬과 화성의 폭을 확장해 위로의 메시지를 크게 밀어 올립니다.",
        "creative_principle": "마지막 후렴을 단순 반복하지 말고 하모니, 애드리브, 상행 레이어로 새 의미를 만듭니다.",
        "avoid_copying": ["클라이맥스 보컬 라인을 직접 따라 하지 않습니다.", "가사 이미지와 메시지를 그대로 옮기지 않습니다."],
    },
]


def search_reference_songs(goal: str | None = None, genre: str | None = None, mood: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Return curated mock research data for MVP without external scraping."""
    tokens = _tokenize(" ".join(item for item in [goal, genre, mood] if item))
    scored = []
    for song in REFERENCE_CATALOG:
        haystack = _tokenize(
            " ".join(
                [
                    song["title"],
                    song["artist"],
                    song["genre"],
                    song["country"],
                    " ".join(song["mood"]),
                    song["hook_type"],
                    song["creative_principle"],
                ]
            )
        )
        score = sum(1 for token in tokens if token in haystack)
        if genre and genre.lower() in song["genre"].lower():
            score += 3
        if mood and any(mood.lower() in value.lower() for value in song["mood"]):
            score += 3
        scored.append((score, song))
    return [song for _, song in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def describe_research_policy() -> str:
    return (
        "MVP에서는 외부 검색 대신 큐레이션된 mock reference data를 사용합니다. "
        "YouTube 링크는 참고 정보로만 저장할 수 있으며, 오디오는 다운로드하거나 추출하지 않습니다."
    )


def _tokenize(text: str) -> set[str]:
    normalized = text.lower().replace("-", " ").replace("/", " ")
    return {token.strip() for token in normalized.split() if token.strip()}
