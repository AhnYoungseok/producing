from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus


RAW_CURATED_HIT_SONGS: list[tuple[str, str, str, str, int, float, str]] = [
    ("Spring Day", "BTS", "K-pop Ballad Pop", "KR", 2017, 108, "Eb major"),
    ("Boy With Luv", "BTS feat. Halsey", "K-pop Funk Pop", "KR/US", 2019, 120, "E major"),
    ("Fake Love", "BTS", "K-pop Emo Pop", "KR", 2018, 78, "D minor"),
    ("DNA", "BTS", "K-pop EDM Pop", "KR", 2017, 130, "C# minor"),
    ("IDOL", "BTS", "K-pop Dance Pop", "KR", 2018, 126, "C# minor"),
    ("Kill This Love", "BLACKPINK", "K-pop Trap Pop", "KR", 2019, 132, "E minor"),
    ("Pink Venom", "BLACKPINK", "K-pop Hip-hop Pop", "KR", 2022, 90, "G minor"),
    ("Shut Down", "BLACKPINK", "K-pop Hip-hop Pop", "KR", 2022, 110, "C# minor"),
    ("As If It's Your Last", "BLACKPINK", "K-pop Dance Pop", "KR", 2017, 125, "C major"),
    ("Lovesick Girls", "BLACKPINK", "K-pop Dance Pop", "KR", 2020, 128, "G major"),
    ("TT", "TWICE", "K-pop Bubblegum Pop", "KR", 2016, 130, "F minor"),
    ("FANCY", "TWICE", "K-pop Dance Pop", "KR", 2019, 132, "F minor"),
    ("Feel Special", "TWICE", "K-pop Dance Pop", "KR", 2019, 129, "A minor"),
    ("What is Love?", "TWICE", "K-pop Bubblegum Pop", "KR", 2018, 170, "C major"),
    ("The Feels", "TWICE", "K-pop English Pop", "KR", 2021, 120, "D major"),
    ("Psycho", "Red Velvet", "K-pop R&B Pop", "KR", 2019, 140, "Eb minor"),
    ("Red Flavor", "Red Velvet", "K-pop Summer Pop", "KR", 2017, 125, "A major"),
    ("Bad Boy", "Red Velvet", "K-pop R&B Pop", "KR", 2018, 150, "D minor"),
    ("Growl", "EXO", "K-pop R&B Dance", "KR", 2013, 104, "G minor"),
    ("Love Shot", "EXO", "K-pop Dance Pop", "KR", 2018, 110, "C minor"),
    ("Gee", "Girls' Generation", "K-pop Bubblegum Pop", "KR", 2009, 100, "G major"),
    ("I Got a Boy", "Girls' Generation", "K-pop Hybrid Pop", "KR", 2013, 130, "D minor"),
    ("Fantastic Baby", "BIGBANG", "K-pop EDM Hip-hop", "KR", 2012, 130, "F minor"),
    ("Haru Haru", "BIGBANG", "K-pop Hip-hop Ballad", "KR", 2008, 120, "G minor"),
    ("Good Day", "IU", "K-pop Orchestral Pop", "KR", 2010, 128, "Ab major"),
    ("Palette", "IU feat. G-DRAGON", "K-pop R&B Pop", "KR", 2017, 102, "F major"),
    ("Celebrity", "IU", "K-pop Synth Pop", "KR", 2021, 100, "F# major"),
    ("Blueming", "IU", "K-pop Pop Rock", "KR", 2019, 104, "E major"),
    ("After LIKE", "IVE", "K-pop Disco Pop", "KR", 2022, 125, "C# minor"),
    ("ELEVEN", "IVE", "K-pop Dance Pop", "KR", 2021, 120, "A minor"),
    ("Baddie", "IVE", "K-pop Hip-hop Pop", "KR", 2023, 160, "G minor"),
    ("ETA", "NewJeans", "K-pop Jersey Club Pop", "KR", 2023, 135, "F minor"),
    ("Attention", "NewJeans", "K-pop R&B Pop", "KR", 2022, 105, "E minor"),
    ("Cookie", "NewJeans", "K-pop R&B Pop", "KR", 2022, 157, "B minor"),
    ("Savage", "aespa", "K-pop Hyper Pop", "KR", 2021, 147, "F# minor"),
    ("Spicy", "aespa", "K-pop Dance Pop", "KR", 2023, 115, "B minor"),
    ("Super", "SEVENTEEN", "K-pop Performance Pop", "KR", 2023, 137, "E minor"),
    ("Don't Wanna Cry", "SEVENTEEN", "K-pop EDM Pop", "KR", 2017, 100, "C# minor"),
    ("Very Nice", "SEVENTEEN", "K-pop Funk Pop", "KR", 2016, 122, "F major"),
    ("UNFORGIVEN", "LE SSERAFIM", "K-pop Latin Pop", "KR", 2023, 104, "E minor"),
    ("EASY", "LE SSERAFIM", "K-pop Trap R&B", "KR", 2024, 104, "F# minor"),
    ("Save Your Tears", "The Weeknd", "Synth Pop", "CA", 2020, 118, "C major"),
    ("Can't Feel My Face", "The Weeknd", "Funk Pop", "CA", 2015, 108, "A minor"),
    ("Starboy", "The Weeknd feat. Daft Punk", "R&B Synth Pop", "CA/FR", 2016, 93, "G minor"),
    ("Blank Space", "Taylor Swift", "Synth Pop", "US", 2014, 96, "F major"),
    ("Love Story", "Taylor Swift", "Country Pop", "US", 2008, 119, "D major"),
    ("Lover", "Taylor Swift", "Pop Ballad", "US", 2019, 69, "G major"),
    ("cardigan", "Taylor Swift", "Indie Folk Pop", "US", 2020, 130, "Eb major"),
    ("Hello", "Adele", "Soul Pop Ballad", "UK", 2015, 79, "F minor"),
    ("Easy On Me", "Adele", "Pop Ballad", "UK", 2021, 142, "F major"),
    ("Set Fire to the Rain", "Adele", "Soul Pop", "UK", 2011, 108, "D minor"),
    ("Perfect", "Ed Sheeran", "Pop Ballad", "UK", 2017, 95, "Ab major"),
    ("Thinking Out Loud", "Ed Sheeran", "Soul Pop Ballad", "UK", 2014, 79, "D major"),
    ("Bad Habits", "Ed Sheeran", "Dance Pop", "UK", 2021, 126, "B minor"),
    ("Photograph", "Ed Sheeran", "Acoustic Pop", "UK", 2015, 108, "E major"),
    ("Don't Start Now", "Dua Lipa", "Nu-disco Pop", "UK", 2019, 124, "B minor"),
    ("New Rules", "Dua Lipa", "Dance Pop", "UK", 2017, 116, "A minor"),
    ("Physical", "Dua Lipa", "Synth Pop", "UK", 2020, 147, "A minor"),
    ("everything i wanted", "Billie Eilish", "Alternative Pop", "US", 2019, 120, "E major"),
    ("Happier Than Ever", "Billie Eilish", "Alternative Rock Pop", "US", 2021, 81, "C major"),
    ("thank u, next", "Ariana Grande", "R&B Pop", "US", 2018, 107, "Db major"),
    ("7 rings", "Ariana Grande", "Trap Pop", "US", 2019, 140, "C# minor"),
    ("positions", "Ariana Grande", "R&B Pop", "US", 2020, 144, "D minor"),
    ("Into You", "Ariana Grande", "Dance Pop", "US", 2016, 108, "F minor"),
    ("Just the Way You Are", "Bruno Mars", "Pop", "US", 2010, 109, "F major"),
    ("Locked Out of Heaven", "Bruno Mars", "Funk Pop Rock", "US", 2012, 144, "D minor"),
    ("Grenade", "Bruno Mars", "Pop Ballad", "US", 2010, 110, "D minor"),
    ("When I Was Your Man", "Bruno Mars", "Piano Ballad", "US", 2012, 73, "C major"),
    ("We Found Love", "Rihanna feat. Calvin Harris", "Dance Pop", "BB/UK", 2011, 128, "F# major"),
    ("Diamonds", "Rihanna", "Pop Ballad", "BB", 2012, 92, "B minor"),
    ("Umbrella", "Rihanna feat. JAY-Z", "R&B Pop", "BB/US", 2007, 87, "B minor"),
    ("Work", "Rihanna feat. Drake", "Dancehall Pop", "BB/CA", 2016, 92, "F# minor"),
    ("Single Ladies", "Beyonce", "R&B Dance Pop", "US", 2008, 97, "E major"),
    ("Halo", "Beyonce", "Pop Ballad", "US", 2008, 80, "A major"),
    ("Crazy in Love", "Beyonce feat. JAY-Z", "R&B Funk Pop", "US", 2003, 99, "D minor"),
    ("Poker Face", "Lady Gaga", "Dance Pop", "US", 2008, 119, "G# minor"),
    ("Bad Romance", "Lady Gaga", "Dance Pop", "US", 2009, 119, "A minor"),
    ("Shallow", "Lady Gaga & Bradley Cooper", "Pop Rock Ballad", "US", 2018, 96, "G major"),
    ("Sugar", "Maroon 5", "Funk Pop", "US", 2014, 120, "C# major"),
    ("Moves Like Jagger", "Maroon 5 feat. Christina Aguilera", "Dance Pop Rock", "US", 2011, 128, "B minor"),
    ("Memories", "Maroon 5", "Pop", "US", 2019, 91, "B major"),
    ("Sorry", "Justin Bieber", "Tropical Pop", "CA", 2015, 100, "Eb major"),
    ("Love Yourself", "Justin Bieber", "Acoustic Pop", "CA", 2015, 100, "E major"),
    ("Peaches", "Justin Bieber feat. Daniel Caesar & Giveon", "R&B Pop", "CA/US", 2021, 90, "C major"),
    ("Circles", "Post Malone", "Pop Rock", "US", 2019, 120, "C major"),
    ("Sunflower", "Post Malone & Swae Lee", "Hip-hop Pop", "US", 2018, 90, "D major"),
    ("One Dance", "Drake feat. Wizkid & Kyla", "Dancehall Pop", "CA/NG/UK", 2016, 104, "Bb minor"),
    ("God's Plan", "Drake", "Hip-hop Pop", "CA", 2018, 77, "E minor"),
    ("Hotline Bling", "Drake", "R&B Pop", "CA", 2015, 135, "F minor"),
    ("Say So", "Doja Cat", "Disco Pop", "US", 2019, 111, "D major"),
    ("Kiss Me More", "Doja Cat feat. SZA", "Disco Pop", "US", 2021, 111, "Ab major"),
    ("vampire", "Olivia Rodrigo", "Pop Rock Ballad", "US", 2023, 138, "F major"),
    ("deja vu", "Olivia Rodrigo", "Alternative Pop", "US", 2021, 181, "A major"),
    ("Wrecking Ball", "Miley Cyrus", "Pop Ballad", "US", 2013, 120, "D minor"),
    ("Viva La Vida", "Coldplay", "Baroque Pop Rock", "UK", 2008, 138, "Ab major"),
    ("Yellow", "Coldplay", "Alternative Rock", "UK", 2000, 86, "B major"),
    ("The Scientist", "Coldplay", "Piano Rock Ballad", "UK", 2002, 146, "F major"),
    ("A Sky Full of Stars", "Coldplay", "EDM Pop Rock", "UK", 2014, 125, "F# major"),
    ("Smells Like Teen Spirit", "Nirvana", "Grunge Rock", "US", 1991, 117, "F minor"),
    ("Wonderwall", "Oasis", "Britpop Rock", "UK", 1995, 87, "F# minor"),
    ("Creep", "Radiohead", "Alternative Rock", "UK", 1992, 92, "G major"),
    ("Numb", "Linkin Park", "Nu Metal Rock", "US", 2003, 110, "F# minor"),
    ("In the End", "Linkin Park", "Nu Metal Rap Rock", "US", 2000, 105, "D# minor"),
    ("Get Lucky", "Daft Punk feat. Pharrell Williams", "Disco Funk Pop", "FR/US", 2013, 116, "F# minor"),
    ("One More Time", "Daft Punk", "French House", "FR", 2000, 123, "D major"),
    ("Wake Me Up", "Avicii", "EDM Folk Pop", "SE/US", 2013, 124, "B minor"),
    ("Levels", "Avicii", "Progressive House", "SE", 2011, 126, "C# minor"),
    ("Despacito", "Luis Fonsi feat. Daddy Yankee", "Latin Pop Reggaeton", "PR", 2017, 89, "B minor"),
    ("Hips Don't Lie", "Shakira feat. Wyclef Jean", "Latin Pop", "CO/US", 2006, 100, "Bb minor"),
    ("La Tortura", "Shakira feat. Alejandro Sanz", "Latin Pop", "CO/ES", 2005, 100, "C minor"),
]


