import string, random

"""An invertible function from the set of uppercase letters to itself"""
class Perm:
    def __init__(self, cycle=""):
        """cycle should be an uppercase string with no repeated letters"""
        self.map = {a:a for a in string.ascii_uppercase}

        for i in range(len(cycle)):
            a = cycle[i - len(cycle)]
            assert cycle.count(a) == 1
            b = cycle[i - len(cycle) + 1]
            self.map[a] = b

    @classmethod
    def from_map(cls, mmap: dict):
        """Create a permutation more directly by providing a dictionary map"""
        p = cls()
        p.map = mmap
        return p

    @classmethod
    def random(cls):
        """Generate a pseudorandom permutation"""
        shuffled = [a for a in string.ascii_uppercase]
        random.shuffle(shuffled)
        return cls.from_map({a: shuffled[string.ascii_uppercase.index(a)] for a in string.ascii_uppercase})

    def disjoint_cycle_decomposition(self):
        """Get a list of lists which is the disjoint cycle decomposition"""
        output = []

        done = []
        for a in string.ascii_uppercase:
            if a not in done:
                out = []
                out.append(a)
                b = self(a)
                while b != a:
                    done.append(b)
                    out.append(b)
                    b = self(b)
                done.append(a)
                output.append(out)

        return output

    def invert(self):
        """Create the inverse of a permutation"""
        return Perm.from_map({self(a): a for a in string.ascii_uppercase})
    
    def __str__(self):
        """Convert to disjoint cycle decomposition string"""
        dcd_strs = []
        for cycle in self.disjoint_cycle_decomposition():
            dcd_strs.append("".join(cycle))
        return "(" + ")(".join(dcd_strs) + ")"

    def __call__(self, char: str):
        """Use the function"""
        return self.map[char]

    def __mul__(self, perm):
        """Compose permutation with another"""
        return Perm.from_map({a:self(perm(a)) for a in string.ascii_uppercase})


def auto_perm_encipher(sigma: Perm, tau: Perm, plaintext: str):
    assert plaintext.isupper()
    if len(plaintext) % 2 == 1:
        plaintext += "X"

    ciphertext = ""

    for i in range(len(plaintext) // 2):
        a = plaintext[2*i]
        b = plaintext[2*i + 1]

        ciphertext += sigma(a) + tau(b)

        if a != b:
            transposition = Perm(a + b)
            sigma = sigma * transposition
            tau = tau * transposition

    return ciphertext


def auto_perm_decipher(sigma: Perm, tau: Perm, ciphertext: str):
    assert ciphertext.isupper()
    assert len(ciphertext) % 2 == 0

    plaintext = ""
    sigma_inverse = sigma.invert()
    tau_inverse = tau.invert()

    for i in range(len(ciphertext) // 2):
        a = ciphertext[2*i]
        b = ciphertext[2*i + 1]

        a_plain = sigma_inverse(a)
        b_plain = tau_inverse(b)

        plaintext += a_plain + b_plain

        if a_plain != b_plain:
            transposition = Perm(a_plain + b_plain)
            sigma_inverse = transposition * sigma_inverse
            tau_inverse = transposition * tau_inverse

    return plaintext
        

if __name__ == "__main__":
    plaintext = ""

    # Get plaintext from plain.txt
    with open("plain.txt") as f:
        text = f.read()
        plaintext = text.upper()
        plaintext = "".join(((a if a in string.ascii_uppercase else "") for a in plaintext))

    print("Plaintext read from file 'plain.txt'.")
    
    print("Generating random keys...")
    # Generate random permutation for initial sigma, tau
    sigma = Perm.random()
    tau = Perm.random()

    print("sigma =", sigma)
    print("tau =", tau)

    print("Enciphering...")
    # Encipher plaintext using random permutations
    ciphertext = auto_perm_encipher(sigma, tau, plaintext)

    # Put ciphertext into cipher.txt
    with open("cipher.txt", "w") as f:
        output = ""
        for i in range(0, len(ciphertext), 5):
            output += ciphertext[i:i+5] + " "
        
        f.write(output[:-1])

    print("Ciphertext written to 'cipher.txt'")
