from collections import defaultdict
from collections import Counter
from entropy_counter import EntropyCounter
import random

class Dataset():
    def __init__(self, points=[]):
        self.points = points

    def entropy_of(self, feature):
        entropies = defaultdict(EntropyCounter)
        for point in self.points:
            entropies[point.get(feature)].record(point.outcome())
        return sum(counter.entropy() for counter in entropies.values())

    def best_feature(self, features):
        return min(features, key=self.entropy_of)

    def most_common_outcomes(self, n=None):
        return Counter(point.outcome() for point in self.points).most_common(n)

    def most_common_outcome(self):
        return self.most_common_outcomes(1)[0][0]

    def is_unanimous(self):
        return len(self.most_common_outcomes()) == 1

    def split_on(self, feature):
        subsets = defaultdict(list)
        for point in self.points:
            subsets[point.get(feature)].append(point)
        return { value: self.__class__(points) for value, points in subsets.items() }

    def bootstrap(self, number_of_points=None):
        if number_of_points is None:
            number_of_points = len(self.points)
        return self.__class__([random.choice(self.points) for i in range(number_of_points)])

    def features(self):
        return self.points[0].features() if self.points else []

if __name__ == '__main__':
    import unittest
    from list_datapoint import ListDatapoint

    class TestDataset(unittest.TestCase):
        def test_entropy(self):
            point1 = ListDatapoint([0, 1, 'H'])
            point2 = ListDatapoint([0, 0, 'T'])
            dataset = Dataset([point1, point2])
            self.assertEqual(dataset.entropy_of(0), 1)
            self.assertEqual(dataset.entropy_of(1), 0)
            self.assertEqual(dataset.best_feature([0]), 0)
            self.assertEqual(dataset.best_feature([0, 1]), 1)

        def test_split_on(self):
            point1 = ListDatapoint([0, 1, 'H'])
            point2 = ListDatapoint([0, 0, 'T'])
            point3 = ListDatapoint([1, 0, 'T'])
            dataset = Dataset([point1, point2, point3])
            split = dataset.split_on(1)
            self.assertEqual(split.keys(), [0, 1])
            self.assertEqual(split[1].points, [point1])
            self.assertEqual(split[0].points, [point2, point3])

        def test_most_common_outcome(self):
            point1 = ListDatapoint([0, 1, 'H'])
            point2 = ListDatapoint([0, 0, 'T'])
            point3 = ListDatapoint([1, 0, 'T'])
            dataset = Dataset([point1, point2, point3])
            self.assertEqual(dataset.most_common_outcome(), 'T')

        def test_is_unanimous(self):
            point1 = ListDatapoint([0, 1, 'H'])
            point2 = ListDatapoint([0, 0, 'T'])
            point3 = ListDatapoint([1, 0, 'T'])
            unanimous_dataset = Dataset([point2, point3])
            disagreeing_dataset = Dataset([point1, point2, point3])
            self.assertEqual(unanimous_dataset.is_unanimous(), True)
            self.assertEqual(disagreeing_dataset.is_unanimous(), False)

        def test_bootstrap(self):
            point1 = ListDatapoint([0, 1, 'H'])
            point2 = ListDatapoint([0, 0, 'T'])
            dataset = Dataset([point1, point2])
            bootstrap = dataset.bootstrap(1000)
            self.assertEqual(len(bootstrap.points), 1000)
            self.assertEqual(point1 in bootstrap.points, True) # this has a 10e-302ish chance of failing

    unittest.main()
