import React, { useState, useEffect } from 'react';
import { Home, Sparkles, TrendingUp, AlertTriangle, Settings } from 'lucide-react';
import { toast } from 'sonner';
import { AgentModal } from './components/AgentModal';
import { Skeleton } from './components/Skeleton';
import { EmptyState } from './components/EmptyState';

type AppState = 'idle' | 'loading' | 'success' | 'error';

export default function App() {
    const [appState, setAppState] = useState<AppState>('idle');
    const [errorMessage, setErrorMessage] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false); // Default to false so it does not block the UI on load
    const [apiKey, setApiKey] = useState('');
    const [model, setModel] = useState('gemini-3.1-pro-preview');
    const [mode, setMode] = useState<'pro' | 'fast'>('pro');
    const [quota, setQuota] = useState({ remaining: 50, limit: 50 });

    const DAILY_LIMITS: Record<string, Record<string, number>> = {
        "pro": { "3.1": 50, "2.5": 25 },
        "flash": { "3.1": 500, "2.5": 250 },
        "flash-lite": { "3.1": 1000, "2.5": 500 }
    };

    const updateQuota = (currentMode: 'pro' | 'fast') => {
        const stored = localStorage.getItem("houseprice_rate_limits");
        const today = new Date().toISOString().slice(0, 10);
        let limits = { date: today, used: {} as Record<string, number> };
        if (stored) {
            const p = JSON.parse(stored);
            if (p.date === today) limits = p;
        } else {
            localStorage.setItem("houseprice_rate_limits", JSON.stringify(limits));
        }
        const tier = currentMode === "pro" ? "pro" : "flash-lite";
        const limit = DAILY_LIMITS[tier]?.["3.1"] || 50;
        const used = limits.used[tier] || 0;
        setQuota({ remaining: Math.max(0, limit - used), limit });
    };

    const trackUsage = (modelName: string) => {
        const tier = modelName.includes("pro") ? "pro" : modelName.includes("flash-lite") ? "flash-lite" : "flash";
        const stored = localStorage.getItem("houseprice_rate_limits");
        const today = new Date().toISOString().slice(0, 10);
        let limits = { date: today, used: {} as Record<string, number> };
        if (stored) {
            const p = JSON.parse(stored);
            if (p.date === today) limits = p;
        }
        limits.used[tier] = (limits.used[tier] || 0) + 1;
        localStorage.setItem("houseprice_rate_limits", JSON.stringify(limits));
        updateQuota(mode);
    };

    // Form State
    const [area, setArea] = useState(3000);
    const [bedrooms, setBedrooms] = useState(3);
    const [bathrooms, setBathrooms] = useState(2);
    const [stories] = useState(2);
    const [parking] = useState(1);
    const [furnishing] = useState('semi-furnished');

    // Toggles
    const [toggles, setToggles] = useState({
        mainroad: true,
        guestroom: false,
        basement: false,
        hotwaterheating: false,
        airconditioning: true,
        prefarea: false
    });

    // Result State
    const [predictedPrice, setPredictedPrice] = useState<number | null>(null);
    const [agentAnalysis, setAgentAnalysis] = useState<string>('');

    useEffect(() => {
        const savedKey = localStorage.getItem('gemini_api_key');
        const savedModel = localStorage.getItem('gemini_model');
        const savedMode = localStorage.getItem('gemini_mode') as 'pro' | 'fast';
        if (savedKey) {
            setApiKey(savedKey);
        }
        if (savedModel) {
            setModel(savedModel);
        }
        if (savedMode) {
            setMode(savedMode);
        } else {
            setMode('pro');
        }
        updateQuota(savedMode || 'pro');
    }, []);

    const handleSaveConfig = (key: string, selectedModel: string, selectedMode: 'pro' | 'fast') => {
        localStorage.setItem('gemini_api_key', key);
        localStorage.setItem('gemini_model', selectedModel);
        localStorage.setItem('gemini_mode', selectedMode);
        setApiKey(key);
        setModel(selectedModel);
        setMode(selectedMode);
        updateQuota(selectedMode);
        setIsModalOpen(false);
        toast.success(`Agent configuration saved (${selectedMode.toUpperCase()} Mode)`);
    };

    const handleToggle = (key: keyof typeof toggles) => {
        setToggles(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        setAppState('loading');
        setErrorMessage('');
        setPredictedPrice(null);
        setAgentAnalysis('');

        try {
            // 1. ML Backend Call
            const mlResponse = await fetch('/app.py?action=predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ area, bedrooms, bathrooms, stories, parking, furnishingstatus: furnishing, ...toggles })
            });

            // Safe JSON parse — guard against empty/HTML responses
            const mlText = await mlResponse.text();
            let mlData: any;
            try {
                mlData = JSON.parse(mlText);
            } catch {
                throw new Error(`ML backend returned invalid response: ${mlText.slice(0, 200) || '(empty)'}`);
            }
            if (!mlResponse.ok) throw new Error(mlData.error || 'ML Inference Failed');

            const price = mlData.predicted_price;
            setPredictedPrice(price);

            // 2. Cross-Project LLM Wrapper Call (Proxy to Server)
            const prompt = `You are an expert real estate market analyst. A user is looking at a property with ${area} sq ft, ${bedrooms} beds, ${bathrooms} baths. Has AC: ${toggles.airconditioning}. The algorithmic pricing model predicted $${price.toLocaleString()}.
      Task: Search for the most recent housing market trends. Provide a short qualitative analysis if this predicted price aligns with current macro trends. Output simple text without markdown blocks.`;

            const aiResponse = await fetch('/app.py?action=analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Gemini-Key': apiKey || ""
                },
                body: JSON.stringify({ prompt, model })
            });

            // Safe JSON parse — guard against empty/HTML responses
            const aiText = await aiResponse.text();
            let aiData: any;
            try {
                aiData = JSON.parse(aiText);
            } catch {
                throw new Error(`AI agent returned invalid response: ${aiText.slice(0, 200) || '(empty)'}`);
            }
            if (!aiResponse.ok) {
                if (aiResponse.status === 429) {
                    throw new Error("⏳ Rate limit reached — try again in ~1 minute, or switch to Fast mode.");
                }
                throw new Error(aiData.error || 'Agent Analysis Failed');
            }

            trackUsage(aiData._model_used || model);

            const analysisText = aiData.candidates[0]?.content?.parts[0]?.text || 'Market analysis complete.';
            setAgentAnalysis(analysisText);
            setAppState('success');
            toast.success('Valuation and active market analysis completed.');

        } catch (err: any) {
            setAppState('error');
            const msg = err.message || 'Network connection dropped';
            setErrorMessage(msg);
            toast.error(`Agent Pipeline Failed: ${msg}`);
        }
    };

    return (
        <>
            <AgentModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSave={handleSaveConfig} initialMode={mode} initialModel={model} quotaRemaining={quota.remaining} quotaLimit={quota.limit} />

            <div className="flex items-center justify-center p-6 lg:p-12 w-full max-w-4xl mx-auto">
                <div className="w-full glass-card p-10">
                    <div className="flex justify-between items-start mb-8">
                        <div>
                            <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-brand-500 to-emerald-300 flex items-center gap-3">
                                <Home className="text-brand-500" size={32} />
                                House Price Predictor
                            </h1>
                            <p className="text-slate-400 mt-2">ML Valuation + Live Web Search Market Agent</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => {
                                    const newMode = mode === 'pro' ? 'fast' : 'pro';
                                    const newModel = newMode === 'pro' ? 'gemini-3.1-pro-preview' : 'gemini-3.1-flash-lite-preview';
                                    handleSaveConfig(apiKey, newModel, newMode);
                                }}
                                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${mode === 'pro'
                                    ? 'bg-gradient-to-br from-purple-600 to-indigo-600 shadow-lg shadow-purple-500/20 text-white'
                                    : 'bg-gradient-to-br from-emerald-600 to-teal-600 shadow-lg shadow-emerald-500/20 text-white'
                                    }`}
                            >
                                {mode === 'pro' ? '⚡ PRO' : '🚀 FAST'}
                            </button>
                            <button
                                onClick={() => setIsModalOpen(true)}
                                className="p-3 bg-white/5 border border-white/10 rounded-full hover:bg-white/10 transition-colors relative"
                                title="Agent Settings"
                            >
                                <Settings size={20} className="text-brand-500" />
                                <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-[#0B0F19] ${quota.remaining / quota.limit > 0.5 ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                            </button>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="bg-black/30 border border-white/5 rounded-2xl p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Area (sq ft)</label>
                                    <input type="number" value={area} onChange={e => setArea(+e.target.value)} className="w-full bg-surface/50 border border-white/10 text-white rounded-xl px-4 py-3 focus:border-brand-500 outline-none" required />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Bedrooms</label>
                                    <input type="number" value={bedrooms} onChange={e => setBedrooms(+e.target.value)} className="w-full bg-surface/50 border border-white/10 text-white rounded-xl px-4 py-3 focus:border-brand-500 outline-none" required />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Bathrooms</label>
                                    <input type="number" value={bathrooms} onChange={e => setBathrooms(+e.target.value)} className="w-full bg-surface/50 border border-white/10 text-white rounded-xl px-4 py-3 focus:border-brand-500 outline-none" required />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mt-8">
                                {Object.entries(toggles).map(([key, val]) => (
                                    <label key={key} className="flex items-center gap-3 bg-surface/50 p-3 rounded-xl border border-white/5 cursor-pointer hover:border-brand-500/50 transition-colors">
                                        <input type="checkbox" checked={val} onChange={() => handleToggle(key as keyof typeof toggles)} className="hidden" />
                                        <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${val ? 'bg-brand-500 border-brand-500' : 'border-slate-500'}`} />
                                        <span className="text-xs font-medium capitalize truncate">{key.replace('prefarea', 'Pref Area').replace('hotwaterheating', 'Hot Water').replace('airconditioning', 'AC')}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={appState === 'loading'}
                            className="w-full py-4 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-500 text-white font-bold text-lg hover:shadow-[0_0_30px_rgba(16,185,129,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
                        >
                            {appState === 'loading' ? (
                                <>
                                    <div className="w-6 h-6 border-3 border-white/20 border-t-white rounded-full animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Sparkles size={24} />
                                    Predict & Analyze
                                </>
                            )}
                        </button>
                    </form>

                    {appState === 'idle' && !predictedPrice && (
                        <EmptyState />
                    )}

                    {appState === 'loading' && (
                        <Skeleton />
                    )}

                    {appState === 'error' && (
                        <div className="mt-8 bg-red-500/10 border border-red-500/20 rounded-2xl p-6 flex items-start gap-4">
                            <AlertTriangle className="text-red-500 shrink-0" />
                            <div>
                                <h3 className="text-red-500 font-bold mb-1">Agent Pipeline Failed</h3>
                                <p className="text-red-400/80 text-sm">{errorMessage}</p>
                            </div>
                        </div>
                    )}

                    {appState === 'success' && predictedPrice && (
                        <div className="mt-8 space-y-6">
                            <div className="bg-surface/80 border border-brand-500/30 rounded-2xl p-8 text-center relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/10 blur-3xl rounded-full" />
                                <p className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-2">Baseline ML Valuation</p>
                                <h2 className="text-5xl font-extrabold text-white">${predictedPrice.toLocaleString()}</h2>
                            </div>

                            <div className="bg-black/40 border border-white/10 rounded-2xl p-8">
                                <div className="flex items-center gap-3 text-brand-500 font-bold mb-4">
                                    <TrendingUp />
                                    Agentic Market Analysis ({model})
                                </div>
                                <div className="text-slate-300 leading-relaxed space-y-4 text-sm" dangerouslySetInnerHTML={{ __html: agentAnalysis.replace(/\n\n/g, '<br/><br/>').replace(/\*\*(.*?)\*\*/g, '<b class="text-white">$1</b>') }} />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
