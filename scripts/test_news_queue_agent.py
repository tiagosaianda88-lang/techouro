import os
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

import news_queue_agent


class NewsQueueAgentTests(unittest.TestCase):
    def test_old_screenshot_name_is_stale_even_with_fresh_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp)
            captured = news_queue_agent.datetime.now() - timedelta(days=3)
            old_capture = source_dir / captured.strftime("Captura de ecra %Y-%m-%d, as %H.%M.%S.png")
            old_capture.write_text("old", encoding="utf-8")

            fresh, stale = news_queue_agent.partition_fresh_and_stale(
                source_dir,
                [old_capture],
                daily_hours=48,
                monthly_days=45,
            )

            self.assertEqual(fresh, [])
            self.assertEqual(stale, [old_capture])

    def test_monthly_source_uses_longer_retention_with_capture_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp)
            monthly_dir = source_dir / "pc guia monthly tech.txt"
            monthly_dir.mkdir()
            captured = news_queue_agent.datetime.now() - timedelta(days=3)
            old_capture = monthly_dir / captured.strftime("Captura de ecra %Y-%m-%d, as %H.%M.%S.png")
            old_capture.write_text("old", encoding="utf-8")

            fresh, stale = news_queue_agent.partition_fresh_and_stale(
                source_dir,
                [old_capture],
                daily_hours=48,
                monthly_days=45,
            )

            self.assertEqual(fresh, [old_capture])
            self.assertEqual(stale, [])

    def test_oldest_first_sorts_by_capture_date_before_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp)
            now = news_queue_agent.datetime.now()
            newer_name = source_dir / now.strftime("Captura de ecra %Y-%m-%d, as %H.%M.%S.png")
            older_name = source_dir / (now - timedelta(minutes=5)).strftime("Captura de ecra %Y-%m-%d, as %H.%M.%S.png")
            newer_name.write_text("newer", encoding="utf-8")
            older_name.write_text("older", encoding="utf-8")
            os.utime(older_name, (news_queue_agent.datetime.now().timestamp(),) * 2)
            os.utime(newer_name, (1, 1))

            ordered = news_queue_agent.sorted_sources(
                source_dir,
                "oldest-first",
                max_age_hours=48,
                monthly_max_age_days=45,
            )

            self.assertEqual(ordered[:2], [older_name, newer_name])


if __name__ == "__main__":
    unittest.main()
