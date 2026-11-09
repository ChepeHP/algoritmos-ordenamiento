import random
import unittest

from section1_comparison.activity3_experiment.experiment import count_operations, quicksort
from section2_animation.replay import (
    MAX_ELEMENTS,
    ORDERS,
    QuicksortReplay,
    decimal_comma_note,
    generate_values,
    parse_values,
)


def run_to_end(replay):
    while replay.step():
        pass


class ReplayTests(unittest.TestCase):
    def cases(self):
        rng = random.Random(7)
        yield [38, 27, 43, 3, 9, 82, 10]
        yield [5.5, -1.25, 5.5, 0, 3]
        yield [4, 4, 4, 4]
        yield [1, 2]
        for _ in range(100):
            yield [rng.randint(-9, 9) for _ in range(rng.randint(2, MAX_ELEMENTS))]

    def test_end_state_matches_the_real_algorithm(self):
        for data in self.cases():
            replay = QuicksortReplay(data)
            run_to_end(replay)
            direct = list(data)
            quicksort(direct)
            self.assertEqual(replay.values, direct)
            self.assertEqual(replay.sorted, set(range(len(data))))

    def test_counters_match_independent_measurement(self):
        for data in self.cases():
            replay = QuicksortReplay(data)
            run_to_end(replay)
            comparisons, swaps, _ = count_operations(quicksort, data)
            self.assertEqual(replay.comparisons, comparisons)
            self.assertEqual(replay.swaps, swaps)

    def test_tree_depth_matches_real_recursion_depth(self):
        for data in self.cases():
            replay = QuicksortReplay(data)
            _, _, depth = count_operations(quicksort, data)
            # Depth counts calls that returned at once; the tree only shows calls with work.
            self.assertGreaterEqual(depth, replay.max_depth + 1)
            self.assertLessEqual(depth, replay.max_depth + 2)

    def test_reset_returns_to_the_start_and_replays_identically(self):
        replay = QuicksortReplay([9, 3, 7, 1, 8, 2])
        run_to_end(replay)
        first = (list(replay.values), replay.comparisons, replay.swaps, len(replay.tree))
        replay.reset()
        self.assertEqual(replay.values, [9, 3, 7, 1, 8, 2])
        self.assertEqual((replay.position, replay.comparisons, replay.swaps), (0, 0, 0))
        self.assertEqual(replay.tree, [])
        run_to_end(replay)
        self.assertEqual((list(replay.values), replay.comparisons, replay.swaps, len(replay.tree)), first)

    def test_pivot_highlight_follows_the_pivot_value(self):
        for data in self.cases():
            replay = QuicksortReplay(data)
            while replay.step():
                if replay.pivot_position is not None:
                    self.assertEqual(replay.values[replay.pivot_position], replay.pivot_value)

    def test_seek_rebuilds_the_same_state_as_stepping_forward(self):
        data = [9, 3, 7, 1, 8, 2, 6, 6, 0]
        forward = QuicksortReplay(data)
        back = QuicksortReplay(data)
        run_to_end(back)
        for position in range(forward.total):
            back.seek(position)
            self.assertEqual(
                (back.values, back.comparisons, back.swaps, back.sorted, back.tree, back.active, back.narration),
                (forward.values, forward.comparisons, forward.swaps, forward.sorted, forward.tree, forward.active,
                 forward.narration),
            )
            forward.step()

    def test_step_past_the_end_returns_none(self):
        replay = QuicksortReplay([2, 1])
        run_to_end(replay)
        self.assertIsNone(replay.step())


class InputTests(unittest.TestCase):
    def test_accepts_ints_reals_and_negatives(self):
        self.assertEqual(parse_values("3, -1.5 2;7"), [3, -1.5, 2, 7])

    def test_rejects_bad_input_with_a_message(self):
        for text in ("1, x", "", "5", "nan, 1", "inf 2", "1e308, 1", " ".join(["1"] * (MAX_ELEMENTS + 1))):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_values(text)

    def test_decimal_comma_is_reported_and_a_spaced_list_is_not(self):
        self.assertEqual(parse_values("3,5"), [3, 5])
        self.assertIn("3,5", decimal_comma_note("3,5"))
        self.assertEqual(decimal_comma_note("3, 5 -1.5"), "")

    def test_generated_orders_have_the_requested_size_and_shape(self):
        rng = random.Random(0)
        for order in ORDERS:
            for kind in ("int", "real"):
                self.assertEqual(len(generate_values(12, order, kind, rng)), 12)
        rising = generate_values(12, "sorted", "int", rng)
        self.assertTrue(all(rising[i] <= rising[i + 1] for i in range(11)))
        falling = generate_values(12, "reversed", "real", rng)
        self.assertTrue(all(falling[i] >= falling[i + 1] for i in range(11)))
        self.assertTrue(any(v < 0 for v in generate_values(30, "negatives", "int", rng)))

    def test_adversarial_order_is_deeper_than_sorted(self):
        rng = random.Random(0)
        deep = QuicksortReplay(generate_values(30, "adversarial", "int", rng)).max_depth
        shallow = QuicksortReplay(generate_values(30, "sorted", "int", rng)).max_depth
        self.assertGreater(deep, 2 * shallow)


if __name__ == "__main__":
    unittest.main()
