import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class SmallCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.net(x)


def load_model(path="models/mnist/mnist_cnn.pth"):
    ckpt = torch.load(path, map_location="cpu")
    model = SmallCNN()
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model


MODEL = load_model()


def predict_from_array(arr_28x28: np.ndarray):
    x = torch.from_numpy(arr_28x28).float().unsqueeze(0).unsqueeze(0) / 255.0
    with torch.no_grad():
        logits = MODEL(x)
        probs = F.softmax(logits, dim=1).squeeze(0).numpy()

    return int(probs.argmax()), probs
