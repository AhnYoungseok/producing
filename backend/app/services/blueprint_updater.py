from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.services.conversation_coach import COMPOSER_STAGES, get_stage_title


COPYRIGHT_NOTICE = (
    "Hit Song Lab은 기존 곡을 복제하기 위한 도구가 아닙니다. "
    "히트곡의 창작 원리를 분석하고, 사용자가 자신만의 새로운 음악을 만들도록 돕는 창작 보조 도구입니다."
)


def initialize_interactive_blueprint(project: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a conversation-ready blueprint while preserving older generated fields."""
    blueprint = deepcopy(existing or {})
    blueprint.setdefault("mode", "interactive_composer_coach")
    blueprint.setdefault("current_stage", 1)
    blueprint.setdefault("stage_title", get_stage_title(int(blueprint["current_stage"])))
    blueprint.setdefault("is_complete", False)
    blueprint.setdefault("conversation_history", [])
    blueprint.setdefault("decisions", [])
    blueprint.setdefault("last_options", [])
    blueprint.setdefault("reference_recommendations", [])
    blueprint.setdefault("reference_common_patterns", [])
    blueprint.setdefault("creative_principles", [])
    blueprint.setdefault("copyright_notice", COPYRIGHT_NOTICE)
    blueprint.setdefault(
        "concept",
        {
            "project_title": project.get("title"),
            "genre": project.get("target_genre"),
            "mood": [project.get("target_mood")] if project.get("target_mood") else [],
            "target_listener": project.get("target_listener"),
            "theme": project.get("theme"),
        },
    )
    blueprint.setdefault("emotion_curve", [])
    blueprint.setdefault("structure_plan", {})
    blueprint.setdefault("title_candidates", [])
    blueprint.setdefault("lyrics_direction", {})
    blueprint.setdefault("harmony_plan", {})
    blueprint.setdefault("melody_direction", blueprint.get("melody_plan", {}))
    blueprint.setdefault("hook_plan", {})
    blueprint.setdefault("rhythm_groove", blueprint.get("rhythm_plan", {}))
    blueprint.setdefault("arrangement_direction", blueprint.get("arrangement_plan", {}))
    blueprint.setdefault("vocal_production", blueprint.get("vocal_plan", {}))
    blueprint.setdefault("sound_mixing", blueprint.get("mixing_plan", {}))
    blueprint.setdefault("final_production_guide", blueprint.get("final_production_guide", ""))
    blueprint.setdefault("manual_notes", [])
    return blueprint


def apply_user_turn(
    project: dict[str, Any],
    blueprint: dict[str, Any],
    message: str | None,
    selected_option_id: str | None,
) -> dict[str, Any]:
    """Apply the user's current answer to the blueprint and advance the stage."""
    if not message and not selected_option_id:
        return blueprint

    updated = deepcopy(blueprint)
    current_stage = int(updated.get("current_stage") or 1)
    selected_option = _find_option(updated.get("last_options", []), selected_option_id)
    user_text = _user_history_text(message, selected_option)

    _append_history(updated, "user", user_text, current_stage)

    decision = {
        "stage": current_stage,
        "stage_title": get_stage_title(current_stage),
        "message": message,
        "selected_option_id": selected_option_id,
        "selected_label": selected_option.get("label") if selected_option else None,
        "selected_summary": selected_option.get("summary") if selected_option else None,
        "created_at": _now(),
    }
    updated["decisions"].append(decision)

    if selected_option:
        _deep_merge(updated, selected_option.get("blueprint_updates", {}))
    elif message:
        updated["manual_notes"].append({"stage": current_stage, "stage_title": get_stage_title(current_stage), "content": message})
        _apply_manual_note(updated, current_stage, message)

    if current_stage >= len(COMPOSER_STAGES):
        updated["current_stage"] = len(COMPOSER_STAGES)
        updated["is_complete"] = True
    else:
        updated["current_stage"] = current_stage + 1
        updated["is_complete"] = False
    updated["stage_title"] = get_stage_title(int(updated["current_stage"]))
    return updated


def attach_assistant_turn(
    blueprint: dict[str, Any],
    assistant_message: str,
    options: list[dict[str, Any]],
    recommendations: dict[str, Any] | None,
) -> dict[str, Any]:
    updated = deepcopy(blueprint)
    current_stage = int(updated.get("current_stage") or 1)
    updated["stage_title"] = get_stage_title(current_stage)
    updated["last_options"] = options
    if recommendations:
        updated["reference_recommendations"] = recommendations.get("recommendations", [])
        updated["reference_common_patterns"] = recommendations.get("common_patterns", [])
        updated["creative_principles"] = recommendations.get("creative_principles", [])
        updated["plagiarism_risks"] = recommendations.get("plagiarism_risks", [])

    history = updated.setdefault("conversation_history", [])
    if not history or history[-1].get("role") != "assistant" or history[-1].get("content") != assistant_message:
        _append_history(updated, "assistant", assistant_message, current_stage)
    return updated


def project_plan_updates(blueprint: dict[str, Any]) -> dict[str, Any]:
    return {
        "concept": blueprint.get("concept", {}),
        "lyrics_plan": {
            "title_candidates": blueprint.get("title_candidates", []),
            "lyrics_direction": blueprint.get("lyrics_direction", {}),
        },
        "harmony_plan": blueprint.get("harmony_plan", {}),
        "melody_plan": blueprint.get("melody_direction", {}),
        "hook_plan": blueprint.get("hook_plan", {}),
        "arrangement_plan": blueprint.get("arrangement_direction", {}),
    }


def _append_history(blueprint: dict[str, Any], role: str, content: str, stage: int) -> None:
    blueprint.setdefault("conversation_history", []).append(
        {
            "role": role,
            "content": content,
            "stage": stage,
            "stage_title": get_stage_title(stage),
            "created_at": _now(),
        }
    )


def _find_option(options: list[dict[str, Any]], selected_option_id: str | None) -> dict[str, Any] | None:
    if not selected_option_id:
        return None
    return next((option for option in options if option.get("id") == selected_option_id), None)


def _user_history_text(message: str | None, selected_option: dict[str, Any] | None) -> str:
    if selected_option and message:
        return f"{selected_option['label']} 선택. 추가 메모: {message}"
    if selected_option:
        return f"{selected_option['label']} 선택 - {selected_option['summary']}"
    return message or "다음 단계로 진행"


def _apply_manual_note(blueprint: dict[str, Any], stage: int, message: str) -> None:
    manual_key_map = {
        1: ("concept", "direction"),
        2: ("concept", "mood_note"),
        5: ("concept", "manual_concept"),
        6: ("lyrics_direction", "manual_note"),
        7: ("emotion_curve_note", None),
        8: ("structure_plan", "manual_note"),
        9: ("harmony_plan", "manual_note"),
        10: ("melody_direction", "manual_note"),
        11: ("hook_plan", "manual_note"),
        12: ("rhythm_groove", "manual_note"),
        13: ("arrangement_direction", "manual_note"),
        14: ("vocal_production", "manual_note"),
        15: ("sound_mixing", "manual_note"),
        16: ("final_production_guide", None),
    }
    key_info = manual_key_map.get(stage)
    if key_info is None:
        return
    key, subkey = key_info
    if subkey is None:
        if key == "final_production_guide":
            blueprint[key] = message
        else:
            blueprint[key] = message
        return
    current = blueprint.setdefault(key, {})
    if isinstance(current, dict):
        current[subkey] = message


def _deep_merge(target: dict[str, Any], updates: dict[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = deepcopy(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
