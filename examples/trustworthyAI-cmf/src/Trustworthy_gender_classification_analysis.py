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

import os
import glob
from skimage import io
from skimage.transform import resize
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import gridspec
from IPython.display import Markdown, display
from IPython import get_ipython
#get_ipython().system('pip install torch')
#get_ipython().system('pip install torchsummary')
import torch
import torch.utils.data
from torch.autograd import Variable
import torch.nn as nn
from torchsummary import summary

import pandas as pd
import sys
sys.path.append("../")

#get_ipython().system('pip install aif360')
from aif360.datasets import BinaryLabelDataset
from aif360.metrics import BinaryLabelDatasetMetric
from aif360.metrics import ClassificationMetric
from aif360.algorithms.preprocessing.reweighing import Reweighing
from aif360.algorithms.inprocessing.adversarial_debiasing import AdversarialDebiasing
from cmflib.cmf import Cmf
from cmflib.cmfquery import CmfQuery

import tensorflow as tf
tf.compat.v1.disable_eager_execution()
tf.__version__

np.random.seed(99)
torch.manual_seed(99)


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
img_size = 64

# Tricks to download UTKFace dataset from the official Google drive distribution
if not os.path.exists(image_dir):
    get_ipython().system('curl -c ./cookie -Ls "https://drive.google.com/uc?export=download&id=0BxYys69jI14kYVM3aVhKS1VhRUk" > /dev/null')
    get_ipython().system('curl -Lb ./cookie "https://drive.google.com/uc?export=download&confirm=`awk \'/download/ {print $NF}\' ./cookie`&id=0BxYys69jI14kYVM3aVhKS1VhRUk" -o UTKFace.tar.gz')
    get_ipython().system('tar -xzvf UTKFace.tar.gz -C ./ 2>&1 > dummy.log')


import os

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


# # Step 2: Learn a Baseline Classifier
# Let's build a simple convolutional neural network (CNN) with $3$ convolutional layers and $2$ fully connected layers using the `pytorch` framework. 
# ![CNN](images/cnn_arch.png)
# Each convolutional layer is followed by a maxpool layer. The final layer provides the logits for the binary gender predicition task.


class ThreeLayerCNN(torch.nn.Module):
    """
    Input: 128x128 face image (eye aligned).
    Output: 1-D tensor with 2 elements. Used for binary classification.
    Parameters:
        Number of conv layers: 3
        Number of fully connected layers: 2       
    """
    def __init__(self):
        super(ThreeLayerCNN,self).__init__()
        self.conv1 = torch.nn.Conv2d(3,6,5)
        self.pool = torch.nn.MaxPool2d(2,2)
        self.conv2 = torch.nn.Conv2d(6,16,5)
        self.conv3 = torch.nn.Conv2d(16,16,6)
        self.fc1 = torch.nn.Linear(16*4*4,120)
        self.fc2 = torch.nn.Linear(120,2)


    def forward(self, x):
        x = self.pool(torch.nn.functional.relu(self.conv1(x)))
        x = self.pool(torch.nn.functional.relu(self.conv2(x)))
        x = self.pool(torch.nn.functional.relu(self.conv3(x)))
        x = x.view(-1,16*4*4)
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.fc2(x)
        return x


# ## Split the dataset into train and test
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


# Next, we will create the pytorch train and test data loaders after transposing and converting the images and labels. The batch size is set to $1024$.


batch_size = 1024

#X_train = X_train.transpose(0,3,1,2)
#X_test = X_test.transpose(0,3,1,2)

X_train = np.transpose(X_train,(0,3,1,2))
X_test = np.transpose(X_test,(0,3,1,2))

train = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_train.astype('float32'))), Variable(torch.LongTensor(y_train.astype('float32'))))
train_loader = torch.utils.data.DataLoader(train, batch_size=batch_size, shuffle=True)
test = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_test.astype('float32'))), Variable(torch.LongTensor(y_test.astype('float32'))))
test_loader = torch.utils.data.DataLoader(test, batch_size=batch_size, shuffle=False)


# ## Create a Plain Model
# In the next few steps, we will create and intialize a model with the above described architecture and train it.


device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
model = ThreeLayerCNN().to(device)
summary(model, (3,img_size,img_size))


# ## Training the network
# Next,  we will train the model summarized above. `num_epochs` specifies the number of epochs used for  training. The learning rate is set to $0.001$. We will use the `Adam` optimizer to minimze the standard cross-entropy loss for classification tasks.


num_epochs = 25
learning_rate = 0.001
print_freq = 1

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


# #### Measure Fairness Metrics
# Let's get the predictions of this trained model on the test and use them to compute various fariness metrics available in the aif360 toolbox. 

