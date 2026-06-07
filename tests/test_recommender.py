from citta_console.recommender import recommend_actions


def test_recommends_inspect_and_pause_for_edit_after_failed_test() -> None:
    actions = recommend_actions(
        {"current_state": "test_failed_after_file_edit"},
        [{"type": "edit_after_failed_test", "severity": "high", "reason": "bad"}],
    )

    assert [action["action"] for action in actions[:2]] == ["inspect_error", "pause"]


def test_recommends_continue_when_no_risk() -> None:
    actions = recommend_actions({"current_state": "latest_action_completed"}, [])

    assert actions[0]["action"] == "continue"
