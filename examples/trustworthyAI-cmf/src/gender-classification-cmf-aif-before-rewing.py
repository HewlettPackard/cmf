#!/usr/bin/env python
# coding: utf-8

# # Bias in Image based Automatic Gender Classification

# ## Overview

# Recent studies have shown that the machine learning models for gender classification task from face images perform differently across groups defined by skin tone. In this tutorial, we will demonstrate the use of the aif360 toolbox to study the differential performance of a custom classifier. We use a bias mitigating algorithm available in aif360 with the aim of improving a classfication model in terms of the fairness metrics. We will work with the UTK dataset for this tutorial. This can be downloaded from here:
# https://susanqq.github.io/UTKFace/
# 
# In a nutshell, we will follow these steps:
#  - Process images and load them as an aif360 dataset
#  - Learn a baseline classifier through Transfer Learning  and obtain fairness metrics
#  - Call the `Reweighing` algorithm to obtain instance weights
#  - Learn a new classifier with the instance weights and obtain updated fairness metrics

# ### Call the import statements

import glob
from skimage import io
from skimage.transform import resize
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from IPython.display import Markdown, display

#!pip install torch
#!pip install torchsummary
import torch
import torch.utils.data
from torch.autograd import Variable
import torch.nn as nn
from torchsummary import summary
from IPython import get_ipython
import pandas as pd
import sys
sys.path.append("../")
import os

#!pip install aif360
from aif360.datasets import BinaryLabelDataset
from aif360.metrics import BinaryLabelDatasetMetric
from aif360.metrics import ClassificationMetric
from aif360.algorithms.preprocessing.reweighing import Reweighing

from IPython import get_ipython

# import troch related libraries 
import torchvision
from torchvision import datasets, models, transforms
import torch.optim as optim
from torch.optim import lr_scheduler
import torch.backends.cudnn as cudnn
import time
import copy

# importing cmf for pipeline logging 
from cmflib.cmf import Cmf
import collections
from cmflib.cmfquery import CmfQuery

# import numba lib for GPU operation
from numba import cuda

np.random.seed(99)
torch.manual_seed(99)
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

# Defining cmf pipeline for logging artifacts 
graph = True 
metawriter = Cmf(filename="mlmd", pipeline_name="aifcmf-env", graph=graph)


# # Step 1: Load and Process Images
# The first step is to to download the `Aligned&cropped` images at the location mentioned above.
# 
# After unzipping the downloaded file, point the location of the folder in the `image_dir` variable below. 
# The file name has the following format `age`-`gender`-`race`-`date&time`.jpg
# 
#     age: indicates the age of the person in the picture and can range from 0 to 116.
#     gender: indicates the gender of the person and is either 0 (male) or 1 (female).
#     race: indicates the race of the person and can be from 0 to 4, denoting White, Black, Asian, Indian, and Others (like Hispanic, Latino, Middle Eastern).
#     date&time: indicates the date and time an image was collected in the UTK dataset.
# 
# For this tutorial we will restict the images to contain `White` and `Others` races. We need to specify the unprivileged and priviledged groups to obtain various metrics from the aif360 toolbox. We set `White` as the priviledged group and `Others` as the unpriviledged group for computing the results with gender as the outcome variable that needs to be predicted. We set prediction as `female (1)` as the unfavorable label and `male (0)` as favorable label for the purpose of computing metrics, it does not have any special meaning in the context of gender prediction.


races_to_consider = [0,4]
unprivileged_groups = [{'race': 4.0}]
privileged_groups = [{'race': 0.0}]
favorable_label = 0.0 
unfavorable_label = 1.0


# ### Update the `image_dir` with the downloaded and extracted images location and specify the desired image size.
# The images are loaded and resized using opencv library. The following code creates three key numpy arrays each containing the raw images, the race attributes and the gender labels.

image_dir = 'UTKFace/'
input_dir = 'UTKFace'
img_size = 224


# Tricks to download UTKFace dataset from the official Google drive distribution
get_ipython().system('curl -c ./cookie -Ls "https://drive.google.com/uc?export=download&id=0BxYys69jI14kYVM3aVhKS1VhRUk" > /dev/null')
get_ipython().system('curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk \'/download/ {print $NF}\' ./cookie`&id=0BxYys69jI14kYVM3aVhKS1VhRUk" -o UTKFace.tar.gz')
get_ipython().system('tar -xzvf UTKFace.tar.gz -C ./ 2>&1 > dummy.log')

