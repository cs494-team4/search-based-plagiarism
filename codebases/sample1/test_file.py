test = [0, 1, 0, 2]


def cleanup(liste):
    sorted(liste, key=lambda x: 1 if x == 0 else 0)


cleanup(test)
print(test)
