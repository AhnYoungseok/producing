# Changelog

## 2026-06-28

### Fixed

- Rebuilt Composer Coach concept flow around structured archetypes, reset support, concept-aware reference matching, and harmony briefs that vary from the matched reference statistics.
- Changed the default auto-reference batch settings to safe development defaults: disabled and no startup run unless explicitly enabled by environment variables.
- Replaced broken Hook Lab UI copy and backend Hook Lab fallback strings so loading, error, empty, search, filter, confidence, and pagination states are readable.
- Replaced the frontend API fallback error message with a stable readable message.
- Updated stale project docs that still described Hook Lab as per-song analysis fetching and auto batch as enabled by default.

### Added

- Added public-site visual graph panels for concept radar, current reference-library distributions, and selected-reference combination analysis so concept, genre, BPM, year, confidence, key, hook, and risk signals are visible at a glance.
- Added a public-site candidate-to-final selection flow so type-matched 20-song recommendations and manually chosen references gather into one final-pick panel before brief/detail generation.
- Added explicit `최종 곡에 담기` actions to every type-matched 20-song candidate row so recommended candidates can be moved into the final selected-song set without searching again.
- Added clearer `최종 선택곡에 담기` buttons on both candidate recommendations and searched reference cards, plus an explicit rule panel stating that briefs and composition plans use only final selected-song analysis/statistics.
- Added an editable public-site chord design pad inside the composition plan, with local Web Audio chord playback and stop controls for auditioning revised progressions without using original-song audio.
- Added a right-side public-site creation workspace that groups the creative brief, composition plan, chord editing, and audition controls into a structured desktop rail.
- Added an in-page official YouTube preview panel with `현재 페이지에서 듣기` buttons on reference cards, candidate rows, and final-pick rows; direct video URLs render through YouTube's iframe player, while search-only rows show a safe fallback and a local direct-URL save field.
- Added a final-pick action directly inside the in-page YouTube preview panel so users can listen first and immediately move the song into the final selected set.
- Added direct YouTube embed hints for frequently surfaced hit references and changed search-only rows to a clear `YouTube 링크 등록/듣기` flow with save and clipboard actions, so `현재 페이지에서 듣기` only appears when an iframe-ready video ID is available.
- Moved the final selected-song panel to the top of the right-side creation rail and placed the composition plan directly below it, so final picks stay visible before detailed song design.
- Moved the reference finder directly below the type-matched 20-song candidate area, labeled type matches as the first-priority closest recommendations and the finder as second-priority conditional search, with only 10 reference cards shown by default.
- Restored the type-matched candidate area as an always-visible first-priority panel with an empty state and automatic 20-song concept matches after concept selection.
- Expanded the right-side creation workspace substantially and restyled the composition plan with a light-green background, stronger border, larger content area, section tables, and readiness meter graphs.
- Added public-site automatic chorus/hook candidate panels for each reference card, showing likely chorus windows, hook strength, lyric-structure hints, melody/rhythm cues, chord hints, creative-use notes, and confidence without storing full lyrics or extracting YouTube audio.
- Added public-site selected-reference combination analysis with average BPM, common key, common chord family, hook type, mood, arrangement signals, conflict notes, and arrangement risk before generating the brief.
- Added mood-coordinate recommendations to the public-site concept graph, mapping dark/bright and calm/intense drag values into BPM, key, chord color, hook style, arrangement, and brief tone.
- Added public-site copy controls for the full brief, chord-only section, chorus/hook section, and today's work instructions, with a clipboard fallback for less-permissive local contexts.
- Added an `AI 5-axis analysis draft` action to public reference cards, filling missing lyric-structure, melody, rhythm/groove, chord, and accompaniment/production analysis fields from available metadata while preserving user-entered values.
- Added public-site reference-song analysis panels for the three required core fields: chorus/hook lyric excerpt, chord progression analysis, and hook melody analysis.
- Added local public-site editing for chorus/hook excerpts, lyric source/input/permission/visibility/confidence metadata, section chord progressions, Roman numeral conversion, harmonic interpretation, and hook melody summaries.
- Expanded the public-site required analysis model from 3 fields to 5 creative axes: lyrics, melody, rhythm/groove, chord progression, and accompaniment/production method.
- Added Composer Coach hook-melody sketches directly under the lyric hook examples, with three generated contour/rhythm variants and browser Web Audio playback for quick auditioning.
- Added a public-site composition plan panel next to the creation brief, separating song structure, chord progression, core lyric, and accompaniment/instrument recommendations from the long-form brief.
- Added MBTI-style public-site concept type naming, with compact four-letter concept codes and Korean type names shown in the concept panel, hints, brief, and composition plan.
- Added a top-level public-site random concept button and renamed the creation action to `브리프 상세 생성`.
- Added a public-site concept type axis guide so four-letter codes map clearly to expression direction, emotional temperature, time direction, and sound texture.
- Added `POST /api/composer/{project_id}/reset` to restart the Composer Coach concept flow without manually editing the database.
- Added and tested the bulk Hook Lab summary response shape for `GET /api/library/hook-summaries`, including country, year, BPM, key, hook cue/type/location, melody summaries, lyrics source status, confidence, and updated timestamps.
- Added a Hook Lab endpoint structure test for the bulk summary payload.
- Added Hook Lab client-side search, genre filtering, confidence filtering, pagination, selected-reference count, and direct YouTube search links.
- Added recommendation harmony statistics so Composer Coach can use selected/recommended songs' verse, pre-chorus, chorus, and bridge progressions instead of repeating a fixed fallback.

