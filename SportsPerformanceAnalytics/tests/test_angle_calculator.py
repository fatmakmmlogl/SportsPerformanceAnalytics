"""
Unit testler: AngleCalculator
"""

import unittest
from models.angle_calculator import AngleCalculator


class TestAngleCalculator(unittest.TestCase):

    def setUp(self):
        self.calc = AngleCalculator()

    def test_right_angle(self):
        """90 derece açı doğru hesaplanmalı."""
        a = (0, 0)
        b = (0, 1)   # köşe
        c = (1, 1)
        angle = self.calc.calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 90.0, places=1)

    def test_straight_angle(self):
        """180 derece düz çizgi."""
        a = (0, 0)
        b = (1, 0)
        c = (2, 0)
        angle = self.calc.calculate_angle(a, b, c)
        self.assertAlmostEqual(angle, 180.0, places=1)

    def test_zero_length_vector(self):
        """Sıfır uzunluklu vektör 0 döndürmeli."""
        a = b = c = (1, 1)
        angle = self.calc.calculate_angle(a, b, c)
        self.assertEqual(angle, 0.0)

    def test_symmetry_score_perfect(self):
        """Eşit açılar mükemmel simetri (100) vermeli."""
        score = AngleCalculator.symmetry_score(90.0, 90.0)
        self.assertEqual(score, 100.0)

    def test_symmetry_score_penalty(self):
        """30 derece fark 0 simetri skoru vermeli."""
        score = AngleCalculator.symmetry_score(60.0, 90.0)
        self.assertEqual(score, 0.0)

    def test_angle_in_range(self):
        self.assertTrue(AngleCalculator.angle_in_range(90, 70, 110))
        self.assertFalse(AngleCalculator.angle_in_range(60, 70, 110))


if __name__ == "__main__":
    unittest.main()
