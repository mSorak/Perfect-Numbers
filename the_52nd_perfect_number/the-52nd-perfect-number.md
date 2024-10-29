# The 52nd Perfect Number

## Wake up babe! New Prime Number just dropped

On October 12th 2024, a former Nvidia engineer named Luke Durant working with the [Great Internet Mersenne Prime Search or GIMPS](https://www.mersenne.org/) discovered a number which takes the title of the largest prime number known to man. After checking to make sure their result was accurate for about 2 weeks, a public announcement was made on October 21st. For reasons I'll explain in a second, this discovery also meant that there's a new largest known perfect number. I don't normally plan on talking about math that much, but I saw the announcement no more than an hour after deciding on the name for this blog, so I honestly feel it'd be a disservice to myself to not talk about it a little. So let's do it. We'll talk a little bit about the math and then once I've thoroughly bored you we'll move on to some hopefully more interesting stuff about the growth in the largest primes known.

Subscribe

## Mersenne Primes and Perfect Numbers

Okay, I really hope everyone reading this knows this, but just in case here's the definition of a prime number from [Wikipedia](https://en.wikipedia.org/wiki/Prime_number): A prime number is a natural number (positive integer) greater than 1 that is not a product of two smaller natural numbers. A _Mersenne_ prime is a special kind of prime which takes the form: 

\\(2^p-1\\)

or- in English- is one less than a power of 2. For example, 7 is a Mersenne prime because 

\\(2^3-1=7\\)

and 7 has no combination of natural numbers other than 7 times 1 for which it is the product. In the age of computers being way better at math than us monkeys, most of the largest primes found have been Mersenne because their primality is easy to check with computers.

Now why we're really talking about Mersenne Primes is because they share a close connection to perfect numbers. Here's a refresher on perfect numbers: 

> Originally defined by Euclid in _[Elements](http://aleph0.clarku.edu/~djoyce/elements/bookVII/defVII22.html)_[ (VII.22)](http://aleph0.clarku.edu/~djoyce/elements/bookVII/defVII22.html), _“A perfect number is that which is equal to the sum of its own parts.”_
> 
> That is, perfect numbers are numbers whose proper divisors (divisors not including the number itself) sum to the number itself _._

All known perfect numbers are related to a corresponding Mersenne prime by the [Euclid-Euler theorem](https://en.wikipedia.org/wiki/Euclid%E2%80%93Euler_theorem#:~:text=The%20Euclid%E2%80%93Euler%20theorem%20is,1%20is%20a%20prime%20number.) which states that an _even_ number is perfect if and only if it has the form 

\\(\text{Perfect Number}=2^{p-1}(2^{p}-1)\\)

where _2 p-1_ is a prime number- a Mersenne Prime! As of today, all known perfect numbers are even and thus have a Mersenne Prime friend, but it remains unproven whether or not there are any odd perfects. Now most mathematicians believe that no odd perfects exist but I personally am hanging on to hope due to the _Sorak Wouldn't it be so damn fun Conjecture_.

## The New Prime and the New Perfect

Okay, now lets talk a little bit about the new prime that was discovered. Just as a PSA, if you aren't someone who routinely thinks about very large numbers (which I find very unrelatable) the numbers we're about to discuss will seem mind-bendingly huge. That's because they are. They are so big as to render them impossible to conceptualize. Just please don't have an existential crisis, it's bad for readership. 

So here's the prime, written using its Mersenne Prime form:

\\(2^{136,279,841}-1\\)

I will not be inserting the actual number as it is _41,024,320 digits_ long, which Substack informs me is to long to put on their servers (a compressed text file of the full number is 22 Megabytes).[1](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-1-150858800) To throw out the classic comparison for large numbers, the number of atoms in the observable universe is roughly 1080, which is... 80 digits long. This number is **stupid** big. It is just not possible to express the size of this numbers in real-world terms in any meaningful way. The previous record holder for the largest known prime is similarly huge. Though relatively it’s tiny, only having _24,862,048_ digits- amateur stuff really. Oh and the new perfect number is 

\\(2^{136,279,840}(2^{136,279,841}-1)\\)

which has exactly double the number of digits as its Mersenne Prime friend: _82,048,640_. Again, that's digits!

Okay let's move on, my head hurts.

## Largest Known Primes Over Time

Let’s look at a time-series plot of the largest known prime over the years by number of digits in the prime:

Growth was very slow for a long time. In 1588, the largest known prime was _524,287,_ a Mersenne Prime with exponent 19 _._ It wasn’t for close to 200 years that a new king prime was crowned- the next Mersenne with exponent 31. By the 20th century, the largest known prime only had 39 digits.

The growth in recent history is due to the increasing capability of computers. The last time a new biggest prime was found which wasn’t discovered by a computer was in 1951. Aimé Ferrier used [Proth’s theorem](https://en.wikipedia.org/wiki/Proth%27s_theorem) to discover that the following number is prime:

\\((2^{148}+1)/17 = 20,988,936,657,440,586,486,151,264,256,610,222,593,863,921\\)

Less than a year later, Mathematician Raphael Robinson was the first to create a computer usable primality test for Mersenne Primes. Throughout 1952, using a _[Standards Western Automatic Computer](https://en.wikipedia.org/wiki/SWAC_\(computer\)) _he checked the primality of all Mersenne numbers;

\\(2^p-1,p<2304\\)

finding a total of 17 primes- confirming the primality of the first 12 and discovering 5 new Mersenne Primes which each successively became the new largest known prime.

However, these early computer-discovered primes barely show an increase on the chart above- they’re drowned out by the behemeth’s of recent years. To really see visually the importance of these early computers we can employ a common technique for visualizing exponential growth: Act like a beaver and _take the log._ So now, roughly speaking we’re looking at the number of digits in the number of digits of the largest know prime over time.[2](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-2-150858800)

Looking at the early 1950s, its clear that the early computer-discovered primes really were a huge leap forward in human’s ability to compute big numbers- an ability which has only grown in the proceeding 70 years. 

### GIMPS and the Future of New Largest Primes

The Great Internet Mersenne Prime Search or GIMPS is a collaborative project for which anyone can sign up and use any downtime of their personal computer for searching for Mersenne Primes. GIMPS has been extremely successful. Since 1996, all 16 new largest primes discoveries has been by a computer collaborating with GIMPS and these discoveries have seen a massive increase in size over the years.

I love the idea that anyone can be part of discovering the next great prime. My computers have been enrolled in the search off and on since I heard about GIMPS, and despite my lack of success the idea still really excites me. But if I’m being honest this recent discovery is somewhat dispiriting for a couple reasons.

The first is how long the new prime took to find- about 6 years. This is the largest gap in biggest prime discoveries since the 1963-1971 period and by far the largest gap since the GIMPS project started.

The second is how this new prime was discovered. It was the first prime discovery on a GPU (Graphics Processing Unit **)** rather than a CPU (Central Processing Unit). GPUs, though initially designed for computations related to displaying graphics, have in recent years been used as more powerful processors for a variety of tasks.[3](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-3-150858800) So in some sense, the recent discovery is representative of a leap forward in the technologies we use for intense calculations. However, it also represents a different type of shift. The GPU it was discovered on was part of a huge distributed supercomputer setup dedicated for searching for Mersenne Primes created by Durant, which according to [his statements in an interview with the YouTube channel Numberphile](https://youtu.be/Yp4ilFOtoeg?t=433), cost “under $2 Million dollars” of his own money to run. Sure “under $2 million” could mean $10 with a free side of fries but I suspect the exact number he invested isn’t exactly replicable for most people. Suffice to say, I’ve given up on my dinky little laptop finding the next big prime.[4](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-4-150858800)

The gap in time and the huge investment required to find the new prime indicates to me that perhaps we’ve reached a threshold for calculations that the computing power accessible to an average person can no longer meet.

## Wrapping Up

Despite my poopooing the discovery, I am still very happy there’s a new largest prime and associated perfect number. I should note however, that this discovery isn’t really _important._ There was no new math involved in the discovery and finding new huge primes really isn’t useful for anything. [In the same Numberphile video](https://youtu.be/Yp4ilFOtoeg?t=518), the founder of GIMPS, George Woltman describes the reason for searching for new big primes as “Because it’s fun.” I agree, but your mileage may vary on whether you think this was the best use of “under $2 million.”

Just as final note, I was considering giving a goofy title to refer to the largest known prime seeing as I said some version of “largest known prime” about 35 times in this piece. I decided against but just for the hell of it- which of these is the better.[5](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-5-150858800)

[](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#poll-229189)


[1](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-anchor-1-150858800)

It starts with “ _881”_ , has 41,024,314 other digits, then ends in “ _551”_. 

[2](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-anchor-2-150858800)

This isn’t exactly what log10(digits) does. If you need a refresher on logarithms I think [this](https://www.snexplores.org/article/explainer-what-are-logarithms-exponents) is a pretty good explainer of what they are and why we use them in data visualization.

[3](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-anchor-3-150858800)

[Here’s a useful explainer ](https://www.splunk.com/en_us/blog/learn/cpu-vs-gpu.html)on more about CPUs and GPUs and why GPUs have started being used for than just graphic.

[4](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-anchor-4-150858800)

[Running GIMPS ](https://www.mersenne.org/gettingstarted/)on your machine is still worth it. There’s useful under the hood calculations the project can utilize your machine for.

[5](https://perfectnumbers.substack.com/p/the-52nd-perfect-number#footnote-anchor-5-150858800)

To give myself some credit- they’re both a hell a lot better than these hilariously horrible [suggestions from ChatGPT](https://chatgpt.com/share/672019b8-8fe0-800c-a60c-0738c889b248).
