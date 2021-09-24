- [Exercise 1: [attack] What are Donald's Favourite Movies?](#exercise-1-attack-what-are-donalds-favourite-movies)
- [Exercise 2: [defense] Differentially Private Queries](#exercise-2-defense-differentially-private-queries)

# Exercise 1: [attack] What are Donald's Favourite Movies?

As established in the handout, our goal is to partially de-anonymize a database, to gain information on data that would be otherwise hard to access. In order to do this, we will use information disclosed in a publicly available database.
Consequently, we won't need to compute any hash here, but rather just match hashes with plaintexts based on the data we can gather from the IMDb database.

## 1.1: Difficulty level: easy

In this case, the IMDb dataset is a subset of our anonimized one. Given this configuration, a possible attack could consist of the following steps: 

1. Start off by finding all the dates for which the victim has posted one or more reviews in the public database. 
2. Subsequently, use this information, along with the rating given, to retrieve the hash from the anonymized database.
3. Finally, use the dates and stars of the reviews for the victim's movies to retrieve the plaintext values of the movies from the public database.

This method works, and is fairly efficient. However, we can observe that, since the databases are not too big, it would not be too expensive to simply compute a cross-product between the entries of the anonymous and public database. This gives us an interesting opportunity, as we would be able to store, for all matching dates and ratings:
1. All the users' hashes for a given user plaintext
2. All the plaintext movie names for a given movie hash 

Once this is done, our first step would be to guess our victim's hash: as the public database is not correctly anonymized, we will simply be able to get it as the most frequent one in our hashes list for the known plaintext. 
At this point, we are almost done: we can retrieve the hashes of all the movies that our victim has reviewed in the anonymous database, and use the same method (just, from hash to plaintext this time) to retrieve the plaintexts for all the movies.

This method is also very versatile, as, once the table is ready, we would be able to easily retrieve the movies watched by any other user with little computation needed.

## 1.2: Difficulty level: normal

Now that the dates of the reviews vary between the two databases, there is no way for us to create that same beautiful table we had before, and the cross-product is useless. However, as we can read from the handout, there is a spark of hope: the frequency at which the movies appear in the anonymized and public databases is the same. Ultimately, this makes our job very easy.

The first thing we need to do to mount our frequency attack, is to sort the databases' movies (in one case the plaintext, in the other the hash) by their frequency: this way, at each index we will have a match between a hash and its corresponding plaintext. We can therefore store our mapping in a dictionary, so that we can retrieve a movie title from its hash in a very short time.

If we had the hash of our victim's email, the job would be done: we could just gather his movies from the anonymized db and use our table to get the equivalent plaintext. However, this is not the case: as a consequence, we will store all of the reviewed films for each user, then find out which of the movie lists belongs to the victim.

Once again, this is made possible by the public database leaking a lot of information: as we will see, if we store in a set the hashes of all the movies reviewed by our victim in the public database, we can then notice that this is a subset only for a single one of the sets of movies reviewed a user in the anonymized database. As a consequence, we can easily infer that the only user that reviewed all the same movies as the victim (plus some more) is the victim himself. At this point, all we need to do is to use the table we built at the very beginning to retrieve the plaintexts for the missing movies.

## 1.3: Difficulty level: hard

As you will know from the handout, this exercise is not compulsory. However, if you are into challenges and love the satisfaction of beating a game in hard mode, get on board!

Here the situation is very complicated. Not only the reviews are posted in different dates, but the frequency cannot help us anymore. The only information we have available is that the same reviews are posted in "close" dates on the two dbs, with a 14 days limit. In addition, we know that the probability distribution varies with the distance from the day the review was posted.

As a consequence of the data we have at our disposal, it will be very complicated here to get all the information right. Instead, we will try and guess the movies by using a convolution.

### The convolution method

In order to figure out the probability distribution around a series of `interesting_dates`, a convolution operation is applied. To do this, at first dates are transformed through [One Hot Encoding](https://en.wikipedia.org/wiki/One-hot). Then, a probability is calculated for each day, through a convolution with a kernel based on the given probability distribution. 
Subsequently, we can calculate the score for an `item` as the dot product between our convolution and the one hot encoding of the dates at which the item occurs.

Sounds confusing, right? Well, it kind of is. But here is an example to, hopefully, clear things up.

Our first goal is to find the most likely hash for the victim's email address. As a consequence, our `interesting_dates` are going to be those where said user has posted a review in the public database. By applying a convolution between the OHE of those dates and our kernel, we can obtain a probability distribution: the values will be 0 in dates very far from the user's reviews, and get higher and higher as the 14-days radius is entered.

At this point, we are ready to calculate the scores of our `items`, which in this case are hashes of the users: by one hot encoding the dates at which said hashes occur, and calculating a dot product with the convolution obtained before, we can compute a score that will grow with the correlation between those two.

Indeed, this does not give us absolute certainty that we will retrieve the correct values.

### Building our predictions

Once we have predicted the user's hash through convolution, we can easily use the same method to try and guess the movies they reviewed. This time, for each movie, the `interesting_dates` are going to be those at which the movie was reviewed in the anon database, while the `items` are going to be the plaintexts, associated with the review dates in the public database.

Indeed, with the given database our method works once again, yielding us both the correct hash for the user and a matching set of movies!

# Exercise 2: [defense] Differentially Private Queries

In this exercise, we are simply asked to use the Laplace mechanism in modulate the responses we give out to some researchers, concerning, once again, movies.
As you learnt from the lecture, replying truthfully to all queries would indeed be a problem, as this would disclose information regarding individual users: this goes beyond the purpoose of research, and it is what we want to avoid.

In order to do this, we define a privacy budget, which is separate for each researcher: for each query, an epsilon value can be specified, and the higher it is, the higher the accuracy of the response will be. As a consequence, a higher epsilon will drain the budget more, and vice versa, a lower epsilon will allow for more queries. 

## The implementation

In the exercise, you are mostly asked to implement the `get_count()` function. This is what the function should do, at a very high level:

* If the query has already been posted, just return the previous result
* In case of a new query, return the differentially private result if the epsilon is compatible with the budget, raise an exception otherwise

Going deep into the implementation, we define a dictionary for `cached_responses` and a `spent_budget` variable in the initialization function.

The `remaining_budget()` function can then simply be implemented as 
```python
return self._privacy_budget` - `self.spent_budget
```

This leaves us with the `get_count()` function. The idea, here, is to start by checking the dictionary, where we store `movie_name` and `rating_threshold` as keys, and the result as value: if the posted ones are already in the dict, we can simply return them. Of course, it would not make sense to deplete privacy budget for a query that has already been asked, so we do not need to update any other parameter.
Once this fast check is done, we get to the heart of the function: if `epsilon < remaining_budget`, we raise a `BudgetDepletedError`. Otherwise, we procede with the computation of the reply.

First of all, we need to compute the real data, without any noise added. To do this, it is enough to iterate through `self._entries`, which has already been kindly provided to you, and increase a counter for each of the entries that are selected by the query. This will therefore return the real number of entries that respect the conditions given in the query.

Once this is out of the way, we add a Laplace noise as defined in the theory: to do this, we can use the function `np.random.laplace(loc=0, scale=1. / epsilon)`.

At this point, all that is left to do is to cache the response, update our budget (`spent_budget += epsilon`) and return the noisy result.
