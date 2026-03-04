#!/usr/bin/env python3

import random

alphas_lower = frozenset('abcdefghijklmnopqrstuvwxyz')
alphas_upper = frozenset(l.upper() for l in alphas_lower)
digits = frozenset('0123456789')

all_chars = alphas_lower | alphas_upper | digits

print(len(all_chars))

#  a b c d e f g h i j k l m n o p q r s t u v w x y z
#  A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
#  0 1 2 3 4 5 6 7 8 9
print(*sorted(alphas_lower))
print(*sorted(alphas_upper))
print(*sorted(digits))

confusable = frozenset('0OQ 1l 5S 8B')
decenders = frozenset('Qgjpqy')

safe_chars = all_chars - confusable - decenders
print(len(safe_chars))
print(*sorted(safe_chars))


char_by_index = sorted(safe_chars)

seed = 3
rand = random.Random()
rand.seed(seed)
rand.shuffle(char_by_index)

char_by_index = tuple(char_by_index)
print(*char_by_index)

def encode_number(number):
    chars = list()
    while True:
        chars.append(char_by_index[number % len(char_by_index)])
        number //= len(char_by_index)
        if number == 0: break

    chars.reverse()
    return ''.join(chars)

for i in range(2 * len(char_by_index)):
    print(f'{i}: {encode_number(i)}')

print(f'0: {encode_number(0)}')
print(f'1: {encode_number(1)}')
print(f'23: {encode_number(23)}')
print(f'23: {encode_number(23)}')
print(f'100: {encode_number(100)}')
print(f'2**37: {encode_number(2**37)}')
print(f'2**37 - 1: {encode_number(2**37 - 1)}')

import random

# Create a Random instance
rng = random.Random()

# Set the seed
rng.seed(42)

# Generate random numbers
print(rng.randint(1, 10))  # Output will be the same every time
print(rng.random())        # Output will be the same every time
foo = list(range(25))
rng.shuffle(foo)
print('foo:', *foo)
