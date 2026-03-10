import { Home } from 'lucide-react';

export function EmptyState() {
    return (
        <div className="mt-8 bg-surface/40 border border-white/5 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-6">
                <Home className="w-8 h-8 text-slate-500" />
            </div>
            <h3 className="text-xl font-bold text-slate-300 mb-2">Ready for Valuation</h3>
            <p className="text-slate-500 max-w-sm">
                Enter the property details and click Predict & Analyze to receive an AI-driven market valuation.
            </p>
        </div>
    );
}