### Changed

- Strengthened the public-site creation brief so it now includes selected-song combination analysis, automatic chorus/hook candidate analysis, and a 20-part composer brief ending with concrete 30-minute production instructions.
- Changed public-site brief generation so final selected songs are the primary source for the detailed brief and composition plan, while type-matched songs remain a candidate pool until explicitly chosen.
- Changed public-site composition-plan data sourcing so candidate pools, search results, concept matches, and default hit lists are never used for detailed brief/composition design until the user adds songs to the final-pick panel.
- Changed the public-site desktop layout so concept/final-pick work stays on the left, the creative brief/composition design stays on the right, and reference search moves into a wider full-width panel below.
- Changed the public-site concept graph labels to the requested emotion-space model: dark to bright on the X axis and calm to intense on the Y axis, with keyboard arrow support in addition to mouse/touch drag.
- Changed public-site reference cards so automatic hook candidates appear before the detailed analysis strip, making chorus/hook, chord, melody, rhythm, and accompaniment signals visible without opening every detail panel.
- Optimized public-site concept selection so button state updates immediately while heavy recommendation and brief regeneration are debounced and cached.
- Expanded the public-site reference-song finder list height so more songs remain visible while composing, especially on desktop and mobile review screens.
- Moved the public-site hit-song statistics section to the end of the page and compressed it into a short summary so creation and reference-song workflows stay primary.
- Expanded the public-site reference-song finder scroll area again, more than doubling the visible song-list height on desktop and increasing the mobile/tablet list area.
- Moved the concept reset button to the top of the concept section and the brief reset button to the top of the creation brief section.
- Updated the public-site concept label to the softer `감성 / 말투`.
- Changed lyric analysis completion so structure-only analysis can count as analyzed while still showing that the original chorus/hook text must be manually verified before any excerpt is displayed.
- Upgraded the public-site concept finder from a single coarse persona label into an 8-axis visual persona model with detailed subtype codes, coordinate map, score bars, rationale notes, and nearest archetype ranking.
- Strengthened source-safe harmony, melody, and hook analyzers so user-provided chords/lyrics produce detailed section functions, tension/release notes, reharmonization options, hook design, melody contour/rhythm summaries, and explicit confidence/source labels without using YouTube audio extraction.
- Updated Hook Lab so it loads reference summaries through one bulk API call instead of relying on per-song analysis requests.
- Expanded confidence metadata for local and cloud/ledger hook summaries while preserving legacy field names for compatibility.
- Reworked Composer Coach so the creation brief is the most prominent section, with practical concept, structure, harmony, hook, arrangement, vocal, and plagiarism-prevention guidance.
- Updated Composer Coach harmony options and the creation brief to prioritize reference-song chord statistics, then transform them with slash chords, secondary dominants, modal interchange, sus/add9 voicings, and new bass motion.
- Changed the public-site harmony brief generator so it selects distinct harmony palettes from concept axes, sound lane, BPM/genre signals, and available chord samples instead of repeating one fixed G major / E minor fallback.
- Added K-pop/global groove harmony detection so Korean pop hooks, post-chorus/performance hooks, drum grooves, and bass/synth references produce dedicated F/D minor or Ab/F minor progression plans instead of falling back to the generic ballad template.
- Added per-reference chord progression analysis to the public-site brief and song detail cards, including raw chord availability, functional family, confidence/source status, and a transformed new-song progression for each recommended song.
- Removed age/speaker-based concept categorization from the public-site concept picker and brief copy; concept selection now starts from speaking position, viewpoint, tone, attitude, emotion, situation, and sound.
- Made the public-site persona graph interactive: dragging the center point now adjusts concept/emotion axes, persists the adjustment, and recalculates archetype, recommended songs, and creation brief around the new coordinates.
- Updated the public-site creation brief so recommended-song chorus/hook lyric status, per-section chord/Roman analysis, and hook melody status are reflected in the concept brief and statistics.
- Updated public-site reference cards and briefs to show missing rhythm and accompaniment/production analysis explicitly instead of treating them as optional notes.
- Replaced broken Korean UI copy in Hook Lab and Composer Coach with clear Korean workflow/status text.

