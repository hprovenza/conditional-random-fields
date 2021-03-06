import numpy as np
from math import exp
import scipy.misc

class CRF(object):

    def __init__(self, label_codebook, feature_codebook):
        self.label_codebook = label_codebook
        self.feature_codebook = feature_codebook
        num_labels = len(self.label_codebook)
        num_features = len(self.feature_codebook)
        self.feature_parameters = np.zeros((num_labels, num_features))
        self.transition_parameters = np.zeros((num_labels, num_labels))

    def train(self, training_set, dev_set):
        """Training function

        Feel free to adjust the hyperparameters (learning rate and batch sizes)
        """
        self.train_sgd(training_set, dev_set, 0.01, 200)

    def train_sgd(self, training_set, dev_set, learning_rate, batch_size):
        """Minibatch SGF for training linear chain CRF

        This should work. But you can also implement early stopping here
        i.e. if the accuracy does not grow for a while, stop.
        """
        num_labels = len(self.label_codebook)
        num_features = len(self.feature_codebook)
        num_batches = len(training_set) / batch_size
        total_expected_feature_count = np.zeros((num_labels, num_features))
        total_expected_transition_count = np.zeros((num_labels, num_labels))
        print 'With all parameters = 0, the accuracy is %s' % \
                sequence_accuracy(self, dev_set)
        for i in range(10):
            for j in range(num_batches):
                batch = training_set[j*batch_size:(j+1)*batch_size]
                total_expected_feature_count.fill(0)
                total_expected_transition_count.fill(0)
                total_observed_feature_count, total_observed_transition_count = self.compute_observed_count(batch)
                
                for sequence in batch:
                    transition_matrices = self.compute_transition_matrices(sequence)
                    alpha_matrix = self.forward(sequence, transition_matrices)
                    beta_matrix = self.backward(sequence, transition_matrices)
                    expected_feature_count, expected_transition_count = \
                            self.compute_expected_feature_count(sequence, alpha_matrix, beta_matrix, transition_matrices)
                    total_expected_feature_count += expected_feature_count
                    total_expected_transition_count += expected_transition_count

                feature_gradient = (total_observed_feature_count - total_expected_feature_count) / len(batch)
                transition_gradient = (total_observed_transition_count - total_expected_transition_count) / len(batch)

                self.feature_parameters += learning_rate * feature_gradient
                self.transition_parameters += learning_rate * transition_gradient
                print sequence_accuracy(self, dev_set)

    def compute_transition_matrices(self, sequence):
        """Compute transition matrices (denoted as M on the slides)

        Compute transition matrix M for all time steps.

        We add one extra dummy transition matrix at time 0. 
        This one dummy transition matrix should not be used ever, but it 
        is there to make the index consistent with the slides

        The matrix for the first time step does not use transition features
        and should be a diagonal matrix.

        Returns :
            a list of transition matrices
        """
        #TODO: Implement this function
        transition_matrices = []
        num_labels = len(self.label_codebook)

        #dummy matrix as t=0 placeholder
        transition_matrix = np.zeros((num_labels, num_labels))
        transition_matrices.append(transition_matrix)

        # diagonal matrix for first time step
        transition_matrix = np.zeros((num_labels, num_labels))
        for s in range(num_labels):
            w = sum([self.feature_parameters[s][self.feature_codebook[f]] for f in \
                     sequence[0].sequence_features(0, sequence)])
            transition_matrix[s][s] = np.exp(w)
        transition_matrices.append(transition_matrix)

        # filling in the rest of the matrix
        for t in range(1, len(sequence)):
            transition_matrix = np.zeros((num_labels, num_labels))
            for s in range(num_labels):
                for _s in range(num_labels):
                    transition_matrix[_s][s] = self.compute_transition_matrix_value(_s, s, sequence, t)
            transition_matrices.append(transition_matrix)
        return transition_matrices

    def compute_transition_matrix_value(self, _s, s, sequence, t):
        lam_state = self.transition_parameters[_s][s]
        lam_feat = sum([self.feature_parameters[_s][self.feature_codebook[f]] for f in sequence[t].sequence_features(t, sequence)])
        return exp(lam_feat + lam_state)

    def forward(self, sequence, transition_matrices):
        """Compute alpha matrix in the forward algorithm
        """
        #TODO: Implement this function
        num_labels = len(self.label_codebook)
        alpha_matrix = np.zeros((num_labels, len(sequence) + 1))

        #initialization step
        for s in range(num_labels):
            alpha_matrix[s][0] = 1

        #recursion step
        for t in range(1, len(sequence)+1):
            for s in range(num_labels):
                k = sum([transition_matrices[t][x][s] * alpha_matrix[x][t-1] for x in range(num_labels)])

                alpha_matrix[s][t] = k
        return alpha_matrix

    def backward(self, sequence, transition_matrices):
        """Compute beta matrix in the backward algorithm

        TODO: Implement this function
        """
        #TODO: Implement this function
        num_labels = len(self.label_codebook)
        beta_matrix = np.zeros((num_labels, len(sequence) + 1))
        time = range(len(sequence))
        time.reverse()
        #initialization step
        for s in range(num_labels):
            beta_matrix[s][len(sequence)] = 1
        #recursion step
        for t in time:
            for s in range(num_labels):
                k = sum([transition_matrices[t+1][s][x] * beta_matrix[x][t+1] for x in range(num_labels)])
                beta_matrix[s][t] = k
        return beta_matrix

    def decode(self, sequence):
        """Find the best label sequence from the feature sequence

        TODO: Implement this function

        Returns :
            a list of label indices (the same length as the sequence)
        """
        #TODO: Implement this function

        transition_matrices = self.compute_transition_matrices(sequence)
        time = range(len(sequence))
        decoded_sequence = []
        alpha = self.forward(sequence, transition_matrices)
        beta = self.backward(sequence, transition_matrices)
        num_labels = len(transition_matrices[0])
        f = lambda i: (alpha[i][t]*beta[i][t])/sum([alpha[k][t]*beta[k][t] for k in range(num_labels)])
        for t in time:
            decoded_sequence.append(max([s for s in range(num_labels)], key=f))
        return decoded_sequence

    def compute_observed_count(self, sequences):
        """Compute observed counts of features from the minibatch

        This is implemented for you.

        Returns :
            A tuple of
                a matrix of feature counts 
                a matrix of transition-based feature counts
        """
        num_labels = len(self.label_codebook)
        num_features = len(self.feature_codebook)

        feature_count = np.zeros((num_labels, num_features))
        transition_count = np.zeros((num_labels, num_labels))
        for sequence in sequences:
            for t in range(len(sequence)):
                if t > 0:
                    transition_count[sequence[t-1].label_index, sequence[t].label_index] += 1
                feature_count[sequence[t].label_index, sequence[t].feature_vector] += 1
        return feature_count, transition_count

    def compute_expected_feature_count(self, sequence, 
            alpha_matrix, beta_matrix, transition_matrices):
        """Compute expected counts of features from the sequence

        This is implemented for you.

        Returns :
            A tuple of
                a matrix of feature counts 
                a matrix of transition-based feature counts
        """
        num_labels = len(self.label_codebook)
        num_features = len(self.feature_codebook)

        feature_count = np.zeros((num_labels, num_features))
        sequence_length = len(sequence)
        Z = np.sum(alpha_matrix[:,-1])

        #gamma = alpha_matrix * beta_matrix / Z 
        gamma = np.exp(np.log(alpha_matrix) + np.log(beta_matrix) - np.log(Z))
        for t in range(sequence_length):
            for j in range(num_labels):
                feature_count[j, sequence[t].feature_vector] += gamma[j, t]

        transition_count = np.zeros((num_labels, num_labels))
        for t in range(sequence_length - 1):
            transition_count += (transition_matrices[t] * np.outer(alpha_matrix[:, t], beta_matrix[:,t+1])) / Z
        return feature_count, transition_count

def sequence_accuracy(sequence_tagger, test_set):
    correct = 0.0
    total = 0.0
    for sequence in test_set:
        decoded = sequence_tagger.decode(sequence)
        assert(len(decoded) == len(sequence))
        total += len(decoded)
        for i, instance in enumerate(sequence):
            if instance.label_index == decoded[i]:
                correct += 1
    return correct / total


