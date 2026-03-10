import { Sparkles } from 'lucide-react';

export function Skeleton() {
    return (
        <div className="mt-8 space-y-6 animate-pulse">
            <div className="bg-surface/80 border border-slate-700/50 rounded-2xl p-8 text-center relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-slate-500/10 blur-3xl rounded-full" />
                <div className="h-4 bg-slate-700/50 rounded w-48 mx-auto mb-4"></div>
                <div className="h-12 bg-slate-700/80 rounded w-64 mx-auto"></div>
            </div>

            <div className="bg-black/40 border border-white/10 rounded-2xl p-8">
                <div className="flex items-center gap-3 text-slate-500 font-bold mb-4">
                    <Sparkles className="animate-pulse" />
                    <div className="h-5 bg-slate-700/50 rounded w-48"></div>
                </div>
                <div className="space-y-4">
                    <div className="h-4 bg-slate-800/80 rounded w-full"></div>
                    <div className="h-4 bg-slate-800/80 rounded w-5/6"></div>
                    <div className="h-4 bg-slate-800/80 rounded w-4/6"></div>
                </div>
            </div>
        </div>
    );
}