### Verified

- Public-site script syntax check passed with `node --check`.
- Public-site local browser check passed for candidate pool creation, final-pick selection, detailed brief generation, editable chord plan updates, Web Audio chord playback/stop controls, and no console errors.
- Public-site local browser check passed for final-selected-only design behavior: no selected songs keeps the plan/chord editor empty, searched reference cards and type-matched candidate rows both add songs through `최종 선택곡에 담기`, and generated plans use the selected-song set.
- Public-site local browser layout check passed: the creative brief/composition workspace renders as a right-side sticky rail on desktop, with no console errors and no literal `undefined`, `null`, or `NaN`.
- Public-site local browser check passed for the YouTube preview fallback: preview buttons open the in-page panel, search-only rows show the direct-link input and YouTube search action, and no console errors occurred.
- Public-site local browser check passed for preview-to-final-pick flow: `현재 페이지에서 듣기` opens the preview panel, `이 곡을 최종 선택곡에 담기` adds the song, disables itself as selected, updates the selected count, and activates the composition plan.
- Public-site local browser check passed for type-matched candidate rows: `유형 맞춤 20곡` renders 20 direct `최종 곡에 담기` buttons, clicking one moves it into the final selected-song set, disables the source row, and activates the composition plan.
- Public-site local browser check passed for the YouTube preview repair: known hit references now render an iframe-ready YouTube embed URL, while search-only references show the direct URL registration panel instead of a blank player.
- Public-site local browser layout check passed for the right rail reorder: the final selected-song panel appears before the composition plan, and the creation rail remains scrollable on desktop.
- Public-site local browser check passed for the candidate/reference priority layout: type-matched candidates appear before the conditional reference finder, the finder renders 10 cards by default, and `더 보기` expands in 10-song increments.
- Public-site local browser check passed for the workspace repair: candidate matches auto-render after concept selection, final-pick plus brief generation updates the composition plan, the plan shows tables and meter graphs, and the right rail expands well beyond the short viewport card.
- Public-site local HTTP browser check passed: 80 reference cards rendered, automatic hook panels and mood-coordinate recommendations were visible, no console errors were reported, and no literal `undefined`, `null`, or `NaN` appeared.
- Public-site mood coordinate keyboard adjustment changed the creation brief in-browser without console errors.
- Backend tests passed with `AUTO_REFERENCE_BATCH_ENABLED=false`: 27 tests.
- Backend tests passed with `AUTO_REFERENCE_BATCH_ENABLED=false`: 28 tests after Composer reset/concept updates.
- Frontend `npm run lint` passed.
- Frontend `npm run build` passed.
- FastAPI server started successfully on port 8110 with auto batch disabled.
- HTTP checks passed for `/docs`, `/api/research/auto-batch/status`, `/api/library/hook-summaries`, bad song ID 404, and main frontend routes.

## 2026-06-22

### Added

- Added automatic local reference-song batch worker.
- Added curated real-hit-song catalog for continued 10-song batches after the initial queue is exhausted.
- Added Hook Lab auto-batch status panel.
- Added Hook Lab lyrics-source status column.
- Added song-detail lyrics display card for user-provided lyrics.
- Added support for updating lyrics/chords/notes on curated reference-song profiles.
- Added a Billboard chart ingestion script that prepends current Hot 100 and Korea Global K-Songs references to the safe local queue.
- Added project documentation:
  - `PROJECT_STATUS.md`
  - `TODO.md`
  - `ISSUES.md`
  - `NEXT_STEPS.md`
  - `docs/analysis_schema.md`
  - `sample_data/songs.json`

### Changed

- Updated root README with current environment variables, auto-batch behavior, and current documentation map.
- Updated backend README with auto-batch settings and safer test command.
- Updated frontend README with Hook Lab route and backend URL notes.
- Preserved existing BPM/Key/public metadata fields when a user updates lyrics/chords on curated profiles.
- Expanded `backend/seeds/cloud_reference_queue.json` with additional real domestic and international hit-song reference profiles so the 10-minute auto-batch worker can continue after the first local queue is exhausted.
- Prepended current Billboard Hot 100 and Billboard Korea Global K-Songs candidates to the reference queue with chart rank/source metadata and low-confidence musical fields where public metadata was not available.

### Verified

- Backend Python compile check passed for modified modules.
- Backend test suite passed: 25 tests.
- Frontend `npm run lint` passed.
- Frontend `npm run build` passed.

### Notes

- Automatic lyrics collection was not added. Full lyrics must be user-provided.
- YouTube audio extraction remains explicitly unsupported and forbidden.
- Older note: this folder was previously not initialized as a git repository. It is now on branch `main` in the checked workspace.
