# dp.py

import csv
import attr
import numpy as np

class BudgetDepletedError(Exception):
    pass

@attr.s
class Rating:
    """Movie rating."""
    user = attr.ib()
    movie = attr.ib()
    date = attr.ib()
    stars = attr.ib()

# Unsure what Rating this? It is a convenient alternative to namedtuple.

class DpQuerySession:
    """
    Respond to database queries with differential privacy.

    Args:
        db (str): Path to the ratings database csv-file.
        privacy_budget (float): Total differential privacy epsilon for the session.
    """

    def __init__(self, db, privacy_budget):
        self.db = db
        self.privacy_budget = privacy_budget
        self._queries = {}
        self._load_db()
        self._used_budget = 0

    def _load_db(self):
        """Load the rating database from a csv-file."""
        self._entries = []
        with open(self.db) as f:
            reader = csv.reader(f, quotechar='"', delimiter=",")
            for email, movie, date, stars in reader:
                self._entries.append(
                    Rating(user=email, movie=movie, date=date, stars=int(stars))
                )

    @property
    def remaining_budget(self):
        """
        Calculate the remaining privacy budget.

        Returns:
            float: The remaining privacy budget.
        """
        return self.privacy_budget - self._used_budget

    def get_count(self, movie_name, rating_threshold, epsilon):
        """
        Get the number of ratings where a given movie is rated at least as high as threshold.

        Args:
            movie_name (str): Movie name.
            rating_threshold (int): Rating threshold (number between 1 and 5).
            epsilon: Differential privacy epsilon to use for this query.

        Returns:
            float: The count with differentially private noise added.

        Raises:
            BudgetDepletedError: When query would exceed the total privacy budget.
        """
        # WARNING: Do not convert the response to positive integers. Leave as a
        # possibly negative float. This is a requirement for our verification.
        #
        # Question: Converting to a positive integer does not affect privacy. Why?

        if (movie_name, rating_threshold) not in self._queries:
            self._used_budget += epsilon

        if self.remaining_budget < 0:
            raise BudgetDepletedError()

        number_movie_rating = len(list(filter(lambda x: x.movie == movie_name and x.stars >= rating_threshold, self._entries)))

        if (movie_name, rating_threshold) in self._queries:
            noise = self._queries[(movie_name, rating_threshold)]
        else:
            noise = np.random.laplace(scale=1/epsilon)
            self._queries[(movie_name, rating_threshold)] = noise
        
        return number_movie_rating + noise
