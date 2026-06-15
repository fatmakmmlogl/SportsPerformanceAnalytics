"""
Unit testler: DatabaseManager
"""

import unittest
import os
import tempfile
from database.database_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        # Her test için geçici bir veritabanı kullan
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db  = DatabaseManager(db_path=self.tmp.name)

    def tearDown(self):
        self.tmp.close()
        os.unlink(self.tmp.name)

    def test_create_and_get_athlete(self):
        athlete_id = self.db.create_athlete("Test Sporcu", age=25, sport="Fitness")
        athlete    = self.db.get_athlete(athlete_id)
        self.assertIsNotNone(athlete)
        self.assertEqual(athlete["name"], "Test Sporcu")
        self.assertEqual(athlete["age"], 25)

    def test_get_or_create_athlete_idempotent(self):
        id1 = self.db.get_or_create_athlete("Ali")
        id2 = self.db.get_or_create_athlete("Ali")
        self.assertEqual(id1, id2)

    def test_create_session(self):
        athlete_id = self.db.create_athlete("Test")
        session_id = self.db.create_session(athlete_id, "squat", score=75.0)
        sessions   = self.db.get_sessions_by_athlete(athlete_id)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["exercise_type"], "squat")

    def test_save_metric(self):
        athlete_id = self.db.create_athlete("Test")
        session_id = self.db.create_session(athlete_id, "squat")
        metric_id  = self.db.save_metric(session_id, 10, 90.0, 80.0, 85.0, 70.0, 75.0)
        metrics    = self.db.get_metrics_by_session(session_id)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0]["repetition_count"], 10)

    def test_get_athlete_stats(self):
        athlete_id = self.db.create_athlete("İstatistik Sporcu")
        self.db.create_session(athlete_id, "squat", score=80.0)
        self.db.create_session(athlete_id, "pushup", score=70.0)
        stats = self.db.get_athlete_stats(athlete_id)
        self.assertEqual(stats["total_sessions"], 2)
        self.assertAlmostEqual(stats["average_score"], 75.0, places=1)
        self.assertAlmostEqual(stats["best_score"],    80.0, places=1)


if __name__ == "__main__":
    unittest.main()
