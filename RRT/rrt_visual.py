import pandas as pd
import matplotlib.pyplot as plt


file = "rrt2d.txt"

def filter_points(file):
    # Read file
    points = pd.read_csv(
        file,
        sep=' ',
        header=None,
        names=["x", "y", "x_", "y_"]
    )
    return points


def plot_rrt_results(file):
    points = filter_points(file)

    for _, row in points.iterrows():
        # plot line from (x, y) to (x_, y_)
        plt.plot([row["x"], row["x_"]],
                 [row["y"], row["y_"]],
                 'r-')

    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("RRT 2D")
    plt.axis("equal")
    plt.show()


if __name__ == "__main__":
    plot_rrt_results(file)
