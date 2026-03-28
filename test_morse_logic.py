"""Unit tests for morse_logic.py"""
import unittest
import os
import wave
import math
import morse_logic


class TestCalculateTimings(unittest.TestCase):
    def test_equal_speeds_no_farnsworth(self):
        """When eff >= char, no Farnsworth spacing is applied."""
        tu, _, char_g, word_g = morse_logic.calculate_timings(20, 20)
        self.assertAlmostEqual(tu, 1.2 / 20)
        self.assertAlmostEqual(char_g, tu * 3)
        self.assertAlmostEqual(word_g, tu * 7)

    def test_eff_greater_than_char(self):
        """When eff > char, should behave same as equal (no negative gaps)."""
        tu, _, char_g, word_g = morse_logic.calculate_timings(10, 15)
        self.assertAlmostEqual(char_g, tu * 3)
        self.assertAlmostEqual(word_g, tu * 7)

    def test_farnsworth_spacing(self):
        """When eff < char, gaps should be stretched."""
        tu, _, char_g, word_g = morse_logic.calculate_timings(20, 5)
        self.assertAlmostEqual(tu, 1.2 / 20)
        # Farnsworth gaps should be larger than standard
        self.assertGreater(char_g, tu * 3)
        self.assertGreater(word_g, tu * 7)

    def test_word_gap_greater_than_char_gap(self):
        """Word gap should always be larger than character gap."""
        for char_wpm in [5, 12, 25, 50]:
            for eff_wpm in [1, 3, 5, 10]:
                if eff_wpm <= char_wpm:
                    _, _, char_g, word_g = morse_logic.calculate_timings(char_wpm, eff_wpm)
                    self.assertGreater(word_g, char_g,
                        f"word_gap should > char_gap at char={char_wpm}, eff={eff_wpm}")

    def test_tu_is_positive(self):
        tu, _, _, _ = morse_logic.calculate_timings(12, 5)
        self.assertGreater(tu, 0)


class TestSanitizeText(unittest.TestCase):
    def test_basic_letters(self):
        text, ignored = morse_logic.sanitize_text("hello")
        self.assertEqual(text, "HELLO")
        self.assertEqual(ignored, set())

    def test_unsupported_chars(self):
        text, ignored = morse_logic.sanitize_text("hello~world")
        self.assertEqual(text, "HELLOWORLD")
        self.assertIn("~", ignored)

    def test_prosigns_preserved(self):
        text, ignored = morse_logic.sanitize_text("CQ <BT> CQ")
        self.assertIn("<BT>", text)
        self.assertEqual(ignored, set())

    def test_spaces(self):
        text, _ = morse_logic.sanitize_text("A B C")
        self.assertEqual(text, "A B C")

    def test_empty_string(self):
        text, ignored = morse_logic.sanitize_text("")
        self.assertEqual(text, "")
        self.assertEqual(ignored, set())

    def test_numbers_and_punctuation(self):
        text, ignored = morse_logic.sanitize_text("73 de K1ABC.")
        self.assertEqual(ignored, set())
        self.assertIn("73", text)
        self.assertIn(".", text)


class TestGenerateRandomText(unittest.TestCase):
    def test_default_produces_groups(self):
        text = morse_logic.generate_random_text(5, "mixed")
        groups = text.split()
        self.assertEqual(len(groups), 5)
        for g in groups:
            self.assertEqual(len(g), 5)

    def test_letters_only(self):
        text = morse_logic.generate_random_text(3, "letters")
        clean = text.replace(" ", "")
        self.assertTrue(clean.isalpha())

    def test_numbers_only(self):
        text = morse_logic.generate_random_text(3, "numbers")
        clean = text.replace(" ", "")
        self.assertTrue(clean.isdigit())

    def test_koch_respects_level(self):
        text = morse_logic.generate_random_text(10, "koch", 2)
        clean = text.replace(" ", "")
        allowed = set(morse_logic.KOCH_SEQUENCE[:2])
        for char in clean:
            self.assertIn(char, allowed,
                f"'{char}' not in Koch level 2 pool: {allowed}")

    def test_koch_level_clamped_to_min_2(self):
        text = morse_logic.generate_random_text(1, "koch", 1)
        clean = text.replace(" ", "")
        allowed = set(morse_logic.KOCH_SEQUENCE[:2])
        for char in clean:
            self.assertIn(char, allowed)

    def test_count_zero(self):
        text = morse_logic.generate_random_text(0, "mixed")
        self.assertEqual(text, "")


