import random, string

from util import gen_file, strip_gen


class Metric:
    """
    A decorator for a function which computes some measure for
    generated text
    """
    def __init__(self, measure):
        """
        measure should be a function which takes a generator and
        computes the metric, returning a number
        """
        self.measure = measure

    def __call__(self, text):
        """Call the actual function"""
        return self.measure(text)

    def random(self):
        """Compute the metric for 5000 randomly generated characters"""
        random_gen =(random.choice(string.ascii_uppercase) for i in range(5000))
        return self.measure(random_gen)

    def english(self):
        """Compute the metric for some english plaintext

        Namely the bee movie script.
        """
        with open("src/beemovie.txt") as f:
            return self.measure(strip_gen(gen_file(f)))


@Metric
def ioc(text, domain_size=26):
    """Compute the index of coincidence for some text

    Works for any alphabet, not just letters
    """
    # Maps letters to how many times they occur
    letters = {}
    # We need to find out how long the text is
    length = 0
    for letter in text:
        length += 1
        if letter in letters:
            letters[letter] += 1
        else:
            letters[letter] = 1

    # Form the actual IOC sum
    ioc_sum = 0
    for _, count in letters.items():
        ioc_sum += (count*(count-1)) / (length*(length-1))
    return ioc_sum * domain_size


LETTER_FREQUENCIES = {"A":0.08167, "B":0.01492, "C":0.02202, "D":0.04253,
                      "E":0.12702, "F":0.02228, "G":0.02015, "H":0.06094,
                      "I":0.06966, "J":0.00153, "K":0.01292, "L":0.04025,
                      "M":0.02406, "N":0.06749, "O":0.07507, "P":0.01929,
                      "Q":0.00095, "R":0.05987, "S":0.06327, "T":0.09356,
                      "U":0.02758, "V":0.00978, "W":0.02560, "X":0.00150,
                      "Y":0.01994, "Z":0.00077}

@Metric
def frequency_goodness_of_fit(text):
    """Compute the goodness of fit with expected English letter frequencies

    Only works for uppercase letters
    """
    letters = {}
    length = 0
    for letter in text:
        length += 1
        if letter in letters:
            letters[letter] += 1
        else:
            letters[letter] = 1

    gof_sum = 0

    for letter, count in letters.items():
        observed = count/length
        expected = LETTER_FREQUENCIES[letter]
        gof_score = (observed - expected)**2/expected
        gof_sum += gof_score

    return gof_sum


if __name__ == "__main__":
    print(ioc.random())
    print(ioc.english())
    print(frequency_goodness_of_fit.random())
    print(frequency_goodness_of_fit.english())