def curated_reference_entries() -> list[dict[str, Any]]:
    return [_build_entry(*row) for row in RAW_CURATED_HIT_SONGS]


def _build_entry(title: str, artist: str, genre: str, country: str, release_year: int, bpm: float, key: str) -> dict[str, Any]:
    profile = _genre_profile(genre, bpm)
    hook_type = profile["hook_type"]
    return {
        "title": title,
        "artist": artist,
        "genre": genre,
        "country": country,
        "release_year": release_year,
        "bpm": bpm,
        "key": key,
        "youtube_url": f"https://www.youtube.com/results?search_query={quote_plus(f'{artist} {title} official')}",
        "lyric_theme": _theme_for_title(title, profile),
        "speaker_situation": profile["speaker_situation"],
        "story_flow": profile["story_flow"],
        "hook_type": hook_type,
        "hook_location": profile["hook_location"],
        "hook_cue": _safe_title_cue(title),
        "hook_melody_interval": profile["hook_melody_interval"],
        "hook_melody_rhythm": profile["hook_melody_rhythm"],
        "why_hook_works": f"'{_safe_title_cue(title)}' 단서가 {profile['why_hook_works']}",
        "chord_progression": profile["chord_progression"],
        "arrangement": profile["arrangement"],
        "vocal": profile["vocal"],
        "mixing": profile["mixing"],
        "hit_factor": profile["hit_factor"],
        "producer_takeaway": profile["producer_takeaway"],
        "avoid_copying": "원곡의 가사 문장, 멜로디 윤곽, 리프, 보컬 애드리브, 사운드 시그니처를 직접 복제하지 않는다.",
        "data_confidence": "medium-low",
        "catalog_source": "curated_real_hit_song_catalog",
    }


