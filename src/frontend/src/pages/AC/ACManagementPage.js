import React, { useState, useEffect, useCallback, useContext } from 'react';
import ACService from '../../services/ACService';
import { AuthContext } from '../../contexts/AuthContext'; // To ensure user is authenticated

const ACManagementPage = () => {
    const [principles, setPrinciples] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [editingPrinciple, setEditingPrinciple] = useState(null); // Principle object or null
    const [isModalOpen, setIsModalOpen] = useState(false);

    const { currentUser } = useContext(AuthContext);

    const fetchPrinciples = useCallback(async () => {
        if (!currentUser) return; // Don't fetch if not logged in
        setIsLoading(true);
        setError('');
        try {
            const data = await ACService.getPrinciples();
            setPrinciples(data.principles || []); // ACService returns { principles: [], total: N }
        } catch (err) {
            setError(err.message || 'Failed to fetch principles.');
        } finally {
            setIsLoading(false);
        }
    }, [currentUser]);

    useEffect(() => {
        fetchPrinciples();
    }, [fetchPrinciples]);

    const handleEdit = (principle) => {
        setEditingPrinciple(principle);
        setIsModalOpen(true);
    };

    const handleCreateNew = () => {
        setEditingPrinciple({ name: '', description: '', content: '', status: 'draft' }); // Fresh object
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this principle?')) {
            setIsLoading(true);
            try {
                await ACService.deletePrinciple(id);
                alert('Principle deleted successfully');
                fetchPrinciples(); // Refresh list
            } catch (err) {
                setError(err.message || 'Failed to delete principle.');
            } finally {
                setIsLoading(false);
            }
        }
    };

    const handleModalClose = () => {
        setIsModalOpen(false);
        setEditingPrinciple(null);
    };

    const handleModalSave = async (updatedPrinciple) => {
        setIsLoading(true);
        setError('');
        try {
            if (updatedPrinciple.id) { // Editing existing
                await ACService.updatePrinciple(updatedPrinciple.id, updatedPrinciple);
                alert('Principle updated successfully');
            } else { // Creating new
                await ACService.createPrinciple(updatedPrinciple);
                alert('Principle created successfully');
            }
            handleModalClose();
            fetchPrinciples(); // Refresh list
        } catch (err) {
            setError(err.message || 'Failed to save principle.');
            // Keep modal open if save fails so user can see error and try again
        } finally {
            setIsLoading(false);
        }
    };


    if (!currentUser) {
        return <p>Please login to manage AC principles.</p>;
    }
    if (isLoading && !principles.length) { // Show loading only on initial load
        return <p>Loading principles...</p>;
    }
    if (error && !isModalOpen) { // Don't show page-level error if modal has its own
        return <p style={{ color: 'red' }}>{error}</p>;
    }

    return (
        <div>
            <h2>Artificial Constitution Management</h2>
            <button onClick={handleCreateNew} disabled={isLoading}>Create New Principle</button>
            {isLoading && <p>Processing...</p>}
            
            {principles.length === 0 && !isLoading && <p>No principles found.</p>}
            
            <ul style={{ listStyleType: 'none', padding: 0 }}>
                {principles.map(p => (
                    <li key={p.id} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
                        <h3>{p.name} (ID: {p.id}, V{p.version})</h3>
                        <p><strong>Status:</strong> {p.status}</p>
                        <p><strong>Description:</strong> {p.description || 'N/A'}</p>
                        <p><strong>Content:</strong> <pre style={{ whiteSpace: 'pre-wrap', background: '#f4f4f4', padding: '5px' }}>{p.content}</pre></p>
                        <p><small>Created: {new Date(p.created_at).toLocaleString()}</small></p>
                        <p><small>Updated: {new Date(p.updated_at).toLocaleString()}</small></p>
                        <button onClick={() => handleEdit(p)} disabled={isLoading}>Edit</button>
                        <button onClick={() => handleDelete(p.id)} disabled={isLoading} style={{ marginLeft: '10px' }}>Delete</button>
                    </li>
                ))}
            </ul>

            {isModalOpen && editingPrinciple && (
                <PrincipleEditModal
                    principle={editingPrinciple}
                    onSave={handleModalSave}
                    onClose={handleModalClose}
                    error={error} // Pass error to modal
                    isLoading={isLoading}
                />
            )}
        </div>
    );
};

// Simple Modal Component (can be moved to components/ later)
const PrincipleEditModal = ({ principle, onSave, onClose, error, isLoading }) => {
    const [formData, setFormData] = useState({ ...principle });

    useEffect(() => {
        setFormData({ ...principle }); // Reset form data if principle prop changes
    }, [principle]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave(formData);
    };

    return (
        <div style={{
            position: 'fixed', top: '20%', left: '50%', transform: 'translate(-50%, -20%)',
            backgroundColor: 'white', padding: '20px', zIndex: 100, border: '1px solid black',
            width: '80%', maxWidth: '600px', maxHeight: '80vh', overflowY: 'auto'
        }}>
            <h3>{formData.id ? 'Edit Principle' : 'Create New Principle'}</h3>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Name:</label>
                    <input type="text" name="name" value={formData.name} onChange={handleChange} required />
                </div>
                <div>
                    <label>Description:</label>
                    <textarea name="description" value={formData.description || ''} onChange={handleChange} rows="3" />
                </div>
                <div>
                    <label>Content:</label>
                    <textarea name="content" value={formData.content} onChange={handleChange} rows="5" required />
                </div>
                <div>
                    <label>Status:</label>
                    <select name="status" value={formData.status} onChange={handleChange}>
                        <option value="draft">Draft</option>
                        <option value="approved">Approved</option>
                        <option value="deprecated">Deprecated</option>
                    </select>
                </div>
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <button type="submit" disabled={isLoading}>{isLoading ? 'Saving...' : 'Save'}</button>
                <button type="button" onClick={onClose} disabled={isLoading} style={{ marginLeft: '10px' }}>Cancel</button>
            </form>
        </div>
    );
};

export default ACManagementPage;
