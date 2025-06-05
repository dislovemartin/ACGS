import pytest
import numpy as np
from src.backend.gs_service.app.wina.svd_utils import (
    perform_svd,
    reconstruct_from_svd,
    apply_svd_transformation,
    get_svd_reduced_components
)

class TestSVDUtils:
    @pytest.fixture
    def sample_matrix(self):
        # A simple, non-square matrix for testing
        return np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], dtype=float)

    @pytest.fixture
    def square_matrix(self):
        return np.array([[1, 2], [3, 4]], dtype=float)

    def test_perform_svd(self, sample_matrix):
        U, s, Vh = perform_svd(sample_matrix)
        
        assert U.shape == (sample_matrix.shape[0], min(sample_matrix.shape))
        assert s.ndim == 1
        assert len(s) == min(sample_matrix.shape)
        assert Vh.shape == (min(sample_matrix.shape), sample_matrix.shape[1])
        
        # Check if singular values are sorted in descending order
        assert np.all(s[:-1] >= s[1:])
        
        # Check orthogonality of U and Vh (for full_matrices=False, U and Vh might not be square)
        # For U (columns are orthonormal)
        assert np.allclose(U.T @ U, np.eye(U.shape[1]))
        # For Vh (rows are orthonormal, so Vh @ Vh.T should be identity)
        assert np.allclose(Vh @ Vh.T, np.eye(Vh.shape[0]))


    def test_perform_svd_invalid_input(self):
        with pytest.raises(TypeError):
            perform_svd("not a matrix")
        with pytest.raises(ValueError):
            perform_svd(np.array([1, 2, 3])) # 1D array

    def test_reconstruct_from_svd_full(self, sample_matrix):
        U, s, Vh = perform_svd(sample_matrix)
        reconstructed = reconstruct_from_svd(U, s, Vh)
        assert np.allclose(sample_matrix, reconstructed)

    def test_reconstruct_from_svd_reduced(self, sample_matrix):
        U, s, Vh = perform_svd(sample_matrix)
        k = 2
        reconstructed_reduced = reconstruct_from_svd(U, s, Vh, k=k)
        
        assert reconstructed_reduced.shape == sample_matrix.shape
        # The reconstructed matrix with fewer components won't be exactly equal,
        # but it should be the best rank-k approximation.
        # A full check of approximation quality is complex, here we just check shape
        # and that it's different from the original if k < rank.
        if k < len(s):
             assert not np.allclose(sample_matrix, reconstructed_reduced)

    def test_reconstruct_from_svd_invalid_k(self, sample_matrix):
        U, s, Vh = perform_svd(sample_matrix)
        with pytest.raises(ValueError):
            reconstruct_from_svd(U, s, Vh, k=0)
        with pytest.raises(ValueError):
            reconstruct_from_svd(U, s, Vh, k=-1)
        with pytest.raises(ValueError):
            reconstruct_from_svd(U, s, Vh, k=len(s) + 1)
        with pytest.raises(ValueError):
            reconstruct_from_svd(U, s, Vh, k="invalid")


    def test_apply_svd_transformation(self, sample_matrix):
        k = 2
        transformed_matrix = apply_svd_transformation(sample_matrix, k=k)
        assert transformed_matrix.shape == sample_matrix.shape
        
        # Verify it's a rank-k approximation
        U, s, Vh = perform_svd(sample_matrix)
        expected_reconstruction = reconstruct_from_svd(U, s, Vh, k=k)
        assert np.allclose(transformed_matrix, expected_reconstruction)

    def test_apply_svd_transformation_invalid_input(self):
        with pytest.raises(TypeError):
            apply_svd_transformation("not a matrix", k=1)
        with pytest.raises(ValueError):
            apply_svd_transformation(np.array([1,2,3]), k=1) # 1D array

    def test_apply_svd_transformation_invalid_k(self, sample_matrix):
        with pytest.raises(ValueError):
            apply_svd_transformation(sample_matrix, k=0)
        with pytest.raises(ValueError):
            apply_svd_transformation(sample_matrix, k=-1)
        with pytest.raises(ValueError): # k > min(matrix.shape)
            apply_svd_transformation(sample_matrix, k=min(sample_matrix.shape) + 1)
        with pytest.raises(ValueError):
            apply_svd_transformation(sample_matrix, k="invalid")


    def test_get_svd_reduced_components(self, sample_matrix):
        k = 2
        U_k, s_k, Vh_k = get_svd_reduced_components(sample_matrix, k=k)
        
        assert U_k.shape == (sample_matrix.shape[0], k)
        assert s_k.shape == (k,)
        assert Vh_k.shape == (k, sample_matrix.shape[1])

        # Check if s_k contains the top k singular values from original s
        _, s_full, _ = perform_svd(sample_matrix)
        assert np.allclose(s_k, s_full[:k])

    def test_get_svd_reduced_components_invalid_input(self):
        with pytest.raises(TypeError):
            get_svd_reduced_components("not a matrix", k=1)
        with pytest.raises(ValueError):
            get_svd_reduced_components(np.array([1,2,3]), k=1)

    def test_get_svd_reduced_components_invalid_k(self, sample_matrix):
        with pytest.raises(ValueError):
            get_svd_reduced_components(sample_matrix, k=0)
        with pytest.raises(ValueError):
            get_svd_reduced_components(sample_matrix, k=-1)
        with pytest.raises(ValueError):
            get_svd_reduced_components(sample_matrix, k=min(sample_matrix.shape) + 1)
        with pytest.raises(ValueError):
            get_svd_reduced_components(sample_matrix, k="invalid_type")

    def test_svd_on_rank_deficient_matrix(self):
        # Create a rank-deficient matrix
        A = np.array([[1, 2, 3], [2, 4, 6], [3, 6, 9]]) # Rank 1
        U, s, Vh = perform_svd(A)
        
        # Number of non-zero singular values should be the rank
        rank = np.sum(s > 1e-9) # Using a tolerance for floating point
        assert rank == 1
        
        reconstructed = reconstruct_from_svd(U, s, Vh)
        assert np.allclose(A, reconstructed)

        # Test reduction
        k = 1 # Should be able to reconstruct perfectly with k=rank
        reconstructed_k1 = reconstruct_from_svd(U, s, Vh, k=k)
        assert np.allclose(A, reconstructed_k1)

        # Test get_svd_reduced_components
        U_k, s_k, Vh_k = get_svd_reduced_components(A, k=1)
        assert U_k.shape == (A.shape[0], 1)
        assert s_k.shape == (1,)
        assert Vh_k.shape == (1, A.shape[1])
        assert np.allclose(s_k[0], s[0])

    def test_svd_on_identity_matrix(self, square_matrix):
        I = np.eye(3)
        U, s, Vh = perform_svd(I)
        assert np.allclose(s, np.ones(3)) # Singular values of identity are all 1
        reconstructed = reconstruct_from_svd(U, s, Vh)
        assert np.allclose(I, reconstructed)

        k = 2
        reconstructed_k = reconstruct_from_svd(U, s, Vh, k=k)
        # Reconstructing identity with fewer components will not be identity
        assert not np.allclose(I, reconstructed_k)
        assert reconstructed_k.shape == I.shape

        U_k, s_k, Vh_k = get_svd_reduced_components(I, k=k)
        assert np.allclose(s_k, np.ones(k))