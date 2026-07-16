#!/usr/bin/env python
# coding: utf-8

# # Bias in Image based Automatic Gender Classification

# ## Overview

# Recent studies have shown that the machine learning models for gender classification task from face images perform differently across groups defined by skin tone. In this tutorial, we will demonstrate the use of the aif360 toolbox to study the differential performance of a custom classifier. We use a bias mitigating algorithm available in aif360 with the aim of improving a classfication model in terms of the fairness metrics. We will work with the UTK dataset for this tutorial. This can be downloaded from here:
# https://susanqq.github.io/UTKFace/
# 
# In a nutshell, we will follow these steps:
#  - Process images and load them as an aif360 dataset
#  - Learn a baseline classifier and obtain fairness metrics
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

# cmf 
display(Markdown("#### cmf: creating metawriter_tf"))
graph = True
pipeline_name = "aifcmf-env"
metawriter_tf = Cmf(filename="mlmd", pipeline_name, graph=graph)


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

if not os.path.exists(image_dir):
    # Tricks to download UTKFace dataset from the official Google drive distribution
    get_ipython().system('curl -c ./cookie -Ls "https://drive.google.com/uc?export=download&id=0BxYys69jI14kYVM3aVhKS1VhRUk" > /dev/null')
    get_ipython().system('curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk \'/download/ {print $NF}\' ./cookie`&id=0BxYys69jI14kYVM3aVhKS1VhRUk" -o UTKFace.tar.gz')
    get_ipython().system('tar -xzvf UTKFace.tar.gz -C ./ 2>&1 > dummy.log')

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

#X_train = X_train.transpose(0,3,1,2)
#X_test = X_test.transpose(0,3,1,2)

X_train = np.transpose(X_train,(0,3,1,2))
X_test = np.transpose(X_test,(0,3,1,2))

train = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_train.astype('float32'))), Variable(torch.LongTensor(y_train.astype('float32'))))
# train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size, shuffle=True)
test = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_test.astype('float32'))), Variable(torch.LongTensor(y_test.astype('float32'))))
test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size, shuffle=False)

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


# # Step 3: Apply the Reweighing algorithm to tranform the dataset
# Reweighing is a preprocessing technique that weights the examples in each (group, label) combination differently to ensure fairness before classification [1]. This is one of the very few pre-processing methods we are aware of that could tractably be applied to multimedia data (since it does not work with the features).
# 
#     References:
#     [1] F. Kamiran and T. Calders,"Data Preprocessing Techniques for Classification without Discrimination," Knowledge and Information Systems, 2012.

RW = Reweighing(unprivileged_groups=unprivileged_groups,
               privileged_groups=privileged_groups)
RW.fit(original_traning_dataset)
transf_traning_dataset = RW.transform(original_traning_dataset)

from aif360.metrics import BinaryLabelDatasetMetric
metric_orig_train = BinaryLabelDatasetMetric(original_traning_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)
metric_tranf_train = BinaryLabelDatasetMetric(transf_traning_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)

# cmf logging of  aif360 Reweighing ...
torch.save(transf_traning_dataset, 'transf_traning_dataset.pt')

_ = metawriter_tf.create_context(pipeline_stage="Reweighing")
_ = metawriter_tf.create_execution(execution_type="aif360-RW-Transform-execution")
_ = metawriter_tf.log_dataset('original_traning_dataset.pt', "input")
_ = metawriter_tf.log_dataset('transf_traning_dataset.pt', "output")


