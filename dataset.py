from collections import defaultdict
from collections import Counter
from entropy_counter import EntropyCounter
from itertools import groupby

class Dataset():
    def __init__(self, points=[]):
        self.points = points

    def entropy_of(self, attribute):
        entropies = defaultdict(EntropyCounter)
        for point in self.points:
            entropies[point.get(attribute)].record(point.outcome())
        return sum(counter.entropy() for counter in entropies.values())

    def best_attribute(self, attributes=None):
        if attributes is None: attributes = self.attributes()
        return min(attributes, key=self.entropy_of)

    def most_common_outcomes(self, n):
        return Counter(p.outcome() for p in self.points).most_common(n)

    def most_common_outcome(self):
        return self.most_common_outcomes(1)[0][0]

    def split_on(self, attribute):
        return { value: self.__class__(list(points)) for value, points in groupby(self.points, key=lambda p: p.get(attribute)) }

    def attributes(self):
        return self.points[0].attributes() if self.points else []

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
            self.assertEqual(dataset.best_attribute(), 1)
            self.assertEqual(dataset.best_attribute([0]), 0)
            self.assertEqual(dataset.best_attribute([0, 1]), 1)
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
    unittest.main()
