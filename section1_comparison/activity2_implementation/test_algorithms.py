import random
import unittest
from collections import Counter

from section1_comparison.activity2_implementation.algorithms import (
    bubble_sort,
    median_of_three,
    quicksort,
)
from section1_comparison.activity3_experiment.experiment import (
    GENERATORS,
    count_operations,
    median_of_three_killer,
)

ALGORITHMS = {"bubble": bubble_sort, "quick": quicksort}
FIXED_CASES = {
    "integers": [5, 2, 9, 1, 7],
    "reals": [3.14, -0.5, 2.71, 0.0, 1.41],
    "ints and reals": [3, 1.5, -2, 2.25, 0],
    "repeated": [4, 1, 4, 2, 1, 4],
    "negatives": [-3, -1, -7, -2],
    "all equal": [7, 7, 7, 7],
    "sorted": [1, 2, 3, 4, 5],
    "reversed": [5, 4, 3, 2, 1],
    "empty": [],
    "one element": [42],
    "two elements": [2, 1],
    "large sorted": list(range(5000)),
    "large reversed": list(range(5000, 0, -1)),
    "large all equal": [1] * 5000,
}


def record_trace(data):
    work = list(data)
    events = []
    quicksort(work, trace=lambda *event: events.append(event))
    return work, events


class SortingTests(unittest.TestCase):
    def assert_sorts(self, algorithm, data):
        result = list(data)
        algorithm(result)
        self.assertTrue(all(result[i] <= result[i + 1] for i in range(len(result) - 1)))
        self.assertEqual(Counter(result), Counter(data))

    def test_fixed_cases(self):
        for name, algorithm in ALGORITHMS.items():
            for label, data in FIXED_CASES.items():
                with self.subTest(algorithm=name, case=label):
                    self.assert_sorts(algorithm, data)

    def test_random_mixed_lists(self):
        rng = random.Random(0)
        for name, algorithm in ALGORITHMS.items():
            for _ in range(500):
                size = rng.randint(0, 60)
                data = [rng.choice([rng.randint(-20, 20), rng.uniform(-20, 20)]) for _ in range(size)]
                with self.subTest(algorithm=name, data=data):
                    self.assert_sorts(algorithm, data)

    def test_no_builtin_sort_in_source(self):
        with open(bubble_sort.__code__.co_filename, encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("sorted(", source)
        self.assertNotIn(".sort(", source)


class MedianOfThreeTests(unittest.TestCase):
    def test_returns_the_median_for_every_order(self):
        for x, y, z in [(1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1),
                        (1, 1, 2), (1, 2, 1), (2, 1, 1), (5, 5, 5)]:
            with self.subTest(values=(x, y, z)):
                a = [x, y, z]
                chosen = a[median_of_three(a, 0, 2)]
                self.assertEqual(chosen, x + y + z - min(x, y, z) - max(x, y, z))

    def test_pivot_comes_from_lo_mid_hi(self):
        a = [9, 0, 0, 5, 0, 0, 1]
        self.assertEqual(median_of_three(a, 0, 6), 3)

    def test_sorted_and_reversed_inputs_split_in_half(self):
        for label, data in [("sorted", list(range(1023))), ("reversed", list(range(1023, 0, -1)))]:
            with self.subTest(case=label):
                _, _, depth = count_operations(quicksort, data)
                self.assertLessEqual(depth, 12)


class ExamFormulaTests(unittest.TestCase):
    """The formal analysis gives exact comparison counts for Bubble Sort."""

    def test_bubble_sorted_makes_n_minus_1_comparisons(self):
        for n in (10, 100, 1000):
            comparisons, swaps, _ = count_operations(bubble_sort, list(range(n)))
            self.assertEqual(comparisons, n - 1)
            self.assertEqual(swaps, 0)

    def test_bubble_reversed_makes_n_n_minus_1_over_2(self):
        for n in (10, 100, 1000):
            comparisons, swaps, _ = count_operations(bubble_sort, list(range(n, 0, -1)))
            self.assertEqual(comparisons, n * (n - 1) // 2)
            self.assertEqual(swaps, n * (n - 1) // 2)


class TraceFidelityTests(unittest.TestCase):
    """The animation replays this trace, so it must match what the algorithm really did."""

    def cases(self):
        rng = random.Random(1)
        yield [38, 27, 43, 3, 9, 82, 10]
        yield [5, 5, 5, 5, 5]
        yield [1, 2, 3, 4, 5, 6, 7, 8]
        yield [8, 7, 6, 5, 4, 3, 2, 1]
        yield []
        yield [1]
        for _ in range(200):
            yield [rng.randint(-9, 9) for _ in range(rng.randint(0, 40))]

    def test_replaying_swaps_reproduces_the_result(self):
        for data in self.cases():
            result, events = record_trace(data)
            replay = list(data)
            for event in events:
                if event[0] == "swap":
                    _, i, j = event
                    replay[i], replay[j] = replay[j], replay[i]
            self.assertEqual(replay, result)

    def test_trace_counts_match_independent_counters(self):
        for data in self.cases():
            _, events = record_trace(data)
            traced = sum(1 for e in events if e[0] in ("compare", "compare_median"))
            swaps = sum(1 for e in events if e[0] == "swap")
            comparisons, counted_swaps, _ = count_operations(quicksort, data)
            self.assertEqual(traced, comparisons)
            self.assertEqual(swaps, counted_swaps)

    def test_every_position_ends_marked_sorted_and_correct(self):
        for data in self.cases():
            result, events = record_trace(data)
            replay = list(data)
            final = set()
            for event in events:
                if event[0] == "swap":
                    _, i, j = event
                    replay[i], replay[j] = replay[j], replay[i]
                elif event[0] == "sorted":
                    _, first, last = event
                    for k in range(first, last + 1):
                        self.assertEqual(replay[k], result[k])
                        final.add(k)
            self.assertEqual(final, set(range(len(data))))

    def test_tracing_does_not_change_the_result(self):
        for data in self.cases():
            traced, _ = record_trace(data)
            plain = list(data)
            quicksort(plain)
            self.assertEqual(traced, plain)


class DatasetTests(unittest.TestCase):
    def test_every_generator_has_requested_size_and_sorts(self):
        rng = random.Random(3)
        for config, generate in GENERATORS.items():
            data = generate(200, rng)
            with self.subTest(config=config):
                self.assertEqual(len(data), 200)
                for algorithm in ALGORITHMS.values():
                    result = list(data)
                    algorithm(result)
                    self.assertTrue(all(result[i] <= result[i + 1] for i in range(199)))

    def test_adversary_forces_quadratic_comparisons(self):
        n = 1000
        data = list(median_of_three_killer(n))
        bad, _, bad_depth = count_operations(quicksort, data)
        rng = random.Random(4)
        good, _, good_depth = count_operations(quicksort, [rng.random() for _ in range(n)])
        self.assertGreater(bad, 10 * good)
        self.assertGreater(bad_depth, 10 * good_depth)


if __name__ == "__main__":
    unittest.main()
