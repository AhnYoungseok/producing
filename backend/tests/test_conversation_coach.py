from app.services.blueprint_updater import apply_user_turn, attach_assistant_turn, initialize_interactive_blueprint
from app.services.conversation_coach import compose_assistant_turn
from app.services.recommendation_service import build_reference_recommendations


def test_initial_composer_turn_has_three_options() -> None:
    project = _project()
    blueprint = initialize_interactive_blueprint(project)
    recommendations = build_reference_recommendations(project, [], [], "70BPM K-pop ballad")

    turn = compose_assistant_turn(project, blueprint, recommendations)

    assert turn["stage"] == 1
    assert "만들고 싶은 곡" in turn["stage_title"]
    assert len(turn["options"]) == 3
    assert all("blueprint_updates" in option for option in turn["options"])


def test_selected_option_updates_blueprint_and_advances_stage() -> None:
    project = _project()
    blueprint = initialize_interactive_blueprint(project)
    recommendations = build_reference_recommendations(project, [], [], None)
    first_turn = compose_assistant_turn(project, blueprint, recommendations)
    blueprint = attach_assistant_turn(blueprint, first_turn["assistant_message"], first_turn["options"], None)

    updated = apply_user_turn(project, blueprint, None, "stage_1_b")
    second_turn = compose_assistant_turn(project, updated, recommendations)

    assert updated["current_stage"] == 2
    assert updated["concept"]["direction"] == "감정 고조형 K-pop 발라드"
    assert updated["decisions"][0]["selected_option_id"] == "stage_1_b"
    assert second_turn["stage"] == 2
    assert len(second_turn["options"]) == 3


def test_reference_recommendations_are_attached_on_stage_three() -> None:
    project = _project()
    blueprint = initialize_interactive_blueprint(project)
    blueprint["current_stage"] = 3
    recommendations = build_reference_recommendations(project, [], [], "정승환 태연 발라드")
    turn = compose_assistant_turn(project, blueprint, recommendations)
    updated = attach_assistant_turn(blueprint, turn["assistant_message"], turn["options"], turn["recommendations"])

    assert turn["recommendations"] is not None
    assert len(updated["reference_recommendations"]) >= 3
    assert "plagiarism_risks" in updated


def _project() -> dict:
    return {
        "id": "project_test",
        "title": "Late Night Ballad",
        "target_genre": "K-pop Ballad",
        "target_mood": "그리움",
        "target_listener": "감성 발라드 청자",
        "reference_song_ids": [],
        "theme": "늦은 밤의 회상",
        "vocal_style": "warm vocal",
        "bpm_range": "70-80",
    }
