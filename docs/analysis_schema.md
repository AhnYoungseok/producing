# Hit Song Analysis Schema

This document defines the producer-style research fields used by Hit Song Lab. Values should include `data_confidence` when possible:

- `high`: reliable structured API, user-verified data, or user-owned audio analysis
- `medium`: multiple-source or curated research summary
- `low`: metadata-only or heuristic estimate

## Identity

| Field | Type | Notes |
| --- | --- | --- |
| song_id | string | Internal ID |
| title | string | Song title |
| artist | string | Main artist |
| release_year | number/null | Release year |
| genre | string | Main genre or hybrid genre |
| country | string | Primary market/country |
| youtube_url | string/null | Reference link only; no audio extraction |
| video_type | string/null | Official MV, lyric video, live, cover, fan upload, search-result reference |

## Core Musical Features

| Field | Type | Notes |
| --- | --- | --- |
| bpm | number/null | From reliable API, user input, permitted audio, or curated estimate |
| key | string/null | Key estimate or verified key |
| chord_progression | object/string | Section-level preferred |
| verse_progression | string/null | Verse chords |
| pre_chorus_progression | string/null | Pre-chorus chords |
| chorus_progression | string/null | Chorus chords |
| bridge_progression | string/null | Bridge chords |
| harmonic_mood | string[] | Emotional function of harmony |
| modulation | boolean/null | Key change if known |

## Structure and Energy

| Field | Type | Notes |
| --- | --- | --- |
| song_structure | string[] | Example: Intro, Verse, Pre-Chorus, Chorus, Bridge, Final Chorus |
| intro_length | number/null | Seconds or bars |
| verse_length | number/null | Seconds or bars |
| pre_chorus_length | number/null | Seconds or bars |
| chorus_length | number/null | Seconds or bars |
| bridge_length | number/null | Seconds or bars |
| first_chorus_time | number/null | Seconds from start |
| final_chorus_expansion | string | Added vocals, adlibs, strings, drums, key change, etc. |
| energy_curve | number[] | Section-level 1-10 estimate |
| repetition_variation_ratio | string/null | How repetition and variation are balanced |

## Hook and Melody

| Field | Type | Notes |
| --- | --- | --- |
| hook_type | string | Lyric, melody, rhythm, sound, title repetition, call-and-response, silence/stop |
| hook_location | string | Chorus first phrase, post-chorus, intro motif, bridge climax, etc. |
| hook_repeat_strategy | string | How the hook repeats or changes |
| lyric_hook_cue | string | Short cue only; do not store full lyrics automatically |
| short_hook_cue | string | 10 words or fewer |
| melody_range | string/null | Example: A3-E5 if user/score data available |
| chorus_first_note | string/null | If user/score data available |
| chorus_peak_position | string/null | First half, second half, final chorus, bridge, etc. |
| melody_interval_summary | string | Stepwise, 2nd/3rd motif, 4th/5th lift, repeated note, etc. |
| melody_rhythm_summary | string | Sustained ballad notes, eighth-note chant, syncopated pop rhythm, etc. |
| hook_melody_contour | string | Rise, fall, arch, repeated-note tag |
| singability | string | Low/medium/high |

## Lyrics and Story

| Field | Type | Notes |
| --- | --- | --- |
| lyrics_source | string | user_provided, summary_only, external_link, unavailable |
| lyric_theme | string | Main topic |
| core_emotion | string | Main emotion |
| mood_keywords | string[] | Up to 10 |
| main_keywords | string[] | Important words/images, not full lyric lines |
| speaker | string | Point of view |
| addressee | string | Who the speaker addresses |
| situation | string | Story setup |
| story_flow | string | Verse to chorus emotional logic |
| verse_role | string | Lyric role |
| pre_chorus_role | string | Lyric role |
| chorus_role | string | Lyric role |
| bridge_role | string | Lyric role |
| title_usage | string | Where/how title appears |
| repeated_phrase_summary | string | Summary only unless user provided text |
| metaphor_level | string | low/medium/high |

