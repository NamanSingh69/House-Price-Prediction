import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (key: string, model: string, mode: 'pro' | 'fast') => void;
    initialMode?: 'pro' | 'fast';
    initialModel?: string;
    quotaRemaining?: number;
    quotaLimit?: number;
}

export function AgentModal({ isOpen, onClose, onSave, initialMode = 'pro', initialModel = 'gemini-3.1-pro-preview', quotaRemaining = 50, quotaLimit = 50 }: ModalProps) {
    const [apiKey, setApiKey] = useState('');
    const [selectedModel, setSelectedModel] = useState(initialModel);
    const [mode, setMode] = useState<'pro' | 'fast'>(initialMode);

    useEffect(() => {
        const savedKey = localStorage.getItem('gemini_api_key');
        if (savedKey) setApiKey(savedKey);
        setSelectedModel(initialModel);
        setMode(initialMode);
    }, [isOpen, initialModel, initialMode]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="w-full max-w-md bg-surface-2 border border-white/10 rounded-2xl p-6 shadow-2xl relative">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-brand-500/10 text-brand-500 rounded-lg">
                            <Sparkles size={24} />
                        </div>
                        <h2 className="text-xl font-bold text-white">Agent Settings</h2>
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-white p-2">
                        ✕
                    </button>
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
                        <div className="flex justify-between items-center mb-2">
                            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                Agent Mode & Model
                            </label>
                            <div className="flex bg-black/40 rounded-lg p-1">
                                <button
                                    className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${mode === 'pro' ? 'bg-brand-500 text-white' : 'text-slate-400 hover:text-white'}`}
                                    onClick={() => { setMode('pro'); setSelectedModel('gemini-3.1-pro-preview'); }}
                                >
                                    PRO
                                </button>
                                <button
                                    className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${mode === 'fast' ? 'bg-brand-500 text-white' : 'text-slate-400 hover:text-white'}`}
                                    onClick={() => { setMode('fast'); setSelectedModel('gemini-3.1-flash-lite-preview'); }}
                                >
                                    FAST
                                </button>
                            </div>
                        </div>
                        <select
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all appearance-none"
                        >
                            {mode === 'pro' ? (
                                <>
                                    <option value="gemini-3.1-pro-preview">Gemini 3.1 Pro Preview (Default)</option>
                                    <option value="gemini-2.5-pro">Gemini 2.5 Pro (Extremely capable but slower)</option>
                                </>
                            ) : (
                                <>
                                    <option value="gemini-3.1-flash-lite-preview">Gemini 3.1 Flash Lite (Default)</option>
                                    <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                                </>
                            )}
                        </select>
                        <p className="text-xs text-slate-500 mt-2">
                            Pro offers deep reasoning but consumes quota 10x faster. Fast is recommended for general analysis.
                        </p>
                    </div>

                    {/* Rate Limit Display */}
                    <div className="bg-black/20 p-4 rounded-xl border border-white/5">
                        <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-400 uppercase font-semibold">Daily Quota</span>
                            <span className="text-white font-medium">{quotaRemaining} / {quotaLimit}</span>
                        </div>
                        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mt-2">
                            <div
                                className={`h-full transition-all duration-500 ${quotaRemaining / quotaLimit > 0.5 ? 'bg-brand-500' : quotaRemaining / quotaLimit > 0.2 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                style={{ width: `${Math.max(0, Math.min(100, (quotaRemaining / quotaLimit) * 100))}%` }}
                            />
                        </div>
                    </div>
                </div>

                <div className="flex gap-3 mt-8">
                    <button
                        onClick={onClose}
                        className="flex-1 bg-white/5 hover:bg-white/10 text-white font-semibold py-3 px-4 rounded-xl transition-colors"
                    >
                        Close
                    </button>
                    <button
                        onClick={() => {
                            onSave(apiKey, selectedModel, mode);
                        }}
                        className="flex-1 bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3 px-4 rounded-xl transition-colors"
                    >
                        Save Configuration
                    </button>
                </div>
            </div>
        </div >
    );
}
