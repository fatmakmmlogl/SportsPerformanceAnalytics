"""
Unit testler: RepCounter
"""

import unittest
from models.rep_counter import RepCounter


class TestRepCounter(unittest.TestCase):

    def setUp(self):
        self.counter = RepCounter()

    def test_squat_rep_counted(self):
        """Squat aşağı→yukarı geçişi 1 rep saymalı."""
        # Aşağı faz
        self.counter.update("squat", {"left_knee": 85, "right_knee": 85})
        # Yukarı faz
        self.counter.update("squat", {"left_knee": 165, "right_knee": 165})
        self.assertEqual(self.counter.get_count("squat"), 1)

    def test_pushup_rep_counted(self):
        """Push-up aşağı→yukarı geçişi 1 rep saymalı."""
        self.counter.update("pushup", {"left_elbow": 80, "right_elbow": 80})
        self.counter.update("pushup", {"left_elbow": 160, "right_elbow": 160})
        self.assertEqual(self.counter.get_count("pushup"), 1)

    def test_no_rep_without_down_phase(self):
        """Aşağı faz olmadan yukarı faz rep saymamalı."""
        self.counter.update("squat", {"left_knee": 170, "right_knee": 170})
        self.assertEqual(self.counter.get_count("squat"), 0)

    def test_reset(self):
        """Reset sonrası tüm sayaçlar sıfırlanmalı."""
        self.counter.update("squat", {"left_knee": 85, "right_knee": 85})
        self.counter.update("squat", {"left_knee": 165, "right_knee": 165})
        self.counter.reset()
        self.assertEqual(self.counter.get_count("squat"), 0)

    def test_total_reps(self):
        """Toplam tekrar birden fazla egzersizi kapsamalı."""
        self.counter.update("squat",  {"left_knee": 85,  "right_knee": 85})
        self.counter.update("squat",  {"left_knee": 165, "right_knee": 165})
        self.counter.update("pushup", {"left_elbow": 80,  "right_elbow": 80})
        self.counter.update("pushup", {"left_elbow": 160, "right_elbow": 160})
        self.assertEqual(self.counter.get_total_reps(), 2)


if __name__ == "__main__":
    unittest.main()
