from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
from api.mnist import predict_from_array

app = FastAPI(title="MNIST Inference API")


class MNISTRequest(BaseModel):
    pixels: list  # 784 values


class MNISTResponse(BaseModel):
    predicted_label: int
    probabilities: dict


@app.post("/mnist/predict", response_model=MNISTResponse)
def mnist_predict(req: MNISTRequest):
    arr = np.array(req.pixels).reshape(28, 28)

    pred, probs = predict_from_array(arr)

    return {
        "predicted_label": pred,
        "probabilities": {str(i): float(probs[i]) for i in range(10)},
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "mnist-inference-api"
    }
