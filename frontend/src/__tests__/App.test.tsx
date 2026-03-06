import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Use Vitest global stubbing instead of global.fetch assignments to satisfy TS
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('House Price Predictor State Machine', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        localStorage.clear();
    });

    it('renders idle state correctly and prompts for API key if missing', () => {
        render(<App />);
        expect(screen.getByText(/House Price Predictor/i)).toBeInTheDocument();

        // Modal should be visible since localStorage has no gemini_api_key
        expect(screen.getByText(/Agent Settings/i)).toBeInTheDocument();
    });

    it('transitions to loading state upon submission and then success', async () => {
        localStorage.setItem('gemini_api_key', 'test_key_123');

        // Mock the ML API call (fetch #1)
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ predicted_price: 450000 })
        });

        // Mock the Gemini Agent call (fetch #2)
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                candidates: [{ content: { parts: [{ text: 'Market analysis complete.' }] } }]
            })
        });

        render(<App />);

        const submitBtn = screen.getByRole('button', { name: /Predict & Analyze/i });

        // Trigger submission
        fireEvent.click(submitBtn);

        // Verify loading state
        expect(submitBtn).toBeDisabled();
        expect(submitBtn).toHaveTextContent(/Processing.../i);

        // Provide explicit wait for state transitions to resolve
        await waitFor(() => {
            // Verify success state reveals the prediction
            expect(screen.getByText(/\$4,?50,000/)).toBeInTheDocument();
            // Verify success state reveals the agent analysis
            expect(screen.getByText('Market analysis complete.')).toBeInTheDocument();
        });

        // Button should be re-enabled
        expect(submitBtn).not.toBeDisabled();
    });

    it('transitions to error state upon network failure', async () => {
        localStorage.setItem('gemini_api_key', 'test_key_123');

        // Mock API failure
        mockFetch.mockRejectedValueOnce(new Error('Network connection dropped'));

        render(<App />);

        fireEvent.click(screen.getByRole('button', { name: /Predict & Analyze/i }));

        await waitFor(() => {
            expect(screen.getByText(/Network connection dropped/i)).toBeInTheDocument();
        });
    });
});
