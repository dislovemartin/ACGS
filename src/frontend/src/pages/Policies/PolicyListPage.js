import React, { useState, useEffect, useCallback, useContext } from 'react';
import IntegrityService from '../../services/IntegrityService';
import { AuthContext } from '../../contexts/AuthContext';

const PolicyListPage = () => {
    const [policies, setPolicies] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [filterStatus, setFilterStatus] = useState(''); // '', 'verified', 'pending', 'failed'
    const { currentUser } = useContext(AuthContext);

    const fetchPolicies = useCallback(async () => {
        if (!currentUser) return;
        setIsLoading(true);
        setError('');
        try {
            const data = await IntegrityService.getPolicies(filterStatus || null); // Pass null if no filter
            setPolicies(data.rules || []); // IntegrityService returns { rules: [], total: N }
        } catch (err) {
            setError(err.message || 'Failed to fetch policies.');
        } finally {
            setIsLoading(false);
        }
    }, [currentUser, filterStatus]);

    useEffect(() => {
        fetchPolicies();
    }, [fetchPolicies]);

    const handleFilterChange = (e) => {
        setFilterStatus(e.target.value);
    };
    
    const getStatusColor = (status) => {
        switch (status) {
            case 'verified': return 'green';
            case 'failed': return 'red';
            case 'pending': return 'orange';
            default: return 'black';
        }
    };

    if (!currentUser) {
        return <p>Please login to view policies.</p>;
    }
    if (isLoading && !policies.length) {
        return <p>Loading policies...</p>;
    }
    
    return (
        <div>
            <h2>Policy List</h2>
            
            <div>
                <label htmlFor="statusFilter">Filter by verification status: </label>
                <select id="statusFilter" value={filterStatus} onChange={handleFilterChange}>
                    <option value="">All</option>
                    <option value="verified">Verified</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                </select>
                <button onClick={fetchPolicies} disabled={isLoading} style={{ marginLeft: '10px' }}>Refresh</button>
            </div>

            {isLoading && <p>Loading...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}
            
            {policies.length === 0 && !isLoading && <p>No policies found for the selected filter.</p>}
            
            <ul style={{ listStyleType: 'none', padding: 0 }}>
                {policies.map(policy => (
                    <li key={policy.id} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
                        <h3>Policy ID: {policy.id} (V{policy.version})</h3>
                        <p>
                            <strong>Status:</strong> 
                            <span style={{ color: getStatusColor(policy.verification_status), fontWeight: 'bold', marginLeft: '5px' }}>
                                {policy.verification_status.toUpperCase()}
                            </span>
                        </p>
                        <p><strong>Source Principle IDs:</strong> {policy.source_principle_ids ? policy.source_principle_ids.join(', ') : 'N/A'}</p>
                        <div>
                            <strong>Content:</strong>
                            <pre style={{ whiteSpace: 'pre-wrap', background: '#f4f4f4', padding: '5px', border: '1px solid #eee' }}>
                                {policy.rule_content}
                            </pre>
                        </div>
                        <p><small>Created: {new Date(policy.created_at).toLocaleString()}</small></p>
                        <p><small>Updated: {new Date(policy.updated_at).toLocaleString()}</small></p>
                        {policy.verified_at && <p><small>Verified At: {new Date(policy.verified_at).toLocaleString()}</small></p>}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default PolicyListPage;