_ = metawriter.create_context(pipeline_stage="Parse")
_ = metawriter.create_execution(execution_type="parse-dataset")
_ = metawriter.log_dataset(image_dir, "input", custom_properties={"img_size": img_size})

protected_race = []
outcome_gender = []
feature_image = []
feature_age = []

for i, image_path in enumerate(glob.glob(image_dir + "*.jpg")):
    try:
        age, gender, race = os.path.basename(image_path).split("_")[:3]
        age = int(age)
        gender = int(gender)
        race = int(race)
        
        if race in races_to_consider:
            protected_race.append(race)
            outcome_gender.append(gender)
            feature_image.append(resize(io.imread(image_path), (img_size, img_size)))
            feature_age.append(age)
    except:
        print("Missing: " + image_path)

feature_image_mat = np.array(feature_image)
outcome_gender_mat =  np.array(outcome_gender)
protected_race_mat =  np.array(protected_race)
age_mat = np.array(feature_age)

# ## step - 2 Split the dataset into train and test
# 
# Let us rescale the pixels to lie between $-1$ and $1$ and split the complete dataset into train and test sets. 
# We use $70$-$30$ percentage for train and test, respectively.

feature_image_mat_normed = 2.0 *feature_image_mat.astype('float32') - 1.0

N = len(feature_image_mat_normed)
ids = np.random.permutation(N)
train_size=int(0.7 * N)
X_train = feature_image_mat_normed[ids[0:train_size]]
y_train = outcome_gender_mat[ids[0:train_size]]
X_test = feature_image_mat_normed[ids[train_size:]]
y_test = outcome_gender_mat[ids[train_size:]]

p_train = protected_race_mat[ids[0:train_size]]
p_test = protected_race_mat[ids[train_size:]]

age_train = age_mat[ids[0:train_size]]
age_test = age_mat[ids[train_size:]]

# Report some numbers for sanity checking 
print("N = "+ str(N))
print("train_size = " + str(train_size))
print("X_train shape: " + str(X_train.shape))


batch_size = 1024
X_train = np.transpose(X_train,(0,3,1,2))
X_test = np.transpose(X_test,(0,3,1,2))

train = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_train.astype('float32'))), Variable(torch.LongTensor(y_train.astype('float32'))))
train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size, shuffle=True)
test = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_test.astype('float32'))), Variable(torch.LongTensor(y_test.astype('float32'))))
test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size, shuffle=False)

# cmf logging 
torch.save(train, 'train_imgs.pt')
torch.save(test, 'test_imgs.pt')

_ = metawriter.log_dataset('train_imgs.pt', "output")
_ = metawriter.log_dataset('test_imgs.pt', "output")

# cmf logging for extracting 'age' 'race' informations from filename.
torch.save(p_train, 'p_train.pt')
torch.save(p_test, 'p_test.pt')

_ = metawriter.create_context(pipeline_stage="protected_features")
_ = metawriter.create_execution(execution_type="protected_features_extraction")
_ = metawriter.log_dataset(image_dir, "input", custom_properties={"number_of_images": N,"img_size": img_size})
_ = metawriter.log_dataset('p_train.pt', "output", custom_properties={"number_of_Train_images": train_size,"img_size": img_size})
_ = metawriter.log_dataset('p_test.pt', "output", custom_properties={"number_of_Train_images": (N-train_size),"img_size": img_size})

# # Step-3 :  transfer learning for gender classification
#@cuda.jit
def train_model(model, criterion, optimizer, num_epochs):
    learning_rate = 0.001
    print_freq = 1
    print("X_train num_epochs : " + str(num_epochs))
    # Specify the loss and the optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Start training the model
    num_batches = len(train_loader)
    for epoch in range(num_epochs):
        for idx, (images, labels) in enumerate(train_loader):
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if (idx+1) % print_freq == 0:
                print ('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}' .format(epoch+1, num_epochs, idx+1, num_batches, loss.item()))

# ## Finetuning : 
# ### Load a pretrained model and reset final fully connected layer.

model_ft = models.resnet18(pretrained=True)

torch.save(model_ft, 'resnet18_model.pt') # save the model to log into cmf
num_ftrs = model_ft.fc.in_features