class TestGetVisualMorse(unittest.TestCase):
    def test_sos(self):
        visual = morse_logic.get_visual_morse("SOS")
        self.assertIn("...", visual)
        self.assertIn("---", visual)

    def test_prosign(self):
        visual = morse_logic.get_visual_morse("<SOS>")
        self.assertIn("...---...", visual)

    def test_empty(self):
        visual = morse_logic.get_visual_morse("")
        self.assertEqual(visual, "")


class TestGenerateMorseWav(unittest.TestCase):
    def setUp(self):
        self.tu, _, self.char_g, self.word_g = morse_logic.calculate_timings(20, 20)

    def test_produces_valid_wav(self):
        path = morse_logic.generate_morse_wav("E", self.tu, self.char_g, self.word_g)
        try:
            self.assertTrue(os.path.exists(path))
            with wave.open(path, 'rb') as w:
                self.assertEqual(w.getnchannels(), 1)
                self.assertEqual(w.getsampwidth(), 2)
                self.assertEqual(w.getframerate(), 22050)
                self.assertGreater(w.getnframes(), 0)
        finally:
            os.remove(path)

    def test_longer_text_produces_larger_file(self):
        path_short = morse_logic.generate_morse_wav("E", self.tu, self.char_g, self.word_g)
        path_long = morse_logic.generate_morse_wav("HELLO WORLD", self.tu, self.char_g, self.word_g)
        try:
            self.assertGreater(os.path.getsize(path_long), os.path.getsize(path_short))
        finally:
            os.remove(path_short)
            os.remove(path_long)

    def test_frequency_clamping(self):
        # Should not raise even with out-of-range frequency
        path = morse_logic.generate_morse_wav("E", self.tu, self.char_g, self.word_g, 50.0)
        try:
            self.assertTrue(os.path.exists(path))
        finally:
            os.remove(path)

    def test_prosign_in_wav(self):
        path = morse_logic.generate_morse_wav("<SOS>", self.tu, self.char_g, self.word_g)
        try:
            self.assertTrue(os.path.exists(path))
            with wave.open(path, 'rb') as w:
                self.assertGreater(w.getnframes(), 0)
        finally:
            os.remove(path)


class TestCombineWavs(unittest.TestCase):
    def test_combine_two_wavs(self):
        tu, _, cg, wg = morse_logic.calculate_timings(20, 20)
        wav1 = morse_logic.generate_morse_wav("E", tu, cg, wg)
        wav2 = morse_logic.generate_morse_wav("T", tu, cg, wg)
        combined = None
        try:
            combined = morse_logic.combine_wavs([wav1, wav2])
            self.assertIsNotNone(combined)
            with wave.open(combined, 'rb') as w:
                self.assertGreater(w.getnframes(), 0)
        finally:
            for f in filter(None, [wav1, wav2, combined]):
                if os.path.exists(f):
                    os.remove(f)

    def test_combine_empty_list(self):
        result = morse_logic.combine_wavs([])
        self.assertIsNone(result)

    def test_combine_with_none_entries(self):
        tu, _, cg, wg = morse_logic.calculate_timings(20, 20)
        wav1 = morse_logic.generate_morse_wav("E", tu, cg, wg)
        combined = None
        try:
            combined = morse_logic.combine_wavs([None, wav1, None])
            self.assertIsNotNone(combined)
        finally:
            for f in filter(None, [wav1, combined]):
                if os.path.exists(f):
                    os.remove(f)


class TestMorseCodeDict(unittest.TestCase):
    def test_all_letters_present(self):
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.assertIn(c, morse_logic.MORSE_CODE)

    def test_all_digits_present(self):
        for c in "0123456789":
            self.assertIn(c, morse_logic.MORSE_CODE)

    def test_space_is_slash(self):
        self.assertEqual(morse_logic.MORSE_CODE[' '], '/')

    def test_koch_sequence_chars_all_in_morse_code(self):
        for c in morse_logic.KOCH_SEQUENCE:
            self.assertIn(c, morse_logic.MORSE_CODE,
                f"Koch char '{c}' missing from MORSE_CODE dict")


class TestKochSequence(unittest.TestCase):
    def test_length(self):
        self.assertEqual(len(morse_logic.KOCH_SEQUENCE), 38)

    def test_starts_with_km(self):
        self.assertEqual(morse_logic.KOCH_SEQUENCE[:2], "KM")

    def test_no_duplicates(self):
        self.assertEqual(len(morse_logic.KOCH_SEQUENCE), len(set(morse_logic.KOCH_SEQUENCE)))


if __name__ == "__main__":
    unittest.main()
