from collections import defaultdict
from collections import Counter
from outcome_counter import OutcomeCounter
import random
import numpy

class SingleAttributeSplitter():
    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

class GreaterThanOrEqualToSplitter(SingleAttributeSplitter):
    def split(self, x):
      return x[self.attribute] >= self.value

    def __str__(self):
      return "x[{0}] >= {1}".format(self.attribute, self.value)

class IsEqualSplitter(SingleAttributeSplitter):
    def split(self, x):
      return x[self.attribute] == self.value

    def __str__(self):
      return "x[{0}] == {1}".format(self.attribute, self.value)

class Dataset():
    def __init__(self, X, y=None, attribute_types=None):
        self.X = X
        self.y = y
        self.outcome_counter = OutcomeCounter(y)
        self.attribute_types = attribute_types
        if attribute_types is None:
            self.attribute_types = numpy.full(self.X.shape[1], 0)

        lx1, lx2 = self.X.shape
        if len(self.y) != lx1:
            raise ValueError("y ({0}) must have same length as X ({1})".format(len(y), lx1))
        if len(self.attribute_types) != lx2:
            raise ValueError("attribute_types ({0}) must have same length as X[i] ({1})".format(len(attribute_types), lx2))

    def is_numeric(self, attribute):
        return self.attribute_types[attribute]

    def __len__(self):
        return self.X.shape[0]

    def each_single_attribute_splitter(self):
        for attribute in range(self.X.shape[1]):
            values = self.X[:, attribute]
            if self.is_numeric(attribute):
                stddev, maximum, value = values.std(), values.max(), values.min()
                if maximum != value:
                    while value < maximum:
                        yield GreaterThanOrEqualToSplitter(attribute, value)
                        value += stddev / 10.0
            else:
                unique_values = numpy.unique(values)
                if len(unique_values) > 1:
                    for value in unique_values:
                        yield IsEqualSplitter(attribute, value)

    def best_single_attribute_splitter(self):
        try:
            return min(self.each_single_attribute_splitter(), key=self.splitter_entropy)
        except ValueError: # no splitters
            return None

    def splitter_entropy(self, splitter):
        splits = defaultdict(OutcomeCounter)
        for i in range(len(self)):
            splits[splitter.split(self.X[i])].record(self.y[i])
        return sum(s.weighted_entropy() for s in splits.values()) / float(len(self))

    def split_on(self, splitter):
        splits = defaultdict(list)
        for i in range(len(self)):
            splits[splitter.split(self.X[i])].append(i)
        return map(self.take, splits.values())

    def take(self, indices):
        return self.__class__(self.X.take(indices, 0), self.y.take(indices), self.attribute_types)

    def bootstrap(self, n=None):
        return self.take([random.randrange(len(self)) for _i in range(n or len(self))])

