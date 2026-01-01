
import { useEffect, useState } from 'react';
import { Mic, Loader2, Sparkles, Check, Brain } from 'lucide-react';
import { cn } from '@/lib/utils';

type State = 'idle' | 'recording' | 'processing' | 'recognizing' | 'polishing' | 'typing' | 'error';

export default function Overlay() {
    const [state, setState] = useState<State>('idle');
    const [audioLevel, setAudioLevel] = useState(0);

    useEffect(() => {
        // Mark body as overlay mode for transparent background
        document.body.classList.add('overlay-mode');
        return () => {
            document.body.classList.remove('overlay-mode');
        };
    }, []);

    useEffect(() => {
        // Listen for state changes
        const handleState = (e: CustomEvent) => {
            console.log("Overlay State:", e.detail);
            setState(e.detail);
        };

        const handleAudio = (e: CustomEvent) => {
            setAudioLevel(e.detail);
        };

        window.addEventListener('overlay-state', handleState as EventListener);
        window.addEventListener('audio-level', handleAudio as EventListener);

        return () => {
            window.removeEventListener('overlay-state', handleState as EventListener);
            window.removeEventListener('audio-level', handleAudio as EventListener);
        };
    }, []);

    // Visual configurations - Chinese text
    const config = {
        idle: { color: 'bg-slate-500', icon: <Mic className="w-5 h-5 text-white" />, text: '就绪' },
        recording: { color: 'bg-red-500', icon: <Mic className="w-5 h-5 text-white animate-pulse" />, text: '聆听中...' },
        processing: { color: 'bg-slate-600', icon: <Loader2 className="w-5 h-5 text-white animate-spin" />, text: '处理中' },
        recognizing: { color: 'bg-blue-600', icon: <Brain className="w-5 h-5 text-white" />, text: '识别中' },
        polishing: { color: 'bg-violet-600', icon: <Sparkles className="w-5 h-5 text-white" />, text: '润色中' },
        typing: { color: 'bg-emerald-500', icon: <Check className="w-5 h-5 text-white" />, text: '输入中' },
        error: { color: 'bg-red-600', icon: <Mic className="w-5 h-5 text-white" />, text: '错误' },
    };

    const current = config[state] || config.idle;

    return (
        <div className="w-screen h-screen flex items-end justify-center pb-2 bg-transparent overflow-hidden">
            {/* Main Container */}
            <div className={cn(
                "relative flex items-center space-x-2 px-3 py-2 rounded-full shadow-lg transition-all duration-300",
                "bg-white/95 backdrop-blur-md border border-white/30",
                state === 'idle' ? "opacity-0 scale-90 translate-y-4" : "opacity-100 scale-100 translate-y-0"
            )}>
                {/* Icon Circle with Ripple Effect */}
                <div className="relative">
                    {/* Ripple rings for recording */}
                    {state === 'recording' && (
                        <>
                            <div
                                className="absolute inset-0 rounded-full bg-red-400 opacity-40"
                                style={{
                                    animation: 'ripple 1.5s ease-out infinite',
                                    transform: `scale(${1 + audioLevel * 0.5})`
                                }}
                            />
                            <div
                                className="absolute inset-0 rounded-full bg-red-400 opacity-30"
                                style={{
                                    animation: 'ripple 1.5s ease-out infinite 0.5s',
                                    transform: `scale(${1.2 + audioLevel * 0.5})`
                                }}
                            />
                            <div
                                className="absolute inset-0 rounded-full bg-red-400 opacity-20"
                                style={{
                                    animation: 'ripple 1.5s ease-out infinite 1s',
                                    transform: `scale(${1.4 + audioLevel * 0.5})`
                                }}
                            />
                        </>
                    )}
                    <div
                        className={cn(
                            "relative w-8 h-8 rounded-full flex items-center justify-center shadow-md transition-all duration-150 z-10",
                            current.color
                        )}
                    >
                        {current.icon}
                    </div>
                </div>

                {/* Text Content */}
                <div className="flex flex-col min-w-[60px]">
                    <span className="text-xs font-bold text-slate-800 leading-none">{current.text}</span>
                    <span className="text-[9px] text-slate-400 font-medium mt-0.5">A8轻语</span>
                </div>
            </div>

            {/* Ripple Keyframes */}
            <style>{`
                @keyframes ripple {
                    0% { transform: scale(1); opacity: 0.5; }
                    100% { transform: scale(2.5); opacity: 0; }
                }
            `}</style>
        </div>
    );
}
