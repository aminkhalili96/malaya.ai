import os
import tempfile

from src.storage import SQLiteStore


def test_sqlite_store_cache_and_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = SQLiteStore(db_path)

        store.response_cache_set("key1", {"answer": "ok"}, 60)
        cached = store.response_cache_get("key1")
        assert cached["answer"] == "ok"

        store.tool_cache_set("tool-key", "value", 60)
        assert store.tool_cache_get("tool-key") == "value"

        store.set_project_memory("proj-1", "summary", 3)
        memory = store.get_project_memory("proj-1")
        assert memory["summary"] == "summary"
        assert memory["message_count"] == 3

        store.create_share("share-1", "conversation", {"hello": "world"}, 60)
        share = store.get_share("share-1")
        assert share["share_type"] == "conversation"

        store.create_feedback(
            "feedback-1",
            "conv-1",
            "msg-1",
            "up",
            "Great response",
            "openai",
            "gpt-4o",
            {"quality": "high"},
        )
        feedback = store.get_feedback("feedback-1")
        assert feedback["rating"] == "up"
        assert feedback["message_id"] == "msg-1"
