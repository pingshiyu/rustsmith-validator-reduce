import matplotlib.pyplot as plt

class Enum:
    def __init__(self, value: str):
        self.value = value

def summarize_dict(data: dict) -> dict:
    summary = {}
    all_integers = []
    for file, numbers in data.items():
        integers = [x[0] for x in numbers]
        all_integers.extend(integers)

    plt.hist(all_integers)
    plt.title("All files")
    plt.show()

data = {
    "file1.txt": [
        (1, Enum("enum1")),
        (2, Enum("enum2")),
        (3, Enum("enum3")),
    ],
    "file2.txt": [
        (4, Enum("enum1")),
        (5, Enum("enum2")),
        (6, Enum("enum3")),
    ],
}

summarize_dict(data)