display(Markdown("#### Original training dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_orig_train.mean_difference())
display(Markdown("#### Transformed training dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_tranf_train.mean_difference())

metric_orig_test = BinaryLabelDatasetMetric(original_test_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)
transf_test_dataset = RW.transform(original_test_dataset)
metric_transf_test = BinaryLabelDatasetMetric(transf_test_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)
display(Markdown("#### Original testing dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_orig_test.mean_difference())
display(Markdown("#### Transformed testing dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_transf_test.mean_difference())

# cmf logging of  aif360 Reweighing ...
torch.save(transf_test_dataset, 'transf_test_dataset.pt')
#np.save('transf_test_dataset', transf_test_dataset)

# _ = metawriter_tf.create_context(pipeline_stage="Reweighing")
_ = metawriter_tf.create_execution(execution_type="aif360-RW-Transform-execution")
_ = metawriter_tf.log_dataset('original_test_dataset.pt', "input")
_ = metawriter_tf.log_dataset('transf_test_dataset.pt', "output")

# # Step 4: Learn a New Classfier using the Instance Weights
# We can see that the reweighing was able to reduce the difference in mean outcomes between privileged and unprivileged groups. This was done by learning appropriate weights for each training instance. In the current step, we will use these learned instance weights to train a network. We  will create a custom pytorch loss called `InstanceWeighetedCrossEntropyLoss` that uses the instances weights to produce the loss value for a batch of data samples.

tranf_train = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_train.astype('float32'))),
                                             Variable(torch.LongTensor(transf_traning_dataset.labels.astype('float32'))),
                                            Variable(torch.FloatTensor(transf_traning_dataset.instance_weights.astype('float32'))),)
tranf_train_loader = torch.utils.data.DataLoader(tranf_train, batch_size=1024, shuffle=True)

class InstanceWeighetedCrossEntropyLoss(nn.Module):
    """Cross entropy loss with instance weights."""
    def __init__(self):
        super(InstanceWeighetedCrossEntropyLoss, self).__init__()

    def forward(self, logits, target, weights):
        loss = log_sum_exp(logits) - select_target_class(logits, target.squeeze(1))
        loss = loss * weights
        return loss.mean()

#Helper functions
def select_target_class(logits, target):
    batch_size, num_classes = logits.size()
    mask = torch.autograd.Variable(torch.arange(0, num_classes)
                                               .long()
                                               .repeat(batch_size, 1)
                                               .to(device)
                                               .eq(target.data.repeat(num_classes, 1).t()))
    return logits.masked_select(mask)

def log_sum_exp(x):
    c, _ = torch.max(x, 1)
    y = c + torch.log(torch.exp(x - c.unsqueeze(dim=1).expand_as(x)).sum(1))
    return y


# ### Load a pretrained model and reset final fully connected layer.
model_ft = models.resnet18(pretrained=True)

torch.save(model_ft, 'resnet18_model.pt') # save the model to log into cmf
num_ftrs = model_ft.fc.in_features
# Here the size of each output sample is set to 2.
# Alternatively, it can be generalized to nn.Linear(num_ftrs, len(class_names)).
model_ft.fc = nn.Linear(num_ftrs, 2)
model_ft = model_ft.to(device)

tranf_model = model_ft
summary(tranf_model, (3,img_size,img_size))
'''
#@cuda.jit
def train_model(model, num_epochs):
    learning_rate = 0.001
    print_freq = 1
    print("X_train num_epochs : " + str(num_epochs))
    # Specify the loss and the optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    # Start training the model
    num_batches = len(tranf_train_loader)
    for epoch in range(num_epochs):
        for idx, (images, labels, weights) in enumerate(tranf_train_loader):
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels, weights)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if (idx+1) % print_freq == 0:
                print ('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}' .format(epoch+1, num_epochs, idx+1, num_batches, loss.item()))

#start training 
num_epochs = 25
train_model(tranf_model, num_epochs)
#numba.cuda.profile_stop()
'''
num_epochs = 25
learning_rate = 0.001
print_freq = 1

# Specify the loss and the optimizer
criterion = InstanceWeighetedCrossEntropyLoss()
optimizer = torch.optim.Adam(tranf_model.parameters(), lr=learning_rate)

# Start training the new model
num_batches = len(tranf_train_loader)
for epoch in range(num_epochs):
    for idx, (images, labels, weights) in enumerate(tranf_train_loader):

        images = images.to(device)
        labels = labels.to(device)
        
        outputs = tranf_model(images)
        loss = criterion(outputs, labels, weights)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        if (idx+1) % print_freq == 0:
            print ('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}' .format(epoch+1, num_epochs, idx+1, num_batches, loss.item()))

# cmf logging of tranf model training 
_ = metawriter_tf.create_context(pipeline_stage="Train_ON_Trnansfer")
_ = metawriter_tf.create_execution(execution_type="Train-TF-execution")

_ = metawriter_tf.log_model(
        path='resnet18_model.pt', event="input", model_framework="PyTroch", model_type="Pretrained",
        model_name="resnet18_imagenet_CNN" )
_ = metawriter_tf.log_dataset('transf_traning_dataset.pt', "input")

torch.save(tranf_model, 'model_tf_new.pt') # save the model to log into cmf

_ = metawriter_tf.log_model(
        path="model_tf_new.pt", event="output", model_framework="PyTroch", model_type="Transfer_Learning",
        model_name="resnet_gender_classification_TF_CNN" )

# Test the model
tranf_model.eval()
y_pred_transf = []
with torch.no_grad():
    for images, labels in test_loader:
        images = images.to(device)
        labels = labels.to(device)
        outputs = tranf_model(images)
        _, predicted = torch.max(outputs.data, 1)
        y_pred_transf += predicted.tolist()
y_pred_transf = np.array(y_pred_transf)


# cmf logging of evaluation  ...
#torch.save(y_pred_transf, 'y_pred_transf.pt') # save the result as file to log into cmf
np.save('y_pred_transf', y_pred_transf)

_ = metawriter_tf.create_context(pipeline_stage="Evaluate_transf")
_ = metawriter_tf.create_execution(execution_type="Evaluate-transf-execution")
_ = metawriter_tf.log_dataset('transf_test_dataset.pt', "input")
_ = metawriter_tf.log_model(
        path="model_tf_new.pt", event="input", model_framework="PyTroch", model_type="Transfer_Learning",
        model_name="resnet_gender_classification_TF_CNN" )

_ = metawriter_tf.log_dataset('y_pred_transf.npy', "output")

# Let us repeat the same steps as before to convert the predictions into aif360 dataset and obtain various metrics.
transf_predictions_test_dataset = dataset_wrapper(outcome=y_pred_transf, protected=p_test, 
                                                  unprivileged_groups=unprivileged_groups,
                                                  privileged_groups=privileged_groups,
                                                 favorable_label=favorable_label,
                                                  unfavorable_label=unfavorable_label
                                                 )

classified_metric_debiasing_test = ClassificationMetric(original_test_dataset, 
                                                 transf_predictions_test_dataset,
                                                 unprivileged_groups=unprivileged_groups,
                                                 privileged_groups=privileged_groups)
TPR = classified_metric_debiasing_test.true_positive_rate()
TNR = classified_metric_debiasing_test.true_negative_rate()
bal_acc_debiasing_test = 0.5*(TPR+TNR)

# cmf logging of  aif360 Reweighing ...
torch.save(transf_predictions_test_dataset, 'transf_predictions_test_dataset.pt')
#np.save('transf_predictions_test_dataset', transf_predictions_test_dataset)

_ = metawriter_tf.create_execution(execution_type="wrapper-test-execution")
_ = metawriter_tf.log_dataset('y_pred_transf.npy', "input")
_ = metawriter_tf.log_dataset('p_test.pt', "input")
_ = metawriter_tf.log_dataset('transf_predictions_test_dataset.pt', "output")

# cmf logging of aif_fairness calculation...
# cmf logging of evaluation  ...
_ = metawriter_tf.create_context(pipeline_stage="Fairness_tranf")
_ = metawriter_tf.create_execution(execution_type="Fairness_tranf_Evaluate-execution")
_ = metawriter_tf.log_dataset('transf_predictions_test_dataset.pt', "input")
_ = metawriter_tf.log_dataset('original_test_dataset.pt', "input")

# Since the reweighing algorithm only reduces the difference in mean outcomes, it doesn't guarantee that every classification metric will be reduced for the debiased model. So your mileage may vary based on how the dataset was split and how the model was trained.

## cmf querry to get metrics logged before debiasing transform 
## cmf querry for geting artifact and metrics

query = CmfQuery("./mlmd")
pipelines = query.get_pipeline_names()
stages = query.get_pipeline_stages(pipelines[0])
executions = query.get_all_executions_in_stage('Fairness')
artifacts = query.get_all_artifacts_for_execution(executions.iloc[0]["id"])
print('************ stages *************')
display(stages)
print('************ executions in stage = Fairness *************')
display(executions)
for index, row in artifacts.iterrows():
    if row["type"] == "metrics":
        break

classified_metric_nodebiasing_test = query.get_artifact(row["name"])

print('************ metrics in stage = Fairness *************')
print(classified_metric_nodebiasing_test)

print("#### Plain model - without debiasing - classification metrics")
print("Test set: Classification accuracy = %f" % classified_metric_nodebiasing_test['Classification_accuracy'])
print("Test set: Balanced classification accuracy = %f" % classified_metric_nodebiasing_test['Balanced_classification_accuracy'])
print("Test set: Statistical parity difference = %f" % classified_metric_nodebiasing_test['Statistical_parity_difference'])
print("Test set: Disparate impact = %f" % classified_metric_nodebiasing_test['Disparate_impact'])
print("Test set: Equal opportunity difference = %f" % classified_metric_nodebiasing_test['Equal_opportunity_difference'])
print("Test set: Average odds difference = %f" % classified_metric_nodebiasing_test['Average_odds_difference'])
print("Test set: Theil_index = %f" % classified_metric_nodebiasing_test['Theil_index'])
print("Test set: False negative rate difference = %f" % classified_metric_nodebiasing_test['False_negative_rate_difference'])

print("#### Model - with debiasing - classification metrics")
print("Test set: Classification accuracy = %f" % classified_metric_debiasing_test.accuracy())
print("Test set: Balanced classification accuracy = %f" % bal_acc_debiasing_test)
print("Test set: Statistical parity difference = %f" % classified_metric_debiasing_test.statistical_parity_difference())
print("Test set: Disparate impact = %f" % classified_metric_debiasing_test.disparate_impact())
print("Test set: Equal opportunity difference = %f" % classified_metric_debiasing_test.equal_opportunity_difference())
print("Test set: Average odds difference = %f" % classified_metric_debiasing_test.average_odds_difference())
print("Test set: Theil_index = %f" % classified_metric_debiasing_test.theil_index())
print("Test set: False negative rate difference = %f" % classified_metric_debiasing_test.false_negative_rate_difference())


# cmf logging of metrics...
result_tranf = dict(Classification_accuracy = classified_metric_debiasing_test.accuracy(),
              Balanced_classification_accuracy =  bal_acc_debiasing_test,
              Statistical_parity_difference = classified_metric_debiasing_test.statistical_parity_difference(),
              Disparate_impact = classified_metric_debiasing_test.disparate_impact(),
              Equal_opportunity_difference = classified_metric_debiasing_test.equal_opportunity_difference(),
              Average_odds_difference = classified_metric_debiasing_test.equal_opportunity_difference(),
              Theil_index = classified_metric_debiasing_test.theil_index(),
              False_negative_rate_difference = classified_metric_debiasing_test.false_negative_rate_difference()) 
_ = metawriter_tf.log_execution_metrics("transf_metrics", result_tranf)

# Let us break down these numbers by age to understand how these bias differs across age groups. For demonstration, we dividee all the samples into these age groups: 0-10, 10-20, 20-40, 40-60 and 60-150. For this we will create aif360 datasets using the subset of samples that fall into each of the age groups. The plot below shows how the `Equal opportunity difference` metric varies across age groups before and after applying the bias mitigating reweighing algorithm.

# Metrics sliced by age
age_range_intervals = [0, 10, 20, 40, 60, 150]
nodebiasing_perf = []
debiasing_perf = []

# cmf query to get result "Y_pred" before debiasing ....

executions = query.get_all_executions_in_stage('Evaluate')
artifacts = query.get_all_artifacts_for_execution(executions.iloc[0]["id"])
print('************ stages *************')
display(stages)
display(executions)
for index, row in artifacts.iterrows():
    #print ('row : ', index, ' value :', row)
    if row["event"] == "OUTPUT":
        break
evaluate_artifact = row["name"]
nodebaising_pred = evaluate_artifact.split(':',1)[0]

print('Loading y_pred : ', nodebaising_pred)

y_pred = np.load(nodebaising_pred)

for idx in range(len(age_range_intervals)-1):
    start = age_range_intervals[idx]
    end = age_range_intervals[idx+1]
    ids = np.where((age_test>start) & (age_test<end))
    true_dataset = dataset_wrapper(outcome=y_test[ids], protected=p_test[ids],
                                   unprivileged_groups=unprivileged_groups,
                                   privileged_groups=privileged_groups,
                                   favorable_label=favorable_label,
                                unfavorable_label=unfavorable_label)
    transf_pred_dataset = dataset_wrapper(outcome=y_pred_transf[ids], protected=p_test[ids],
                                          unprivileged_groups=unprivileged_groups,
                                          privileged_groups=privileged_groups,
                                          favorable_label=favorable_label,
                                          unfavorable_label=unfavorable_label)
    
    pred_dataset = dataset_wrapper(outcome=y_pred[ids], protected=p_test[ids],
                                   unprivileged_groups=unprivileged_groups,
                                   privileged_groups=privileged_groups,
                                   favorable_label=favorable_label,
                                   unfavorable_label=unfavorable_label)
 
    classified_metric_nodebiasing_test = ClassificationMetric(true_dataset, 
                                                 pred_dataset,
                                                 unprivileged_groups=unprivileged_groups,
                                                 privileged_groups=privileged_groups)
    
    classified_metric_debiasing_test = ClassificationMetric(true_dataset, 
                                                 transf_pred_dataset,
                                                 unprivileged_groups=unprivileged_groups,
                                                 privileged_groups=privileged_groups)
    
    nodebiasing_perf.append(classified_metric_nodebiasing_test.equal_opportunity_difference())
    debiasing_perf.append(classified_metric_debiasing_test.equal_opportunity_difference())

print('nodebiasing_perf : ', nodebiasing_perf)
print('debiasing_perf : ', debiasing_perf)
N = len(age_range_intervals)-1
fig, ax = plt.subplots()
ind = np.arange(N)
width = 0.35

p1 = ax.bar(ind, nodebiasing_perf, width, color='r')
p2 = ax.bar(ind + width, debiasing_perf, width,
            color='y')
ax.set_title('Equal opportunity difference by age group')
ax.set_xticks(ind + width / 2)
ax.set_xticklabels([str(age_range_intervals[idx])+'-'+str(age_range_intervals[idx+1]) for idx in range(N)])

ax.legend((p1[0], p2[0]), ('Before', 'After'))
ax.autoscale_view()

#plt.show()
plt.savefig('bias_before_after_fig.jpg')
print('***** finished ******')
plt.close(fig)

# # Conclusions
# In this tutorial, we have examined fairness in the scenario of binary classification with face images. We discussed methods to process several attributes of images, outcome variables, and protected attributes and created aif360 ready dataset objects on which many bias mitigation algorithms can be easily applied and fairness metrics can be easliy computed. We used the reweighing algorithm with the aim of improving the algorithmic fairness of the learned classifiers. The empirical results show slight improvement in the case of debiased model over the vanilla model. When sliced by age group, the results appear to be mixed bag and thus has scope for further improvements by considering age groups while learning models. 
