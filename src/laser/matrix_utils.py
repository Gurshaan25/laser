import torch
import numpy as np
import matplotlib.pyplot as plt


# Helper functions for abs weight pruning
def sorted_mat(matrix):
    temp = list(abs(matrix).flatten())
    temp.sort()
    return temp


def prune(matrix, mat_sort, to_prune):
    if to_prune != 0:
        alpha = mat_sort[int(to_prune * 0.1 * len(mat_sort))]
        matrix[abs(matrix) <= alpha] = 0
    return matrix


def rank(matrix):
    np_matrix = np.array(matrix)
    return np.linalg.matrix_rank(np_matrix)/min(list(np_matrix.shape))


# What percentage can be pruned by weight
def sparsity(matrix, alpha):
    abs_matrix = abs(matrix)
    filtered_matrix = abs_matrix[abs_matrix < alpha]
    return len(filtered_matrix)/matrix.size


def viz_rank_change(rank_list,name):
    fig = plt.figure()
    plt.plot(rank_list)
    plt.savefig(name)


# Helper functions for rank reduction
def do_low_rank(weight, k, debug=False, niter=2):
    assert weight.ndim == 2

    max_rank = min(weight.shape[0], weight.shape[1])
    desired_rank = int(max_rank * k)

    if debug:
        print(f"Shape is {weight.shape} and shape is {weight.dtype} => desired rank {desired_rank}")

    results = torch.svd_lowrank(weight,
                                q=desired_rank,
                                niter=niter)
    weight_approx = results[0] @ torch.diag(results[1]) @ results[2].T

    if debug:
        print(f"New matrix has shape {weight_approx.shape}")

    assert weight_approx.shape[0] == weight.shape[0] and weight_approx.shape[1] == weight.shape[1]
    weight_approx = torch.nn.Parameter(weight_approx)

    return weight_approx

def do_UV_approximation(weight, r, me_lr=0.0001, n_iter=1000):
    assert weight.ndim == 2
    m = weight.shape[0]
    n = weight.shape[1]
    m = int(m)
    r = int(r)
    n = int(n)
    #DEBUG
    print(m)
    print(r)
    print(n)
    U = torch.rand((m, r), dtype=torch.float32) * 2 - 1
    V = torch.rand((r, n), dtype=torch.float32) * 2 - 1
    U.requires_grad_()
    V.requires_grad_()
    for _ in range(n_iter):
        try:
            U.grad = None
            V.grad = None
            loss = torch.sum((torch.matmul(U, V) - weight) ** 2)
            loss.backward()
            with torch.no_grad():
                U -= me_lr * U.grad
                V -= me_lr * V.grad
        except Exception as e:
            print("Error occured: ", e)
            break
    w_approx = torch.matmul(U, V)
    print(torch.sum((w_approx- weight) ** 2))
    return w_approx