def _genre_profile(genre: str, bpm: float) -> dict[str, str]:
    lowered = genre.lower()
    if "ballad" in lowered or bpm < 84:
        return {
            "speaker_situation": "개인적인 감정을 직접 고백하거나 회상하는 화자",
            "story_flow": "상황 제시 > 감정 축적 > 후렴 고백 > 후반부 보컬/편곡 확장",
            "hook_type": "lyric statement + vocal melody hook",
            "hook_location": "chorus or bridge climax",
            "hook_melody_interval": "stepwise motion + 3rd/4th emotional lift",
            "hook_melody_rhythm": "slow phrasing with sustained emotional notes",
            "why_hook_works": "제목과 감정 상태를 짧게 압축하고 보컬 고조로 설득한다.",
            "chord_progression": "I - V - vi - IV / IV - V - I",
            "arrangement": "sparse verse, piano/guitar focus, chorus strings or full-band lift",
            "vocal": "intimate verse delivery, open chorus, final adlib or harmony lift",
            "mixing": "front vocal, controlled low end, medium-long reverb, wide final chorus",
            "hit_factor": "direct emotional title, singable chorus, final chorus payoff",
            "producer_takeaway": "초반 절제와 후렴 집중, 마지막 확장을 새 곡의 감정 설계 원리로 활용한다.",
        }
    if "rock" in lowered or "metal" in lowered or "grunge" in lowered:
        return {
            "speaker_situation": "내적 긴장이나 세대적 에너지를 밴드 사운드로 밀어붙이는 화자",
            "story_flow": "리프/모티브 제시 > 벌스 긴장 > 후렴 폭발 > 브리지 또는 마지막 후렴 강화",
            "hook_type": "riff + chorus chant hook",
            "hook_location": "intro riff and chorus",
            "hook_melody_interval": "repeated note + 3rd/5th lift with guitar-riff identity",
            "hook_melody_rhythm": "driving eighth-note rock phrasing with strong downbeats",
            "why_hook_works": "리프, 제목 단서, 후렴 에너지가 같은 방향으로 반복된다.",
            "chord_progression": "i - VI - III - VII / power-chord riff loop",
            "arrangement": "signature guitar riff, band entry, dense chorus, dynamic bridge",
            "vocal": "restrained verse, pushed chorus, grit or shout at climax",
            "mixing": "guitar and vocal forward, punchy drums, compact low-mid power",
            "hit_factor": "instant riff identity and chorus release",
            "producer_takeaway": "원곡 리프를 복제하지 말고, 첫 10초 안에 새 리프나 리듬 정체성을 제시한다.",
        }
    if "hip-hop" in lowered or "trap" in lowered or "rap" in lowered:
        return {
            "speaker_situation": "자기 캐릭터, 태도, 관계 상황을 플로우로 선언하는 화자",
            "story_flow": "태도 제시 > 짧은 제목 단서 반복 > 벌스 캐릭터 확장 > 후크 재각인",
            "hook_type": "attitude lyric + rhythm hook",
            "hook_location": "chorus/title phrase",
            "hook_melody_interval": "repeated note + spoken melodic tags",
            "hook_melody_rhythm": "syncopated rap-pop cadence with quotable rests",
            "why_hook_works": "짧은 제목 단서가 플로우와 캐릭터를 동시에 설명한다.",
            "chord_progression": "minor loop / i - VI - III - VII",
            "arrangement": "808 or tight bass, sparse drums, sample/synth motif, vocal foreground",
            "vocal": "dry, close, rhythmic delivery with hook doubles",
            "mixing": "front vocal, tight low end, minimal ambience, strong transient focus",
            "hit_factor": "quotable hook phrase and strong attitude identity",
            "producer_takeaway": "긴 설명보다 한 단어/한 문장 태도를 리듬으로 각인시키는 전략을 참고한다.",
        }
    if "dance" in lowered or "disco" in lowered or "edm" in lowered or "house" in lowered or bpm >= 120:
        return {
            "speaker_situation": "감정을 몸의 움직임과 반복 가능한 제목 행동으로 바꾸는 화자",
            "story_flow": "그루브 제시 > 프리코러스 기대감 > 후렴/드롭 반복 > 포스트후크 각인",
            "hook_type": "title phrase + groove hook",
            "hook_location": "chorus or post-chorus",
            "hook_melody_interval": "repeated note + 2nd/3rd short motif",
            "hook_melody_rhythm": "four-on-the-floor or syncopated dance-pop eighth rhythm",
            "why_hook_works": "제목 단서가 리듬 위에서 몸으로 먼저 기억된다.",
            "chord_progression": "i - VI - III - VII / I - V - vi - IV",
            "arrangement": "tight drums, bass groove, synth motif, chorus layer expansion",
            "vocal": "clean rhythmic lead, stacked chorus doubles, post-hook repetition",
            "mixing": "punchy low end, bright hook elements, streaming-friendly loudness",
            "hit_factor": "danceable groove and short repeatable title hook",
            "producer_takeaway": "후렴 첫 두 마디와 포스트후크에 새 제목 리듬을 분명히 배치한다.",
        }
    return {
        "speaker_situation": "관계와 정체성을 대중적인 언어로 정리하는 화자",
        "story_flow": "상황 제시 > 감정/태도 강화 > 제목 후크 > 마지막 반복에서 확장",
        "hook_type": "lyric + melody hook",
        "hook_location": "chorus first phrase",
        "hook_melody_interval": "repeated note + 2nd/3rd singable motion",
        "hook_melody_rhythm": "mid-tempo pop phrasing with short repeated cells",
        "why_hook_works": "제목 단서가 멜로디와 리듬 양쪽에서 반복된다.",
        "chord_progression": "I - V - vi - IV",
        "arrangement": "signature intro motif, restrained verse, fuller chorus, final layer lift",
        "vocal": "conversational verse, open chorus, doubled hook",
        "mixing": "front vocal, clean stereo bed, controlled low end, polished top end",
        "hit_factor": "clear title hook and familiar-but-polished pop structure",
        "producer_takeaway": "익숙한 구조 위에 새 제목, 새 멜로디, 새 사운드 모티브를 결합한다.",
    }


def _theme_for_title(title: str, profile: dict[str, str]) -> str:
    lowered = title.lower()
    if any(token in lowered for token in ["love", "lover", "perfect", "halo", "diamonds", "yellow"]):
        return "사랑, 이상화, 관계의 확신"
    if any(token in lowered for token in ["sorry", "fake", "bad", "kill", "savage", "venom", "monster", "creep"]):
        return "갈등, 태도, 어두운 자기 인식"
    if any(token in lowered for token in ["dance", "party", "funk", "lucky", "one more time", "levels"]):
        return "몸의 움직임, 해방감, 반복 가능한 에너지"
    if any(token in lowered for token in ["spring", "memories", "photograph", "cardigan", "scientist"]):
        return "회상, 상실, 시간의 감정"
    if "speaker_situation" in profile and "고백" in profile["speaker_situation"]:
        return "개인적 고백과 감정의 축적"
    return "관계, 정체성, 감정 변화를 대중적인 후크로 압축"


def _safe_title_cue(title: str) -> str:
    words = title.replace("/", " ").split()
    return " ".join(words[:8])