## Arrangement

| Field | Type | Notes |
| --- | --- | --- |
| arrangement_instruments | string[] | Main instruments |
| intro_instruments | string[] | If known |
| verse_instruments | string[] | If known |
| pre_chorus_instruments | string[] | If known |
| chorus_instruments | string[] | If known |
| bridge_instruments | string[] | If known |
| final_chorus_instruments | string[] | If known |
| build_strategy | string | Sparse verse, fuller chorus, final lift, drop, etc. |
| removal_strategy | string/null | Drop-out, breakdown, silence, half-time, etc. |
| fx_usage | string | Risers, impacts, vocal chops, transitions |
| space_design | string | Dry/intimate, wide/reverb, cinematic, club, etc. |

## Vocal Production

| Field | Type | Notes |
| --- | --- | --- |
| vocal_tone | string | Warm, airy, raspy, close, bright, etc. |
| verse_delivery | string | Conversational, restrained, rhythmic, etc. |
| chorus_delivery | string | Open, belted, stacked, chant-like, etc. |
| breath_usage | string/null | If known |
| doubling | string/null | Verse/chorus/final chorus |
| harmony | string/null | Where background vocals appear |
| adlib_usage | string/null | Final chorus, bridge, outro |
| vocal_effects | string[] | Reverb, delay, tuning, distortion, etc. |
| vocal_position | string | Front, blended, wide stack, etc. |

## Mixing and Sound

| Field | Type | Notes |
| --- | --- | --- |
| low_end_density | string | Controlled, heavy, sub-forward, light |
| midrange_presence | string | Vocal/guitar/synth focus |
| high_end_brightness | string | Dark, balanced, bright |
| stereo_width | string | Narrow, moderate, wide |
| reverb_amount | string | Dry, medium, large |
| delay_usage | string | Slap, throw, long delay, minimal |
| drum_presence | string | Front, soft, punchy, washed |
| instrument_separation | string | Dense, clean, layered |
| mastering_style | string | Streaming pop, radio loud, dynamic ballad |

## Producer Notes

| Field | Type | Notes |
| --- | --- | --- |
| hit_factor | string | Why the song is memorable |
| first_30_seconds_impact | string | Strong/medium/low |
| short_form_potential | string | Strong/medium/low |
| live_moment | string | Singalong, adlib, dance point, drop |
| producer_note | string | Producer interpretation |
| songwriting_reference_point | string | What a songwriter can learn |
| avoid_copying | string[] | Lyrics, melody, riffs, adlibs, sound signatures |
| creative_application | string[] | Transferable principles for original songs |

## Minimal JSON Shape

```json
{
  "title": "Example Song",
  "artist": "Example Artist",
  "release_year": 2024,
  "genre": "K-pop Pop",
  "country": "KR",
  "bpm": {
    "value": 120,
    "confidence": "medium",
    "source": "curated research"
  },
  "key": {
    "value": "A minor",
    "confidence": "medium",
    "source": "curated research"
  },
  "chord_progression": {
    "chorus": "i - VI - III - VII",
    "confidence": "low",
    "source": "example placeholder"
  },
  "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Final Chorus"],
  "lyrics": {
    "source": "summary_only",
    "theme": "longing and recovery",
    "short_hook_cue": "title cue only"
  },
  "hook": {
    "type": "lyric + melody hook",
    "location": "chorus first phrase",
    "melody_interval_summary": "repeated note + 2nd/3rd motion",
    "melody_rhythm_summary": "syncopated eighth-note pop phrase"
  },
  "producer_notes": {
    "hit_factor": "clear title cue and chorus lift",
    "creative_application": ["Use the title as a new short hook cue."],
    "avoid_copying": ["Do not reuse original lyrics, melody, riffs, or sound signatures."]
  }
}
```