if __name__ == '__main__':
    import unittest

    class TestDataset(unittest.TestCase):
        def test_entropy(self):
            X = numpy.array([[0, 1], [0, 0]])
            y = numpy.array(['H', 'T'])
            dataset = Dataset(X, y, [0, 0])
            self.assertEqual(dataset.splitter_entropy(IsEqualSplitter(0, 0)), 1)
            self.assertEqual(dataset.splitter_entropy(IsEqualSplitter(0, 1)), 1)
            self.assertEqual(dataset.splitter_entropy(IsEqualSplitter(1, 0)), 0)
            self.assertEqual(dataset.splitter_entropy(IsEqualSplitter(1, 1)), 0)

            best_splitter = dataset.best_single_attribute_splitter()
            self.assertEqual(best_splitter.attribute, 1)
            self.assertEqual(best_splitter.value, 0)

        def test_split_on(self):
            X = numpy.array([[0, 1], [0, 0], [1, 0]])
            y = numpy.array(['H', 'T', 'T'])
            dataset = Dataset(X, y)
            split = dataset.split_on(IsEqualSplitter(1, 0))
            numpy.testing.assert_array_equal(split[0].X, numpy.array([[0, 1]]))
            numpy.testing.assert_array_equal(split[1].X, numpy.array([[0, 0], [1, 0]]))

        def test_multitype_splitting(self):
            # x1 < 0.5, x2 = 0 => 'Red'
            # x1 < 0.5, x2 = 1 => 'Yellow'
            # x1 >= .5 => 'Green'
            X = numpy.array([[0.25, 0], [0.33, 0], [0.31, 1], [0.12, 1], [0.45, 0], [0.52, 0], [0.81, 0], [0.67, 1], [0.51, 1]])
            y = numpy.array(['Red', 'Red', 'Yellow', 'Yellow', 'Red', 'Green', 'Green', 'Green', 'Green'])
            dataset = Dataset(X, y, [1, 0])
            splitter = dataset.best_single_attribute_splitter()
            self.assertEqual(splitter.attribute, 0)
            self.assertGreaterEqual(splitter.value, 0.45)
            self.assertLess(splitter.value, 0.52)

            subset1, subset2 = dataset.split_on(splitter)
            subsplitter = subset1.best_single_attribute_splitter()
            self.assertEqual(subsplitter.attribute, 1)
            self.assertEqual(subsplitter.value, 0)

        def test_more_complicated_splitting(self):
            # x1  < 0.25 => 'a'
            # x1 >= 0.25, x2 = 0 => 'b'
            # x1  < 0.50, x2 = 1 => 'c'
            # x1 >= 0.50, x2 = 1 => 'd'
            X = numpy.array([[0.2, 0], [0.01, 1], [0.15, 0], [0.232, 1], [0.173, 0], [0.263, 0], [0.671, 0], [0.9, 0], [0.387, 1], [0.482, 1], [0.632, 1], [0.892, 1]])
            y = numpy.array(['a', 'a', 'a', 'a', 'a', 'b', 'b', 'b', 'c', 'c', 'a', 'a'])
            dataset = Dataset(X, y, [1, 0])

            splitter = dataset.best_single_attribute_splitter()
            self.assertEqual(splitter.attribute, 0)
            self.assertGreaterEqual(splitter.value, 0.23)
            self.assertLess(splitter.value, 0.27)
            subset1, subset2 = dataset.split_on(splitter)
            numpy.testing.assert_array_equal(subset1.y, ['a', 'a', 'a', 'a', 'a'])

            splitter2 = subset2.best_single_attribute_splitter()
            self.assertEqual(splitter2.attribute, 1)
            self.assertEqual(splitter2.value, 0)
            subset21, subset22 = subset2.split_on(splitter2)
            numpy.testing.assert_array_equal(subset22.y, ['b', 'b', 'b'])

            splitter21 = subset21.best_single_attribute_splitter()
            self.assertEqual(splitter21.attribute, 0)
            self.assertGreaterEqual(splitter21.value, 0.482)
            self.assertLess(splitter21.value, 0.632)
            subset211, subset212 = subset21.split_on(splitter21)
            numpy.testing.assert_array_equal(subset211.y, ['c', 'c'])
            numpy.testing.assert_array_equal(subset212.y, ['a', 'a'])

        def test_outcomes(self):
            X = numpy.array([[0, 1], [0, 0], [1, 0]])
            y = numpy.array(['H', 'T', 'T'])
            dataset = Dataset(X, y)
            outcomes = dataset.outcome_counter
            self.assertEqual(outcomes.counter.most_common(), [('T', 2), ('H', 1)])

        def test_bootstrap(self):
            X = numpy.array([[0, 1], [0, 0]])
            y = numpy.array(['H', 'T'])
            dataset = Dataset(X, y)
            bootstrap = dataset.bootstrap(1000)
            self.assertEqual(bootstrap.X.shape[0], 1000)
            self.assertEqual('H' in bootstrap.y, True) # this has a 10e-302ish chance of failing

    unittest.main()