# Here the size of each output sample is set to 2.
# Alternatively, it can be generalized to nn.Linear(num_ftrs, len(class_names)).
model_ft.fc = nn.Linear(num_ftrs, 2)
model_ft = model_ft.to(device)

# Next, we will create the pytorch train and test data loaders after transposing and converting the images and labels. The batch size is set to $1024$.
# ## create a transfer-learning model...

model = model_ft
summary(model, (3,img_size,img_size))

# ## Training the network
# Next,  we will train the model summarized above. `num_epochs` specifies the number of epochs used for  training. The learning rate is set to $0.001$. We will use the `Adam` optimizer to minimze the standard cross-entropy loss for classification tasks.
# 
# 
# #### It should take around 15-25 min on CPU. On GPU though, it takes less than a minute.

learning_rate = 0.001
print_freq = 1

# Specify the loss and the optimizer
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

#start training 
train_model(model, criterion, optimizer, num_epochs=1)
#numba.cuda.profile_stop()
# cmf logging of model training 
_ = metawriter.create_context(pipeline_stage="Train")
_ = metawriter.create_execution(execution_type="Train-execution")

_ = metawriter.log_model(
        path='resnet18_model.pt', event="input", model_framework="PyTroch", model_type="Pretrained",
        model_name="resnet18_imagenet_CNN" )
_ = metawriter.log_dataset('train_imgs.pt', "input")

torch.save(model, 'model_tf.pt') # save the model to log into cmf

_ = metawriter.log_model(
        path="model_tf.pt", event="output", model_framework="PyTroch", model_type="Transfer_Learning",
        model_name="resnet_gender_classification_CNN" )

# #### Measure Fairness Metrics
# Let's get the predictions of this trained model on the test and use them to compute various fariness metrics available in the aif360 toolbox. 

## Run Evaluation on fine tuned model
model.eval()
y_pred = []
with torch.no_grad():
    for images, labels in test_loader:
        images = images.to(device)
        labels = labels.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs.data, 1)
        y_pred += predicted.tolist()
y_pred = np.array(y_pred)

# cmf logging of evaluation  ...
#torch.save(y_pred, 'y_pred.pt') # save the result as file to log into cmf
np.save('y_pred', y_pred)
_ = metawriter.create_context(pipeline_stage="Evaluate")
_ = metawriter.create_execution(execution_type="Evaluate-execution")
_ = metawriter.log_dataset('test_imgs.pt', "input")
_ = metawriter.log_model(
        path="model_tf.pt", event="input", model_framework="PyTroch", model_type="Transfer_Learning",
        model_name="resnet_gender_classification_CNN" )

_ = metawriter.log_dataset('y_pred.npy', "output")
# The wrapper function defined below can be used to convert the numpy arrays and the related meta data into a aif360 dataset. This will ease the process of computing metrics and comparing two datasets. The wrapper consumes the outcome array, the protected attribute array, information about unprivileged_groups and privileged_groups; and the favorable and unfavorable label to produce an instance of aif360's `BinaryLabelDataset`.

def dataset_wrapper(outcome, protected, unprivileged_groups, privileged_groups,
                          favorable_label, unfavorable_label):
    """ 
    A wraper function to create aif360 dataset from outcome and protected in numpy array format.
    """
    df = pd.DataFrame(data=outcome,
                      columns=['outcome'])
    df['race'] = protected
    
    dataset = BinaryLabelDataset(favorable_label=favorable_label,
                                       unfavorable_label=unfavorable_label,
                                       df=df,
                                       label_names=['outcome'],
                                       protected_attribute_names=['race'],
                                       unprivileged_protected_attributes=unprivileged_groups)
    return dataset

# Binarization of datasets through wrapper function for evaluating biasness metrics 
original_traning_dataset = dataset_wrapper(outcome=y_train, protected=p_train, 
                                            unprivileged_groups=unprivileged_groups, 
                                            privileged_groups=privileged_groups,
                                            favorable_label=favorable_label,
                                            unfavorable_label=unfavorable_label)

original_test_dataset = dataset_wrapper(outcome=y_test, protected=p_test, 
                                            unprivileged_groups=unprivileged_groups, 
                                            privileged_groups=privileged_groups,
                                            favorable_label=favorable_label,
                                            unfavorable_label=unfavorable_label)

