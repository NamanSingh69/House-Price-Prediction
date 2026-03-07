import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (key: string, model: string) => void;
}

export function AgentModal({ isOpen, onSave }: ModalProps) {
    const [apiKey, setApiKey] = useState('');
    const [selectedModel, setSelectedModel] = useState('gemini-1.5-flash');

    useEffect(() => {
        const savedKey = localStorage.getItem('gemini_api_key');
        const savedModel = localStorage.getItem('gemini_model');
        if (savedKey) setApiKey(savedKey);
        if (savedModel) setSelectedModel(savedModel);
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="w-full max-w-md bg-surface-2 border border-white/10 rounded-2xl p-6 shadow-2xl relative">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-brand-500/10 text-brand-500 rounded-lg">
                        <Sparkles size={24} />
                    </div>
                    <h2 className="text-xl font-bold text-white">Agent Settings</h2>
                </div>

                <p className="text-sm text-slate-400 mb-6">
                    Configure your Bring-Your-Own-Key (BYOK) AI Agent. This enables real-time market analysis using Google Search Grounding.
                </p>

                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            Gemini API Key
                        </label>
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="Using public fallback key — paste your own for higher limits"
                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all font-mono"
                        />
                        <div className="text-[10px] text-slate-400 mt-2 leading-snug px-1">
                            ✅ A free public API key is active by default. Add your own for higher rate limits.<br />
                            <strong className="text-slate-300">Free Tier Limits:</strong> 15 Requests/Min, 1,000,000 Tokens/Min, 1,500 Requests/Day.
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                            Agent Model (Gemini 3.1 Resolver)
                        </label>
                        <select
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all appearance-none"
                        >
                            <option value="gemini-1.5-flash">Gemini 1.5 Flash (Default, High Speed)</option>
                            <option value="gemini-1.5-pro">Gemini 1.5 Pro (Deep Reasoning, Slower)</option>
                            <option value="gemini-2.5-pro">Gemini 2.5 Pro (Experimental)</option>
                        </select>
                        <p className="text-xs text-slate-500 mt-2">
                            Flash is recommended for immediate UI responsiveness. Pro is recommended for complex comparative market analysis.
                        </p>
                    </div>
                </div>

                <div className="flex gap-3 mt-8">
                    <button
                        onClick={() => {
                            onSave(apiKey, selectedModel);
                        }}
                        className="flex-1 bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3 px-4 rounded-xl transition-colors"
                    >
                        Save Configuration
                    </button>
                </div>
            </div>
        </div>
    );
}
