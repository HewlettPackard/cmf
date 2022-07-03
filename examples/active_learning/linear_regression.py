import torch
from torch.autograd import Variable


class LinearRegressionModel(torch.nn.Module):

	def __init__(self):
		super(LinearRegressionModel, self).__init__()
		self.linear = torch.nn.Linear(1, 1) # One in and one out

	def forward(self, x):
		y_pred = self.linear(x)
		return y_pred

class LinearPredictor:
    def __init__(self, x_data, y_data):
        #print(x_data)
        #print(x_data.reshape(1, len(x_data)).t())
        self.x_data = x_data.reshape(1, len(x_data)).t()
        self.y_data = y_data.reshape(1, len(x_data)).t()
        self.model = LinearRegressionModel()
        self.criterion = torch.nn.MSELoss(size_average = False)
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr = 0.001)

    def train(self):
        for epoch in range(500):

        # Forward pass: Compute predicted y by passing
        # x to the model
            pred_y = self.model(self.x_data)

        # Compute and orrint loss
            loss = self.criterion(pred_y, self.y_data)

        # Zero gradients, perform a backward pass,
        # and update the weights.
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            #print('epoch {}, loss {}'.format(epoch, loss.item()))

# our model
    def predict(self, x_data):
        #new_var = Variable(torch.Tensor([[x_data]]))
        #p = [elem for elem in enumerate(x_data)]
        #print(p)
        pred_y = [ self.model(Variable(torch.Tensor([[elem]]))).item() for index, elem in enumerate(x_data)]

       # pred_y = [ self.model(elem).item() for index, elem in enumerate(x_data)]
        #print("predict (after training)", x_data, pred_y)
        return pred_y
