/**
 * Test suite for PublicConsultationPage React component
 * 
 * Tests the complete public consultation interface including:
 * - Component rendering and navigation
 * - Proposal submission and display
 * - Feedback collection and submission
 * - Transparency dashboard functionality
 * - Anonymous and authenticated user interactions
 * - Integration with PublicConsultationService
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import PublicConsultationPage from '../../src/pages/PublicConsultation/PublicConsultationPage';
import PublicConsultationService from '../../src/services/PublicConsultationService';

// Mock the PublicConsultationService
jest.mock('../../src/services/PublicConsultationService');

// Mock data
const mockProposals = [
    {
        id: 1,
        title: "Enhanced Privacy Protection",
        description: "Strengthen privacy protections for citizens in AI governance systems.",
        proposed_changes: "Add explicit consent requirements for data processing.",
        justification: "Current privacy protections are insufficient.",
        submitter_name: "Test Citizen",
        submitter_organization: "Privacy Advocacy Group",
        stakeholder_group: "citizen",
        status: "open",
        created_at: "2024-01-15T10:00:00Z",
        consultation_period_days: 30,
        public_support_count: 75,
        requires_review: false
    },
    {
        id: 2,
        title: "AI Transparency Requirements",
        description: "Mandate transparency in AI decision-making processes.",
        proposed_changes: "Require explainable AI for all governance decisions.",
        justification: "Citizens need to understand how AI affects them.",
        submitter_name: "Dr. AI Expert",
        submitter_organization: "AI Ethics Institute",
        stakeholder_group: "expert",
        status: "review",
        created_at: "2024-01-10T14:30:00Z",
        consultation_period_days: 30,
        public_support_count: 120,
        requires_review: true
    }
];

const mockMetrics = {
    total_proposals: 15,
    active_consultations: 8,
    total_participants: 1250,
    feedback_count: 3400,
    sentiment_distribution: {
        support: 45,
        oppose: 20,
        neutral: 25,
        suggestion: 10
    },
    stakeholder_participation: {
        citizen: 60,
        expert: 25,
        civil_society: 15
    },
    engagement_rate: 0.68,
    completion_rate: 0.82,
    time_period_days: 30
};

// Helper function to render component with router
const renderWithRouter = (component) => {
    return render(
        <BrowserRouter>
            {component}
        </BrowserRouter>
    );
};

describe('PublicConsultationPage', () => {
    beforeEach(() => {
        // Reset all mocks before each test
        jest.clearAllMocks();
        
        // Setup default mock implementations
        PublicConsultationService.getProposals.mockResolvedValue(mockProposals);
        PublicConsultationService.getMetrics.mockResolvedValue(mockMetrics);
        PublicConsultationService.submitProposal.mockResolvedValue({ id: 3, success: true });
        PublicConsultationService.submitFeedback.mockResolvedValue({ id: 1, success: true });
    });

    describe('Component Rendering', () => {
        test('renders main page elements', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Check main heading
            expect(screen.getByText('Public Consultation')).toBeInTheDocument();
            expect(screen.getByText('Participate in constitutional governance through democratic consultation')).toBeInTheDocument();
            
            // Check tab navigation
            expect(screen.getByText('Proposals')).toBeInTheDocument();
            expect(screen.getByText('Submit Feedback')).toBeInTheDocument();
            expect(screen.getByText('Transparency Dashboard')).toBeInTheDocument();
        });

        test('loads and displays proposals on mount', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Wait for proposals to load
            await waitFor(() => {
                expect(screen.getByText('Enhanced Privacy Protection')).toBeInTheDocument();
                expect(screen.getByText('AI Transparency Requirements')).toBeInTheDocument();
            });
            
            // Verify service was called
            expect(PublicConsultationService.getProposals).toHaveBeenCalledTimes(1);
            expect(PublicConsultationService.getMetrics).toHaveBeenCalledTimes(1);
        });

        test('displays loading state initially', () => {
            // Mock delayed response
            PublicConsultationService.getProposals.mockImplementation(
                () => new Promise(resolve => setTimeout(() => resolve(mockProposals), 100))
            );
            
            renderWithRouter(<PublicConsultationPage />);
            
            // Should show loading state
            expect(screen.getByText(/loading/i)).toBeInTheDocument();
        });
    });

    describe('Tab Navigation', () => {
        test('switches between tabs correctly', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Wait for initial load
            await waitFor(() => {
                expect(screen.getByText('Enhanced Privacy Protection')).toBeInTheDocument();
            });
            
            // Switch to feedback tab
            fireEvent.click(screen.getByText('Submit Feedback'));
            expect(screen.getByText('Submit Public Feedback')).toBeInTheDocument();
            
            // Switch to transparency tab
            fireEvent.click(screen.getByText('Transparency Dashboard'));
            expect(screen.getByText('Consultation Transparency')).toBeInTheDocument();
            
            // Switch back to proposals
            fireEvent.click(screen.getByText('Proposals'));
            expect(screen.getByText('Enhanced Privacy Protection')).toBeInTheDocument();
        });
    });

    describe('Proposal Submission', () => {
        test('opens proposal form when submit button clicked', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Wait for proposals to load
            await waitFor(() => {
                expect(screen.getByText('Submit New Proposal')).toBeInTheDocument();
            });
            
            // Click submit new proposal button
            fireEvent.click(screen.getByText('Submit New Proposal'));
            
            // Check form elements appear
            expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/proposed changes/i)).toBeInTheDocument();
        });

        test('submits proposal form with valid data', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Wait for load and open form
            await waitFor(() => {
                fireEvent.click(screen.getByText('Submit New Proposal'));
            });
            
            // Fill out form
            fireEvent.change(screen.getByLabelText(/title/i), {
                target: { value: 'Test Proposal Title' }
            });
            fireEvent.change(screen.getByLabelText(/description/i), {
                target: { value: 'Test proposal description' }
            });
            fireEvent.change(screen.getByLabelText(/proposed changes/i), {
                target: { value: 'Test proposed changes' }
            });
            fireEvent.change(screen.getByLabelText(/justification/i), {
                target: { value: 'Test justification' }
            });
            
            // Submit form
            fireEvent.click(screen.getByText('Submit Proposal'));
            
            // Verify service was called
            await waitFor(() => {
                expect(PublicConsultationService.submitProposal).toHaveBeenCalledWith(
                    expect.objectContaining({
                        title: 'Test Proposal Title',
                        description: 'Test proposal description',
                        proposed_changes: 'Test proposed changes',
                        justification: 'Test justification'
                    })
                );
            });
        });
    });

    describe('Feedback Submission', () => {
        test('switches to feedback tab when provide feedback clicked', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Wait for proposals to load
            await waitFor(() => {
                expect(screen.getByText('Enhanced Privacy Protection')).toBeInTheDocument();
            });
            
            // Click provide feedback button on first proposal
            const feedbackButtons = screen.getAllByText('Provide Feedback');
            fireEvent.click(feedbackButtons[0]);
            
            // Should switch to feedback tab
            expect(screen.getByText('Submit Public Feedback')).toBeInTheDocument();
        });

        test('submits feedback with valid data', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Switch to feedback tab
            fireEvent.click(screen.getByText('Submit Feedback'));
            
            // Fill out feedback form
            const contentTextarea = screen.getByLabelText(/feedback content/i);
            fireEvent.change(contentTextarea, {
                target: { value: 'This is my test feedback' }
            });
            
            const nameInput = screen.getByLabelText(/your name/i);
            fireEvent.change(nameInput, {
                target: { value: 'Test User' }
            });
            
            // Submit feedback
            fireEvent.click(screen.getByText('Submit Feedback'));
            
            // Verify service was called
            await waitFor(() => {
                expect(PublicConsultationService.submitFeedback).toHaveBeenCalledWith(
                    expect.objectContaining({
                        content: 'This is my test feedback',
                        submitter_name: 'Test User'
                    })
                );
            });
        });

        test('allows anonymous feedback submission', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Switch to feedback tab
            fireEvent.click(screen.getByText('Submit Feedback'));
            
            // Fill out only content (no name for anonymous)
            const contentTextarea = screen.getByLabelText(/feedback content/i);
            fireEvent.change(contentTextarea, {
                target: { value: 'Anonymous feedback content' }
            });
            
            // Submit feedback without name
            fireEvent.click(screen.getByText('Submit Feedback'));
            
            // Verify service was called with anonymous data
            await waitFor(() => {
                expect(PublicConsultationService.submitFeedback).toHaveBeenCalledWith(
                    expect.objectContaining({
                        content: 'Anonymous feedback content',
                        submitter_name: ''
                    })
                );
            });
        });
    });

    describe('Transparency Dashboard', () => {
        test('displays metrics correctly', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Switch to transparency tab
            fireEvent.click(screen.getByText('Transparency Dashboard'));
            
            // Wait for metrics to load and display
            await waitFor(() => {
                expect(screen.getByText('15')).toBeInTheDocument(); // total_proposals
                expect(screen.getByText('8')).toBeInTheDocument();  // active_consultations
                expect(screen.getByText('1,250')).toBeInTheDocument(); // total_participants
                expect(screen.getByText('3,400')).toBeInTheDocument(); // feedback_count
            });
        });

        test('displays sentiment distribution', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Switch to transparency tab
            fireEvent.click(screen.getByText('Transparency Dashboard'));
            
            // Check sentiment percentages
            await waitFor(() => {
                expect(screen.getByText('45%')).toBeInTheDocument(); // support
                expect(screen.getByText('20%')).toBeInTheDocument(); // oppose
                expect(screen.getByText('25%')).toBeInTheDocument(); // neutral
                expect(screen.getByText('10%')).toBeInTheDocument(); // suggestion
            });
        });
    });

    describe('Error Handling', () => {
        test('displays error message when proposals fail to load', async () => {
            // Mock service to reject
            PublicConsultationService.getProposals.mockRejectedValue(new Error('Network error'));
            
            renderWithRouter(<PublicConsultationPage />);
            
            // Wait for error to appear
            await waitFor(() => {
                expect(screen.getByText(/failed to load proposals/i)).toBeInTheDocument();
            });
        });

        test('displays error message when proposal submission fails', async () => {
            // Mock service to reject
            PublicConsultationService.submitProposal.mockRejectedValue(new Error('Submission failed'));
            
            renderWithRouter(<PublicConsultationPage />);
            
            // Open form and submit
            await waitFor(() => {
                fireEvent.click(screen.getByText('Submit New Proposal'));
            });
            
            // Fill minimal form data
            fireEvent.change(screen.getByLabelText(/title/i), {
                target: { value: 'Test' }
            });
            
            fireEvent.click(screen.getByText('Submit Proposal'));
            
            // Wait for error message
            await waitFor(() => {
                expect(screen.getByText(/failed to submit proposal/i)).toBeInTheDocument();
            });
        });
    });

    describe('Accessibility', () => {
        test('has proper ARIA labels and roles', async () => {
            renderWithRouter(<PublicConsultationPage />);
            
            // Check for proper form labels
            await waitFor(() => {
                fireEvent.click(screen.getByText('Submit New Proposal'));
            });
            
            expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
            expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
            
            // Check tab navigation has proper roles
            const tabButtons = screen.getAllByRole('button');
            expect(tabButtons.length).toBeGreaterThan(0);
        });
    });
});