plain_predictions_test_dataset = dataset_wrapper(outcome=y_pred, protected=p_test, 
                                                    unprivileged_groups=unprivileged_groups,
                                                    privileged_groups=privileged_groups,
                                                    favorable_label=favorable_label,
                                                    unfavorable_label=unfavorable_label)

# cmf logging of dataset wrapper...
torch.save(original_traning_dataset, 'original_traning_dataset.pt') # save to log into cmf
torch.save(original_test_dataset, 'original_test_dataset.pt') # save to log into cmf
torch.save(plain_predictions_test_dataset, 'plain_predictions_test_dataset.pt')

# loging wraper dataset to cmf ... 
_ = metawriter.create_context(pipeline_stage="wrapper")
_ = metawriter.create_execution(execution_type="wrapper-train-execution")
_ = metawriter.log_dataset('p_train.pt', "input")
_ = metawriter.log_dataset('plain_predictions_test_dataset.pt', "output")

_ = metawriter.create_execution(execution_type="wrapper-test-execution")
_ = metawriter.log_dataset('p_test.pt', "input")
_ = metawriter.log_dataset('original_test_dataset.pt', "output")

_ = metawriter.create_execution(execution_type="wrapper-test-execution")
_ = metawriter.log_dataset('p_test.pt', "input")
_ = metawriter.log_dataset('y_pred.npy', "input")
_ = metawriter.log_dataset('plain_predictions_test_dataset.pt', "output")

# #### Obtaining the Classification Metrics
# We use the `ClassificationMetric` class from the aif360 toolbox for computing metrics based on two BinaryLabelDatasets. The first dataset is the original one and the second is the output of the classification transformer (or similar). Later on we will use `BinaryLabelDatasetMetric` which computes based on a single `BinaryLabelDataset`.


classified_metric_nodebiasing_test = ClassificationMetric(original_test_dataset, 
                                                 plain_predictions_test_dataset,
                                                 unprivileged_groups=unprivileged_groups,
                                                 privileged_groups=privileged_groups)
TPR = classified_metric_nodebiasing_test.true_positive_rate()
TNR = classified_metric_nodebiasing_test.true_negative_rate()
bal_acc_nodebiasing_test = 0.5*(TPR+TNR)

# cmf logging of fairness evaluation  ...
_ = metawriter.create_context(pipeline_stage="Fairness")
_ = metawriter.create_execution(execution_type="Fairness_Evaluate-execution")
_ = metawriter.log_dataset('original_test_dataset.pt', "input")
_ = metawriter.log_dataset('plain_predictions_test_dataset.pt', "input")

display(Markdown("#### Plain model - without debiasing - classification metrics"))
print("Test set: Classification accuracy = %f" % classified_metric_nodebiasing_test.accuracy())
print("Test set: Balanced classification accuracy = %f" % bal_acc_nodebiasing_test)
print("Test set: Statistical parity difference = %f" % classified_metric_nodebiasing_test.statistical_parity_difference())
print("Test set: Disparate impact = %f" % classified_metric_nodebiasing_test.disparate_impact())
print("Test set: Equal opportunity difference = %f" % classified_metric_nodebiasing_test.equal_opportunity_difference())
print("Test set: Average odds difference = %f" % classified_metric_nodebiasing_test.average_odds_difference())
print("Test set: Theil index = %f" % classified_metric_nodebiasing_test.theil_index())
print("Test set: False negative rate difference = %f" % classified_metric_nodebiasing_test.false_negative_rate_difference())

# cmf logging of metrics...
result = dict(Classification_accuracy = classified_metric_nodebiasing_test.accuracy(),
              Balanced_classification_accuracy =  bal_acc_nodebiasing_test,
              Statistical_parity_difference = classified_metric_nodebiasing_test.statistical_parity_difference(),
              Disparate_impact = classified_metric_nodebiasing_test.disparate_impact(),
              Equal_opportunity_difference = classified_metric_nodebiasing_test.equal_opportunity_difference(),
              Average_odds_difference = classified_metric_nodebiasing_test.average_odds_difference(),
              Theil_index = classified_metric_nodebiasing_test.theil_index(),
              False_negative_rate_difference = classified_metric_nodebiasing_test.false_negative_rate_difference()) 

_ = metawriter.log_execution_metrics("metrics", result)
