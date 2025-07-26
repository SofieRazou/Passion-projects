import random
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.models import Sequential
from sklearn.decomposition import PCA

from quantum_kernel import QClassifier

# ---- Reproducibility
SEED_VALUE = 42
random.seed(SEED_VALUE)
np.random.seed(SEED_VALUE)
tf.random.set_seed(SEED_VALUE)

# ---- Dataset config
NUM_CLASSES = 10
IMG_HEIGHT = 32
IMG_WIDTH = 32
NUM_CHANNELS = 3

EPOCHS = 5
BATCH_SIZE = 128

# --- Load CIFAR-10 dataset (replace with EuroSAT + TFDS if needed)
(X_train, y_train), (X_test, y_test) = cifar10.load_data()

X_train = X_train.astype("float32") / 255.0
X_test = X_test.astype("float32") / 255.0

y_train_cat = to_categorical(y_train, NUM_CLASSES)
y_test_cat = to_categorical(y_test, NUM_CLASSES)


def cnn_model(input_shape=(IMG_HEIGHT, IMG_WIDTH, NUM_CHANNELS), num_filters=32, kernel_size=3):
    model = Sequential()
    model.add(layers.Conv2D(filters=num_filters, kernel_size=kernel_size, padding="same", activation="relu", input_shape=input_shape))
    model.add(layers.Conv2D(filters=num_filters, kernel_size=kernel_size, padding="same", activation="relu"))
    model.add(layers.MaxPooling2D(pool_size=(2, 2)))
    model.add(layers.Flatten())
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(NUM_CLASSES, activation='softmax'))
    return model


model = cnn_model()
model.compile(
    optimizer='rmsprop',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

history = model.fit(
    X_train, y_train_cat,
    batch_size=BATCH_SIZE,
    epochs=EPOCHS,
    validation_split=0.3,
    verbose=1
)

# Extract features from penultimate layer (the Dense(64) layer)
feature_extractor = tf.keras.Model(inputs=model.input, outputs=model.layers[-2].output)
train_features = feature_extractor.predict(X_train)
test_features = feature_extractor.predict(X_test)

# Use PCA to reduce to 4 features for quantum classifier
pca = PCA(n_components=4)
train_features_pca = pca.fit_transform(train_features)
test_features_pca = pca.transform(test_features)

# Quantum Classifier expects labels as 1D arrays (not one-hot)
y_train_1d = y_train.flatten()
y_test_1d = y_test.flatten()

q_clf = QClassifier(nqubits=4)
q_clf.fit(train_features_pca, y_train_1d)
q_clf.evaluate(test_features_pca, y_test_1d)


# Plotting training history (optional)
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

def plot_results(metrics, title=None, ylabel=None, ylim=None, metric_name=None, color=None):
    fig, ax = plt.subplots(figsize=(10, 4))
    if not isinstance(metric_name, (list, tuple)):
        metrics = [metrics]
        metric_name = [metric_name]
    for idx, metric in enumerate(metrics):
        ax.plot(metric, color=color[idx])
    plt.xlabel("Epoch")
    plt.ylabel(ylabel)
    plt.ylim(ylim)
    plt.title(title)
    plt.xlim([0, EPOCHS - 1])
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    plt.grid(True)
    plt.legend(metric_name)
    plt.show()
    plt.close()

plot_results(
    [history.history["loss"], history.history["val_loss"]],
    ylabel="Loss",
    ylim=[0.0, 2.0],
    metric_name=["Training Loss", "Validation Loss"],
    color=["green", "blue"],
)

plot_results(
    [history.history["accuracy"], history.history["val_accuracy"]],
    ylabel="Accuracy",
    ylim=[0.0, 1.0],
    metric_name=["Training Accuracy", "Validation Accuracy"],
    color=["green", "blue"],
)
