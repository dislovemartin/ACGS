import numpy as np
from typing import Tuple

def perform_svd(matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Performs Singular Value Decomposition (SVD) on a given matrix.

    Args:
        matrix: The input matrix (NumPy array) for SVD.

    Returns:
        A tuple (U, s, Vh) where:
            U: Unitary matrix having left singular vectors as columns.
            s: The singular values, sorted in non-increasing order.
            Vh: Unitary matrix having right singular vectors as rows.
    """
    if not isinstance(matrix, np.ndarray):
        raise TypeError("Input matrix must be a NumPy array.")
    if matrix.ndim != 2:
        raise ValueError("Input matrix must be 2-dimensional.")

    U, s, Vh = np.linalg.svd(matrix, full_matrices=False)
    return U, s, Vh

def reconstruct_from_svd(U: np.ndarray, s: np.ndarray, Vh: np.ndarray, k: int = None) -> np.ndarray:
    """
    Reconstructs a matrix from its SVD components, optionally reducing dimensionality.

    Args:
        U: Unitary matrix having left singular vectors as columns.
        s: The singular values.
        Vh: Unitary matrix having right singular vectors as rows.
        k: The number of singular values/vectors to use for reconstruction.
           If None, all components are used.

    Returns:
        The reconstructed matrix (NumPy array).
    """
    if k is None:
        k = len(s)
    elif not isinstance(k, int) or k <= 0:
        raise ValueError("Number of components k must be a positive integer.")
    elif k > len(s):
        raise ValueError(f"Number of components k ({k}) cannot exceed the number of singular values ({len(s)}).")

    # Create a diagonal matrix from the top k singular values
    Sigma_k = np.diag(s[:k])
    
    # Select the top k singular vectors
    U_k = U[:, :k]
    Vh_k = Vh[:k, :]
    
    # Reconstruct the matrix
    reconstructed_matrix = U_k @ Sigma_k @ Vh_k
    return reconstructed_matrix

def apply_svd_transformation(matrix: np.ndarray, k: int) -> np.ndarray:
    """
    Applies SVD-based transformation for dimensionality reduction.

    This function performs SVD on the input matrix and then reconstructs
    it using the top k singular values/vectors, effectively reducing
    its dimensionality while preserving the most significant information.

    Args:
        matrix: The input matrix (e.g., W_k, W_gate) to transform.
        k: The number of singular values/vectors to retain (target dimensionality).

    Returns:
        The transformed matrix with reduced dimensionality.
    """
    if not isinstance(matrix, np.ndarray):
        raise TypeError("Input matrix must be a NumPy array.")
    if matrix.ndim != 2:
        raise ValueError("Input matrix must be 2-dimensional.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("Number of components k must be a positive integer.")
    if k > min(matrix.shape):
         raise ValueError(f"Number of components k ({k}) cannot exceed the smallest dimension of the matrix ({min(matrix.shape)}).")


    U, s, Vh = perform_svd(matrix)
    
    # The "transformed" matrix in this context is the reconstruction using top k components.
    # Alternatively, one might return U_k, Sigma_k, Vh_k or just U_k @ Sigma_k if the goal
    # is to get a lower-dimensional representation rather than a full reconstruction.
    # For WINA, a common approach is to use the reduced U, S, V to form new, smaller weight matrices.
    # For now, we return the reconstructed matrix of the same original shape but lower rank.
    # The actual application (e.g., replacing original weights or using components)
    # will depend on how WINA integrates this.
    
    transformed_matrix = reconstruct_from_svd(U, s, Vh, k)
    return transformed_matrix

# Placeholder for a function that might return the components for further use
def get_svd_reduced_components(matrix: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Performs SVD and returns the top k components (U_k, s_k, Vh_k).

    Args:
        matrix: The input matrix.
        k: The number of components to select.

    Returns:
        A tuple (U_k, s_k, Vh_k) representing the reduced SVD components.
        s_k is a 1D array of the top k singular values.
    """
    if not isinstance(matrix, np.ndarray):
        raise TypeError("Input matrix must be a NumPy array.")
    if matrix.ndim != 2:
        raise ValueError("Input matrix must be 2-dimensional.")
    if not isinstance(k, int) or k <= 0:
        raise ValueError("Number of components k must be a positive integer.")
    if k > min(matrix.shape):
         raise ValueError(f"Number of components k ({k}) cannot exceed the smallest dimension of the matrix ({min(matrix.shape)}).")

    U, s, Vh = perform_svd(matrix)
    
    U_k = U[:, :k]
    s_k = s[:k] # s is already 1D
    Vh_k = Vh[:k, :]
    
    return U_k, s_k, Vh_k