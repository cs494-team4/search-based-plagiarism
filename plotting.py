import os
import matplotlib.pyplot as plt

if __name__ == '__main__':
    min_scores = []
    min_lengths = []
    avg_scores = []
    avg_lengths = []
    std_scores = []
    std_lengths = []
    gen = []

    with open('pycode_pycode_sim.txt', 'r') as f:
        generations = f.readlines()[1:]

        for line in generations:
            line = line.replace('[', '')
            line = line.replace(']', '')
            line = line.split()
            print(line)
            gen.append(int(line[0]))
            min_scores.append(float(line[4]))
            min_lengths.append(float(line[5]))
            avg_scores.append(float(line[6]))
            avg_lengths.append(float(line[7]))
            std_scores.append(float(line[2]))
            std_lengths.append(float(line[3]))

        print(min_scores)
        print(min_lengths)

    fig, ax1 = plt.subplots()
    line1 = ax1.errorbar(gen, avg_scores, std_scores,
                         color='r', ecolor='lightgray', elinewidth=1, capsize=0, label="Average Scores")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Score", color="b")
    for tl in ax1.get_yticklabels():
        tl.set_color("b")

    ax2 = ax1.twinx()
    line2 = ax2.errorbar(gen, avg_lengths, std_lengths,
                         color='b', ecolor='lightblue', elinewidth=1, capsize=0, label="Average Sequence Lengths")
    ax2.set_ylabel("Length", color="r")
    for tl in ax2.get_yticklabels():
        tl.set_color("r")

    lns = line1 + line2
    labs = [line1.get_label(), line2.get_label()]
    ax1.legend([line1, line2], labs, loc="upper center")

    plt.show()
