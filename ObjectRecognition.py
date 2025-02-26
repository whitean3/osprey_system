import torch
import torchvision.models as models
import cv2
import os
from resnet_pytorch import ResNet
from torchvision import transforms
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from Response_Correlation import Pairs

# Load the pre-trained ResNet-152 model
model = ResNet.from_pretrained("resnet152")
model.eval()


# Pre-processing and feature extraction function
def extract_features(image_path, model):
    img = Image.open(image_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    img = transform(img).unsqueeze(0)  # Add batch dimension
    print(img)
    with torch.no_grad():
        features = model(img)
    # print(features)
    return features.numpy().flatten()



def object_recognition(result1, result2, r2, r1):
    pairs = []
    for object1 in result1['objects']:
        for object2 in result2['objects']:
            pairs.append(Pairs(object1, object2))

    for i in range(len(pairs)):
        pairs[i].Detector1 = result1['Detector']
        pairs[i].Detector2 = result2['Detector']
        pairs[i].Path1 = result1['image paths'][i]
        pairs[i].Path2 = result2['image paths'][i]
        features1 = extract_features(pairs[i].Path1, model)
        features2 =  extract_features(pairs[i].Path2, model)
        pairs[i].Response2_true = r2
        pairs[i].Response1 = r1
        # Compute cosine similarity
        pairs[i].Similarity = cosine_similarity([features1], [features2])[0][0]

    return pairs