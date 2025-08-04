import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import trange, tqdm
# USING THE MNIST DATASET 

# --- Load and preprocess data ---
data = pd.read_csv("train.csv").to_numpy()
np.random.shuffle(data)

X = data[:, 1:].T / 255.0  # Normalize pixel values to [0,1]
Y = data[:, 0].astype(int)  # Extract labels

X_train, Y_train = X[:, 1000:], Y[1000:]
X_dev, Y_dev = X[:, :1000], Y[:1000]

# --- Activation functions and utilities ---
def relu(Z):
    return np.maximum(0, Z)

def maxpooling(Z, size=2, stride=2):
    n, m = Z.shape
    out_h = 1 + (n - size) // stride
    out_w = 1 + (m - size) // stride
    pooled = np.zeros((out_h, out_w))
    for i in range(out_h):
        for j in range(out_w):
            pooled[i, j] = np.max(Z[i*stride:i*stride+size, j*stride:j*stride+size])
    return pooled

def flattening(Z):
    return Z.flatten()

def softmax(x):
    x -= np.max(x, axis=0, keepdims=True)  # Numerical stability
    e_x = np.exp(x)
    return e_x / np.sum(e_x, axis=0, keepdims=True)

def cross_entropy_loss(Y_hat, Y):
    m = Y.shape[0]
    return -np.sum(np.log(Y_hat[Y, range(m)] + 1e-9)) / m  # Avoid log(0)

def accuracy(Y_hat, Y):
    return np.mean(np.argmax(Y_hat, axis=0) == Y)

# --- PID Optimizer ---
class PIDopt:
    def __init__(self, shape, Kp=0.1, Ki=0.001, Kd=0.01, beta_I=0.9):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.beta_I = beta_I
        self.I = np.zeros(shape)
        self.prev_gradient = np.zeros(shape)

    def step(self, param, grad):
        # Proportional
        P = grad

        # Integral (EMA of gradients)
        self.I = self.beta_I * self.I + (1 - self.beta_I) * grad
        I = self.I

        # Derivative
        D = grad - self.prev_gradient
        self.prev_gradient = grad

        # PID update
        update = self.Kp * P + self.Ki * I + self.Kd * D
        param -= update

# --- Model initialization and forward/backward ---
def init_model():
    return {
        "W": np.random.randn(10, 196) * 0.01,
        "b": np.zeros((10, 1))
    }

def fc_forward(X, params):
    return np.dot(params["W"], X) + params["b"]

def fc_backward(Y_hat, Y, X):
    m = Y.shape[0]
    dZ = Y_hat.copy()
    dZ[Y, range(m)] -= 1
    dZ /= m
    return {
        "dW": np.dot(dZ, X.T),
        "db": np.sum(dZ, axis=1, keepdims=True)
    }

# --- Training function with PID optimizer ---
def train(X_train, Y_train, X_dev, Y_dev, epochs=5, batch_size=32):
    params = init_model()
    opt_W = PIDopt(params["W"].shape)
    opt_b = PIDopt(params["b"].shape)
    m = X_train.shape[1]

    with open("results.csv", "w") as f:
        f.write("epoch,loss,accuracy\n")

    for epoch in trange(epochs, desc="Training epochs"):
        perm = np.random.permutation(m)
        X_epoch = X_train[:, perm]
        Y_epoch = Y_train[perm]

        for i in tqdm(range(0, m, batch_size), desc=f"Epoch {epoch+1}", leave=False):
            Xb = X_epoch[:, i:i+batch_size]
            Yb = Y_epoch[i:i+batch_size]
            bs = Xb.shape[1]

            # Forward pass for each image
            A = []
            for k in range(bs):
                img = Xb[:, k].reshape(28, 28)
                a1 = relu(img)
                a2 = maxpooling(a1, size=4, stride=4)  # Downsample to 7x7
                a3 = flattening(a2).reshape(-1, 1)     # 49x1
                A.append(a3)
            A = np.concatenate(A, axis=1)             # (49, bs)
            A_full = np.vstack([A] * 4)               # Expand to 196xbs

            Z = fc_forward(A_full, params)
            Y_hat = softmax(Z)

            loss = cross_entropy_loss(Y_hat, Yb)
            acc = accuracy(Y_hat, Yb)

            grads = fc_backward(Y_hat, Yb, A_full)
            opt_W.step(params["W"], grads["dW"])
            opt_b.step(params["b"], grads["db"])

        # Log training metrics
        with open("results.csv", "a") as f:
            f.write(f"{epoch+1},{loss:.5f},{acc:.5f}\n")

# --- Plot training metrics ---
def plot_results():
    df = pd.read_csv("results.csv")
    plt.figure(figsize=(10, 5))
    plt.plot(df["epoch"], df["loss"], label="Loss", marker='o')
    plt.plot(df["epoch"], df["accuracy"], label="Accuracy", marker='x')
    plt.xlabel("Epoch")
    plt.ylabel("Metric")
    plt.title("Training Progress")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# --- Main execution ---
def main():
    train(X_train, Y_train, X_dev, Y_dev, epochs=20, batch_size=32)
    plot_results()

if __name__ == "__main__":
    main()