# Run model on test set in eval mode.
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


# The wrapper function defined below can be used to convert the numpy arrays and the related meta data into a aif360 dataset. This will ease the process of computing metrics and comparing two datasets. The wrapper consumes the outcome array, the protected attribute array, information about unprivileged_groups and privileged_groups; and the favorable and unfavorable label to produce an instance of aif360's `BinaryLabelDataset`.

def dataset_wrapper(outcome, protected, unprivileged_groups, privileged_groups,
                          favorable_label, unfavorable_label):
    """ A wraper function to create aif360 dataset from outcome and protected in numpy array format.
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
plain_predictions_test_dataset = dataset_wrapper(outcome=y_pred, protected=p_test, 
                                                       unprivileged_groups=unprivileged_groups,
                                                       privileged_groups=privileged_groups,
                                                 favorable_label=favorable_label,
                                          unfavorable_label=unfavorable_label)


# #### Obtaining the Classification Metrics
# We use the `ClassificationMetric` class from the aif360 toolbox for computing metrics based on two BinaryLabelDatasets. The first dataset is the original one and the second is the output of the classification transformer (or similar). Later on we will use `BinaryLabelDatasetMetric` which computes based on a single `BinaryLabelDataset`.

classified_metric_nodebiasing_test = ClassificationMetric(original_test_dataset, 
                                                 plain_predictions_test_dataset,
                                                 unprivileged_groups=unprivileged_groups,
                                                 privileged_groups=privileged_groups)
TPR = classified_metric_nodebiasing_test.true_positive_rate()
TNR = classified_metric_nodebiasing_test.true_negative_rate()
bal_acc_nodebiasing_test = 0.5*(TPR+TNR)


display(Markdown("#### Plain model - without debiasing - classification metrics"))
print('**********************************************************************************')
print("Test set: Classification accuracy = %f" % classified_metric_nodebiasing_test.accuracy())
print("Test set: Balanced classification accuracy = %f" % bal_acc_nodebiasing_test)
print("Test set: Statistical parity difference = %f" % classified_metric_nodebiasing_test.statistical_parity_difference())
print("Test set: Disparate impact = %f" % classified_metric_nodebiasing_test.disparate_impact())
print("Test set: Equal opportunity difference = %f" % classified_metric_nodebiasing_test.equal_opportunity_difference())
print("Test set: Average odds difference = %f" % classified_metric_nodebiasing_test.average_odds_difference())
print("Test set: Theil index = %f" % classified_metric_nodebiasing_test.theil_index())
print("Test set: False negative rate difference = %f" % classified_metric_nodebiasing_test.false_negative_rate_difference())
print('**********************************************************************************')

# # Step 3: Apply the Reweighing algorithm to tranform the dataset
# Reweighing is a preprocessing technique that weights the examples in each (group, label) combination differently to ensure fairness before classification [1]. This is one of the very few pre-processing methods we are aware of that could tractably be applied to multimedia data (since it does not work with the features).
# 
#     References:
#     [1] F. Kamiran and T. Calders,"Data Preprocessing Techniques for Classification without Discrimination," Knowledge and Information Systems, 2012.

'''
RW = Reweighing(unprivileged_groups=unprivileged_groups,
               privileged_groups=privileged_groups)
RW.fit(original_traning_dataset)
transf_traning_dataset = RW.transform(original_traning_dataset)
'''
print("**** Applying AdversarialDebiasing on train and test dataset")
sess = tf.compat.v1.Session()
debiased_model = AdversarialDebiasing(privileged_groups = privileged_groups,
                          unprivileged_groups = unprivileged_groups,
                          scope_name='debiased_classifier',
                          debias=True,
                          sess=sess)

debiased_model.fit(original_traning_dataset)

transf_traning_dataset = debiased_model.predict(original_traning_dataset)

metric_orig_train = BinaryLabelDatasetMetric(original_traning_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)
metric_tranf_train = BinaryLabelDatasetMetric(transf_traning_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)


display(Markdown("#### Original training dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_orig_train.mean_difference())
display(Markdown("#### Transformed training dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_tranf_train.mean_difference())


metric_orig_test = BinaryLabelDatasetMetric(original_test_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)
# transf_test_dataset = RW.transform(original_test_dataset)
transf_test_dataset = debiased_model.predict(original_test_dataset)
metric_transf_test = BinaryLabelDatasetMetric(transf_test_dataset, 
                                             unprivileged_groups=unprivileged_groups,
                                             privileged_groups=privileged_groups)
display(Markdown("#### Original testing dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_orig_test.mean_difference())
display(Markdown("#### Transformed testing dataset"))
print("Difference in mean outcomes between privileged and unprivileged groups = %f" % metric_transf_test.mean_difference())


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


tranf_model = ThreeLayerCNN().to(device)

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


# Since the reweighing algorithm only reduces the difference in mean outcomes, it doesn't guarantee that every classification metric will be reduced for the debiased model. So your mileage may vary based on how the dataset was split and how the model was trained.

display(Markdown("#### Plain model - without debiasing - classification metrics"))
print('**********************************************************************************')
print("Test set: Classification accuracy = %f" % classified_metric_nodebiasing_test.accuracy())
print("Test set: Balanced classification accuracy = %f" % bal_acc_nodebiasing_test)
print("Test set: Statistical parity difference = %f" % classified_metric_nodebiasing_test.statistical_parity_difference())
print("Test set: Disparate impact = %f" % classified_metric_nodebiasing_test.disparate_impact())
print("Test set: Equal opportunity difference = %f" % classified_metric_nodebiasing_test.equal_opportunity_difference())
print("Test set: Average odds difference = %f" % classified_metric_nodebiasing_test.average_odds_difference())
print("Test set: Theil_index = %f" % classified_metric_nodebiasing_test.theil_index())
print("Test set: False negative rate difference = %f" % classified_metric_nodebiasing_test.false_negative_rate_difference())
print('**********************************************************************************')
display(Markdown("#### Model - with debiasing - classification metrics"))
print('**********************************************************************************')
print("Test set: Classification accuracy = %f" % classified_metric_debiasing_test.accuracy())
print("Test set: Balanced classification accuracy = %f" % bal_acc_debiasing_test)
print("Test set: Statistical parity difference = %f" % classified_metric_debiasing_test.statistical_parity_difference())
print("Test set: Disparate impact = %f" % classified_metric_debiasing_test.disparate_impact())
print("Test set: Equal opportunity difference = %f" % classified_metric_debiasing_test.equal_opportunity_difference())
print("Test set: Average odds difference = %f" % classified_metric_debiasing_test.average_odds_difference())
print("Test set: Theil_index = %f" % classified_metric_debiasing_test.theil_index())
print("Test set: False negative rate difference = %f" % classified_metric_debiasing_test.false_negative_rate_difference())
print('**********************************************************************************')
# Let us break down these numbers by age to understand how these bias differs across age groups. For demonstration, we dividee all the samples into these age groups: 0-10, 10-20, 20-40, 40-60 and 60-150. For this we will create aif360 datasets using the subset of samples that fall into each of the age groups. The plot below shows how the `Equal opportunity difference` metric varies across age groups before and after applying the bias mitigating reweighing algorithm.

## cmf querry for geting artifact and metrics
pipeline_name="aifcmf-env"
query = CmfQuery("./mlmd")
pipelines = query.get_pipeline_names()
stages = query.get_pipeline_stages(pipelines[0])
print('************ stages *************')
print(stages)
executions = query.get_all_executions_in_stage('Fairness')
#stage_fairness = pipeline_name + '/' + 'Fairness'
#executions = query.get_all_executions_in_stage(stage_fairness)
print('************ executions *************')
print(executions)
artifacts = query.get_all_artifacts_for_execution(executions.iloc[0]["id"])
print('************ executions in stage = Fairness *************')
display(executions)
for index, row in artifacts.iterrows():
    if row["type"] == "metrics":
        break

classified_metric_nodebiasing_test_TF = query.get_artifact(row["name"])

print('************ metrics in stage = Fairness *************')
print(classified_metric_nodebiasing_test_TF)


############## after appliing rewirhing algo #################
executions = query.get_all_executions_in_stage('Fairness_tranf')
#stage_fairness = pipeline_name + '/' + 'Fairness_tranf'
#executions = query.get_all_executions_in_stage(stage_fairness)
artifacts = query.get_all_artifacts_for_execution(executions.iloc[0]["id"])
for index, row in artifacts.iterrows():
    if row["type"] == "transf_metrics":
        break

classified_metric_debiasing_test_TF = query.get_artifact(row["name"])
print('************ metrics in stage = Fairness_tranf *************')

print(classified_metric_debiasing_test_TF)
print('**********************************************')
print("keys: ", classified_metric_debiasing_test_TF.keys())
################## 

############## after appliing adversial algo #################
executions = query.get_all_executions_in_stage('Fairness_tranf_AD')
#stage_fairness = pipeline_name + '/' + 'Fairness_tranf_AD'
#executions = query.get_all_executions_in_stage(stage_fairness)
artifacts = query.get_all_artifacts_for_execution(executions.iloc[0]["id"])
for index, row in artifacts.iterrows():
    if row["type"] == "transf_metrics_ad":
        break

classified_metric_debiasing_test_TF_Ad = query.get_artifact(row["name"])
print(classified_metric_debiasing_test_TF_Ad)

################## 

# creating dataframe
df = pd.DataFrame({
    'Bias_Before_mitigation': ['Classification_accuracy', 'Balanced_classification_accuracy', 'Statistical_parity_difference', 'Disparate_impact', 'Equal_opportunity_difference', 'Average_odds_difference', 'Theil_index', 'False_negative_rate_difference'],
    'Plain_CNN': [classified_metric_nodebiasing_test.accuracy(),
                bal_acc_nodebiasing_test,
                classified_metric_nodebiasing_test.statistical_parity_difference(),
                classified_metric_nodebiasing_test.disparate_impact(),
                classified_metric_nodebiasing_test.equal_opportunity_difference(),
                classified_metric_nodebiasing_test.average_odds_difference(),
                classified_metric_nodebiasing_test.theil_index(),
                classified_metric_nodebiasing_test.false_negative_rate_difference()],
    'Transfer_Learning': [float(classified_metric_nodebiasing_test_TF['Classification_accuracy']),
                float(classified_metric_nodebiasing_test_TF['Balanced_classification_accuracy']),
                float(classified_metric_nodebiasing_test_TF['Statistical_parity_difference']),
                float(classified_metric_nodebiasing_test_TF['Disparate_impact']),
                float(classified_metric_nodebiasing_test_TF['Equal_opportunity_difference']),
                float(classified_metric_nodebiasing_test_TF['Average_odds_difference']),
                float(classified_metric_nodebiasing_test_TF['Theil_index']),
                float(classified_metric_nodebiasing_test_TF['False_negative_rate_difference'])]
})


print("before_mitigation :", df)
df.to_csv('before_biasmitigation_CNN_TF.csv')
# plotting graph
#df.plot(x="Bias_Before_mitigation", y=["Plain_CNN", "Transfer_Learning"], kind="bar")
df.plot(x="Bias_Before_mitigation", kind="bar")

plt.savefig('Bias_Before_Mitigation_CNN_TF.jpg')
print('***** finished ******')
#plt.close(fig)

# creating dataframe after bias-mitigation
df1 = pd.DataFrame({
    'Bias_After_Mitigation': ['Classification_accuracy', 'Balanced_classification_accuracy', 'Statistical_parity_difference', 'Equal_opportunity_difference', 'Average_odds_difference', 'Theil_index', 'False_negative_rate_difference'],
    'Plain_CNN': [classified_metric_debiasing_test.accuracy(), 
                bal_acc_debiasing_test, 
                classified_metric_debiasing_test.statistical_parity_difference(), 
                classified_metric_debiasing_test.equal_opportunity_difference(),
                classified_metric_debiasing_test.average_odds_difference(),
                classified_metric_debiasing_test.theil_index(),
                classified_metric_debiasing_test.false_negative_rate_difference()],
    'Transfer_Learning': [float(classified_metric_debiasing_test_TF['Classification_accuracy']),
                float(classified_metric_debiasing_test_TF['Balanced_classification_accuracy']),
                float(classified_metric_debiasing_test_TF['Statistical_parity_difference']),
                float(classified_metric_debiasing_test_TF['Equal_opportunity_difference']),
                float(classified_metric_debiasing_test_TF['Average_odds_difference']),
                float(classified_metric_debiasing_test_TF['Theil_index']),
                float(classified_metric_debiasing_test_TF['False_negative_rate_difference'])],
    'Transfer_Learning_Adv': [float(classified_metric_debiasing_test_TF_Ad['Classification_accuracy']),
                float(classified_metric_debiasing_test_TF_Ad['Balanced_classification_accuracy']),
                float(classified_metric_debiasing_test_TF_Ad['Statistical_parity_difference']),
                float(classified_metric_debiasing_test_TF_Ad['Equal_opportunity_difference']),
                float(classified_metric_debiasing_test_TF_Ad['Average_odds_difference']),
                float(classified_metric_debiasing_test_TF_Ad['Theil_index']),
                float(classified_metric_debiasing_test_TF_Ad['False_negative_rate_difference'])]

})

# plotting graphc
print("**********************")
print("after_mitigation :", df1)
df1.to_csv('after_biasmitigation_CNN_TF.csv')
df1.plot(x="Bias_After_Mitigation", kind="bar", )

plt.savefig('Bias_After_Mitigation_CNN_TF.jpg')
print('***** finished ******')
