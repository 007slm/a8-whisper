import { useEffect, useState } from 'react';
import { bridge } from '@/lib/bridge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Activity, Mic, Brain, Settings as SettingsIcon, Keyboard, Server, Cpu, CheckCircle, AlertCircle, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

// ... interface Config ...
interface Config {
    asr_model: string;
    llm_enabled: boolean;
    llm_model: string;
    use_cloud: boolean;
    user_dict: string[];
    hotkey: string;
    sound_enabled?: boolean;
    overlay_enabled?: boolean;
    asr_prompt?: string;
    llm_prompt?: string;
    models_status?: Record<string, boolean>;
}

type NavItem = 'general' | 'models' | 'dictionary';

function App() {
    const [config, setConfig] = useState<Config | null>(null);
    const [nav, setNav] = useState<NavItem>('general');
    const [newWord, setNewWord] = useState("");
    const [downloadState, setDownloadState] = useState({ downloading: false, progress: 0, model: "" });
    const [llmDownloadProgress, setLlmDownloadProgress] = useState(0);
    const [llmInstalled, setLlmInstalled] = useState(false);
    // State for initialization removed


    // ... Original App Logic ...
    useEffect(() => {
        // Force light mode by default for enterprise feel
        document.documentElement.classList.remove('dark');

        // Disable browser context menu for product feel
        const handleContextMenu = (e: MouseEvent) => {
            e.preventDefault();
        };
        document.addEventListener('contextmenu', handleContextMenu);

        bridge.getConfig().then((cfg: any) => {
            if (typeof cfg === 'string') cfg = JSON.parse(cfg);
            setConfig(cfg);
        });

        // ... rest of useEffect

        if ((bridge as any).onConfigChanged) {
            (bridge as any).onConfigChanged((newConfig: Config) => {
                setConfig(prev => ({ ...prev, ...newConfig }));
            });
        }

        if ((bridge as any).onLlmDownloadProgress) {
            (bridge as any).onLlmDownloadProgress((progress: number) => {
                console.log("LLM Progress:", progress);
                setLlmDownloadProgress(progress);
                if (progress >= 1) {
                    setLlmInstalled(true);
                    alert("LLM 模型下载完成 / LLM Model Downloaded");
                } else if (progress < 0) {
                    alert("LLM 模型下载失败 / LLM Model Download Failed");
                }
            });
        }

        if ((bridge as any).onDownloadProgress) {
            (bridge as any).onDownloadProgress((model: string, progress: number) => {
                if (progress < 0) {
                    setDownloadState({ downloading: false, progress: 0, model: "" });
                    alert("下载失败 / Download Failed");
                } else if (progress >= 1) {
                    setDownloadState({ downloading: false, progress: 0, model: "" });
                    bridge.getConfig().then(setConfig);
                } else {
                    setDownloadState({ downloading: true, progress, model });
                }
            });
        }

        // Listen for initialization status (Removed for UI, but keeping listener if needed for other logic? No, just removing UI logic)
        // const handleInitStatus = (e: CustomEvent) => { ... }


        return () => {
            document.removeEventListener('contextmenu', handleContextMenu);
            // window.removeEventListener("init_status", handleInitStatus as EventListener);
        };
    }, []);

    const downloadModel = (model: string) => {
        setDownloadState({ downloading: true, progress: 0.01, model });
        bridge.downloadModel(model);
    };

    const updateConfig = (key: keyof Config, value: any) => {
        if (!config) return;
        const newConfig = { ...config, [key]: value };
        setConfig(newConfig);
        bridge.saveConfig(newConfig);
    };

    const addWord = () => {
        if (!config || !newWord.trim()) return;
        const newDict = [...config.user_dict, newWord.trim()];
        updateConfig('user_dict', newDict);
        setNewWord("");
    };

    const removeWord = (word: string) => {
        if (!config) return;
        updateConfig('user_dict', config.user_dict.filter(w => w !== word));
    };

    // WS State removed (Native Bridge Mode)

    if (!config) return (
        <div className="flex items-center justify-center h-screen bg-slate-50">
            <div className="flex flex-col items-center max-w-md text-center p-6 bg-white rounded-lg shadow-sm border border-slate-100">
                <div className="w-8 h-8 border-4 border-slate-200 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
                <h3 className="text-lg font-medium text-slate-800 mb-2">正在启动本地引擎...</h3>
                <div className="text-left text-xs text-slate-500 font-mono bg-slate-100 p-3 rounded w-full">
                    <p>Mode: <span className="text-indigo-600 font-bold">Native Bridge</span></p>
                    <p>Status: Initializing...</p>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onClick={() => window.location.reload()}
                >
                    刷新页面 (Reload)
                </Button>
            </div>
        </div>
    );

    return (
        <div className="flex flex-col h-screen bg-slate-50 font-sans text-slate-900 overflow-hidden selection:bg-indigo-100 selection:text-indigo-900 rounded-xl">

            {/* Custom Title Bar - Frameless Window */}
            <div
                className="h-10 bg-white border-b border-slate-100 flex items-center justify-between px-4 shrink-0 rounded-t-xl cursor-move pywebview-drag-region"
                onMouseDown={() => bridge.startDrag()}
            >
                <span className="text-sm font-medium text-slate-600">A8轻语 设置</span>
                <div className="flex items-center gap-1" onMouseDown={(e) => e.stopPropagation()}>
                    <button
                        onClick={() => bridge.minimizeWindow()}
                        className="w-8 h-8 rounded-md hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-slate-700 transition-colors"
                        title="最小化"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" /></svg>
                    </button>
                    <button
                        onClick={() => bridge.maximizeWindow()}
                        className="w-8 h-8 rounded-md hover:bg-slate-100 flex items-center justify-center text-slate-500 hover:text-slate-700 transition-colors"
                        title="最大化/还原"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2" strokeWidth={2} /></svg>
                    </button>
                    <button
                        onClick={() => bridge.closeWindow()}
                        className="w-8 h-8 rounded-md hover:bg-red-50 flex items-center justify-center text-slate-500 hover:text-red-600 transition-colors"
                        title="关闭"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex flex-1 overflow-hidden">

                {/* Sidebar */}
                <aside className="w-64 bg-white border-r border-slate-200 flex flex-col z-10 transition-all duration-300">
                    <div className="p-6 pb-4 cursor-default">
                        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center">
                            <span className="w-10 h-10 mr-3 flex items-center justify-center">
                                <svg viewBox="0 0 512 512" className="w-10 h-10">
                                    <defs>
                                        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" style={{ stopColor: '#6366f1' }} />
                                            <stop offset="100%" style={{ stopColor: '#4f46e5' }} />
                                        </linearGradient>
                                    </defs>
                                    <rect x="0" y="0" width="512" height="512" rx="96" fill="url(#bgGrad)" />
                                    <rect x="180" y="100" width="100" height="160" rx="50" fill="white" />
                                    <path d="M 150 220 Q 150 320 230 320 Q 310 320 310 220" fill="none" stroke="white" strokeWidth="20" strokeLinecap="round" />
                                    <line x1="230" y1="320" x2="230" y2="380" stroke="white" strokeWidth="20" strokeLinecap="round" />
                                    <line x1="180" y1="380" x2="280" y2="380" stroke="white" strokeWidth="20" strokeLinecap="round" />
                                    <line x1="330" y1="140" x2="420" y2="140" stroke="white" strokeWidth="16" strokeLinecap="round" opacity="0.9" />
                                    <line x1="330" y1="190" x2="400" y2="190" stroke="white" strokeWidth="16" strokeLinecap="round" opacity="0.7" />
                                    <line x1="330" y1="240" x2="380" y2="240" stroke="white" strokeWidth="16" strokeLinecap="round" opacity="0.5" />
                                </svg>
                            </span>
                            轻语
                        </h1>
                        <p className="text-xs text-slate-500 mt-1 pl-14">企业级语音助手</p>
                    </div>

                    <nav className="flex-1 px-4 space-y-1 mt-4">
                        <SidebarItem
                            active={nav === 'general'}
                            onClick={() => setNav('general')}
                            icon={<SettingsIcon className="w-4 h-4" />}
                            label="常规设置"
                            subLabel="General Settings"
                        />
                        <SidebarItem
                            active={nav === 'models'}
                            onClick={() => setNav('models')}
                            icon={<Brain className="w-4 h-4" />}
                            label="模型引擎"
                            subLabel="Model Engine"
                        />
                        <SidebarItem
                            active={nav === 'dictionary'}
                            onClick={() => setNav('dictionary')}
                            icon={<Activity className="w-4 h-4" />}
                            label="热词管理"
                            subLabel="Dictionary"
                        />
                    </nav>

                    <div className="p-4 border-t border-slate-100">
                        <div className="bg-slate-50 rounded-lg p-3 flex items-center space-x-3 border border-slate-100">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                            <div>
                                <p className="text-xs font-medium text-slate-700">服务运行中</p>
                                <p className="text-[10px] text-slate-500">v1.2.0 • Pro Edition</p>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 flex flex-col min-w-0 z-0">

                    {/* Critical Alerts Area */}
                    {(config.models_status && !config.models_status[config.asr_model]) && (
                        <div className="bg-red-50 border-b border-red-100 px-8 py-3 flex items-center justify-between animate-in slide-in-from-top-2">
                            <div className="flex items-center text-red-700 text-sm">
                                <AlertCircle className="w-4 h-4 mr-2" />
                                <span className="font-medium">组件缺失:</span>
                                <span className="ml-1 opacity-90">请下载 <strong>{config.asr_model}</strong> 模型以启用语音识别功能。</span>
                            </div>
                            <Button
                                size="sm"
                                className="bg-red-600 hover:bg-red-700 text-white border-0 h-7 text-xs shadow-none"
                                onClick={() => downloadModel(config.asr_model)}
                                disabled={downloadState.downloading}
                            >
                                {downloadState.downloading ? `下载中 ${Math.round(downloadState.progress * 100)}%` : "立即下载"}
                            </Button>
                        </div>
                    )}

                    {/* Initialization Status Bar */}
                    {/* Initialization Status Bar Removed */}

                    {/* If downloading, show thin progress bar */}
                    {downloadState.progress > 0 && (
                        <div className="h-0.5 w-full bg-slate-100">
                            <div className="h-full bg-indigo-600 transition-all duration-300" style={{ width: `${downloadState.progress * 100}%` }} />
                        </div>
                    )}

                    <ScrollArea className="flex-1 p-8">
                        <div className="max-w-4xl mx-auto space-y-8 pb-10">

                            {/* Header Section */}
                            <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
                                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                                    {nav === 'general' && '常规设置'}
                                    {nav === 'models' && '模型引擎'}
                                    {nav === 'dictionary' && '热词管理'}
                                </h2>
                                <p className="text-slate-500 mt-1.5 text-sm">
                                    {nav === 'general' && '配置全局快捷键与应用行为偏好。'}
                                    {nav === 'models' && '管理本地推理模型与云端 API 连接。'}
                                    {nav === 'dictionary' && '添加专用术语以提高语音识别准确率。'}
                                </p>
                            </div>

                            <div className="h-px bg-slate-200/60 w-full" />

                            {/* Content */}
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                {nav === 'general' && (
                                    <div className="grid grid-cols-1 gap-6">
                                        <SectionCard title="交互设置" icon={<Keyboard className="w-5 h-5 text-indigo-600" />}>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                                <div className="space-y-3">
                                                    <Label className="text-slate-700 font-medium">全局热键</Label>
                                                    <div className="flex items-center">
                                                        <div className="px-4 py-2.5 bg-slate-100 border border-slate-200 rounded-md font-mono text-sm text-slate-600 flex items-center shadow-sm w-full">
                                                            <span className="bg-white border border-slate-200 rounded px-1.5 py-0.5 text-xs mr-2 shadow-sm text-slate-500">长按</span>
                                                            {config.hotkey}
                                                        </div>
                                                    </div>
                                                    <p className="text-[11px] text-slate-400 leading-relaxed">
                                                        长按开始录音，松开结束并转换。<br />系统使用底层键盘钩子监听。
                                                    </p>
                                                </div>
                                                <div className="space-y-4">
                                                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100 transition-colors hover:border-slate-200">
                                                        <div className="space-y-0.5">
                                                            <Label className="text-base text-slate-700">桌面悬浮窗</Label>
                                                            <p className="text-xs text-slate-500">显示极简状态指示器</p>
                                                        </div>
                                                        <Switch
                                                            checked={config.overlay_enabled ?? true}
                                                            onCheckedChange={(c) => updateConfig('overlay_enabled', c)}
                                                            className="data-[state=checked]:bg-indigo-600"
                                                        />
                                                    </div>
                                                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100 transition-colors hover:border-slate-200">
                                                        <div className="space-y-0.5">
                                                            <Label className="text-base text-slate-700">声音反馈</Label>
                                                            <p className="text-xs text-slate-500">开始/结束时播放提示音</p>
                                                        </div>
                                                        <Switch
                                                            checked={config.sound_enabled ?? false}
                                                            onCheckedChange={(c) => updateConfig('sound_enabled', c)}
                                                            className="data-[state=checked]:bg-indigo-600"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </SectionCard>

                                        {/* Prompt Configuration Section */}
                                        <SectionCard title="提示词配置" icon={<Sparkles className="w-5 h-5 text-purple-600" />}>
                                            <div className="space-y-6">
                                                <div className="space-y-2">
                                                    <Label className="text-slate-700 font-medium">ASR 识别提示词</Label>
                                                    <p className="text-xs text-slate-500">帮助模型更准确识别特定领域术语。<span className="text-indigo-600 font-medium">热词管理中的词汇会自动附加到此提示词后。</span></p>
                                                    <textarea
                                                        value={config.asr_prompt ?? ''}
                                                        onChange={(e) => updateConfig('asr_prompt', e.target.value)}
                                                        className="w-full h-20 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 resize-none"
                                                        placeholder="例如: 以下是关于软件开发的技术讨论..."
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <Label className="text-slate-700 font-medium">LLM 润色提示词</Label>
                                                    <p className="text-xs text-slate-500">控制智能润色的行为。使用 {'{user_dict}'} 作为用户词典占位符。</p>
                                                    <textarea
                                                        value={config.llm_prompt ?? ''}
                                                        onChange={(e) => updateConfig('llm_prompt', e.target.value)}
                                                        className="w-full h-40 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 resize-none font-mono"
                                                        placeholder="系统提示词..."
                                                    />
                                                </div>
                                            </div>
                                        </SectionCard>
                                    </div>
                                )}

                                {nav === 'models' && (
                                    <div className="space-y-6">
                                        <SectionCard title="语音识别 (ASR)" icon={<Mic className="w-5 h-5 text-blue-600" />}>
                                            <div className="flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <h4 className="font-medium text-slate-800">Faster-Whisper 模型</h4>
                                                    <p className="text-sm text-slate-500">选择模型尺寸以平衡速度与精度。</p>
                                                </div>
                                                <Select value={config.asr_model} onValueChange={(v) => updateConfig('asr_model', v)}>
                                                    <SelectTrigger className="w-[240px] bg-white border-slate-200 shadow-sm focus:ring-2 focus:ring-indigo-500/20">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="large-v3">Large V3 (推荐 / 高精度)</SelectItem>
                                                        <SelectItem value="medium">Medium (平衡)</SelectItem>
                                                        <SelectItem value="small">Small (极速)</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>

                                            {config.models_status && config.models_status[config.asr_model] && (
                                                <div className="mt-4 flex items-center text-xs text-emerald-600 bg-emerald-50 px-3 py-2 rounded-md border border-emerald-100 w-fit">
                                                    <CheckCircle className="w-3.5 h-3.5 mr-2" />
                                                    模型已安装就绪
                                                </div>
                                            )}
                                        </SectionCard>

                                        <SectionCard title="智能润色 (LLM)" icon={<Brain className="w-5 h-5 text-violet-600" />}>
                                            <div className="space-y-6">
                                                <div className="flex items-center justify-between">
                                                    <div className="space-y-1">
                                                        <h4 className="font-medium text-slate-800">启用文本修正</h4>
                                                        <p className="text-sm text-slate-500">使用大模型自动修正错别字、标点与格式。</p>
                                                    </div>
                                                    <Switch
                                                        checked={config.llm_enabled}
                                                        onCheckedChange={(c) => updateConfig('llm_enabled', c)}
                                                        className="data-[state=checked]:bg-indigo-600"
                                                    />
                                                </div>

                                                {config.llm_enabled && (
                                                    <div className="bg-slate-50 rounded-lg p-5 border border-slate-200 space-y-5 animate-in slide-in-from-top-1">
                                                        <div className="grid grid-cols-2 gap-4">
                                                            <button
                                                                onClick={async () => {
                                                                    // VRAM Check (Non-blocking)
                                                                    if (config.use_cloud) { // Switching TO local
                                                                        const vram = await (bridge as any).checkVRAM();
                                                                        console.log("Checked VRAM:", vram);
                                                                        if (vram < 6) {
                                                                            // Just warn, don't block
                                                                            alert(`警告：显存 (${vram.toFixed(1)}GB) 较低，建议至少 6GB。`);
                                                                        }

                                                                        // Check if model exists
                                                                        const exists = await (bridge as any).checkLLMFileExists();
                                                                        setLlmInstalled(exists);
                                                                    }
                                                                    updateConfig('use_cloud', false);
                                                                }}
                                                                className={cn(
                                                                    "flex flex-col items-center p-4 rounded-lg border transition-all text-sm font-medium",
                                                                    !config.use_cloud
                                                                        ? "bg-white border-indigo-600 text-indigo-700 shadow-sm ring-1 ring-indigo-600"
                                                                        : "bg-transparent border-slate-200 text-slate-600 hover:bg-white hover:border-slate-300"
                                                                )}
                                                            >
                                                                <Cpu className="w-6 h-6 mb-2 opacity-80" />
                                                                本地运行 (隐私)
                                                            </button>
                                                            <button
                                                                onClick={() => updateConfig('use_cloud', true)}
                                                                className={cn(
                                                                    "flex flex-col items-center p-4 rounded-lg border transition-all text-sm font-medium",
                                                                    config.use_cloud
                                                                        ? "bg-white border-indigo-600 text-indigo-700 shadow-sm ring-1 ring-indigo-600"
                                                                        : "bg-transparent border-slate-200 text-slate-600 hover:bg-white hover:border-slate-300"
                                                                )}
                                                            >
                                                                <Server className="w-6 h-6 mb-2 opacity-80" />
                                                                云端 API
                                                            </button>
                                                        </div>

                                                        {config.use_cloud ? (
                                                            <div className="space-y-2">
                                                                <Label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">API 密钥配置</Label>
                                                                <Input type="password" placeholder="sk-..." className="bg-white border-slate-200" />
                                                            </div>
                                                        ) : (
                                                            <div className="space-y-4">
                                                                <div className="space-y-2">
                                                                    <Label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">本地模型状态</Label>
                                                                    <div className={cn(
                                                                        "p-3 rounded text-xs font-mono border truncate flex items-center justify-between transition-colors",
                                                                        llmInstalled ? "bg-emerald-50 text-emerald-700 border-emerald-100" : "bg-slate-100 text-slate-600 border-slate-200"
                                                                    )}>
                                                                        <span title="models/qwen2.5-coder-7b-instruct-q4_k_m.gguf">
                                                                            {llmInstalled ? "Qwen2.5-Coder-7B 已安装就绪" : "未检测到模型文件 (Missing)"}
                                                                        </span>
                                                                        {llmDownloadProgress > 0 && llmDownloadProgress < 1 ? (
                                                                            <span className="text-indigo-600 font-bold">{Math.round(llmDownloadProgress * 100)}%</span>
                                                                        ) : llmInstalled ? (
                                                                            <CheckCircle className="w-4 h-4 text-emerald-500" />
                                                                        ) : (
                                                                            <AlertCircle className="w-4 h-4 text-slate-400" />
                                                                        )}
                                                                    </div>
                                                                </div>

                                                                {!llmInstalled && (
                                                                    <div className="bg-yellow-50 text-yellow-800 p-3 rounded-md text-xs border border-yellow-100 flex items-center justify-between">
                                                                        <span>模型 (4.3GB) 可由系统自动下载</span>
                                                                        <Button
                                                                            size="sm" variant="outline" className="h-7 text-xs bg-white"
                                                                            onClick={() => (bridge as any).downloadLLMModel()}
                                                                            disabled={llmDownloadProgress > 0 && llmDownloadProgress < 1}
                                                                        >
                                                                            {llmDownloadProgress > 0 && llmDownloadProgress < 1 ? "下载中..." : "立即下载"}
                                                                        </Button>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </SectionCard>
                                    </div>
                                )}

                                {nav === 'dictionary' && (
                                    <SectionCard title="词库管理" icon={<Activity className="w-5 h-5 text-emerald-600" />}>
                                        <div className="space-y-4">
                                            <div className="flex space-x-3">
                                                <Input
                                                    placeholder="输入需要优化的词汇 (如: '深度求索')"
                                                    className="flex-1 bg-white border-slate-200 shadow-sm focus-visible:ring-emerald-500/20"
                                                    value={newWord}
                                                    onChange={(e) => setNewWord(e.target.value)}
                                                    onKeyDown={(e) => e.key === 'Enter' && addWord()}
                                                />
                                                <Button onClick={addWord} className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm">
                                                    添加词汇
                                                </Button>
                                            </div>
                                            <div className="min-h-[300px] border border-slate-200 rounded-lg bg-slate-50/50 p-4">
                                                <div className="flex flex-wrap gap-2">
                                                    {config.user_dict.length === 0 && (
                                                        <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm mt-10">
                                                            暂无自定义词汇
                                                        </div>
                                                    )}
                                                    {config.user_dict.map((word) => (
                                                        <div key={word} className="group flex items-center space-x-2 bg-white border border-slate-200 px-3 py-1.5 rounded-full text-sm text-slate-700 shadow-sm hover:border-emerald-500 hover:ring-1 hover:ring-emerald-500/20 transition-all">
                                                            <span>{word}</span>
                                                            <button
                                                                onClick={() => removeWord(word)}
                                                                className="text-slate-300 hover:text-red-500 transition-colors ml-1"
                                                            >
                                                                &times;
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </SectionCard>
                                )}
                            </div>
                        </div>
                    </ScrollArea>
                </main>
            </div>
        </div>
    );
}

function SectionCard({ title, icon, children }: { title: string, icon: React.ReactNode, children: React.ReactNode }) {
    return (
        <Card className="border border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-3 px-6">
                <CardTitle className="text-sm font-semibold text-slate-700 flex items-center">
                    {icon}
                    <span className="ml-3">{title}</span>
                </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
                {children}
            </CardContent>
        </Card>
    );
}

function SidebarItem({ active, onClick, icon, label, subLabel }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string, subLabel: string }) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "w-full flex items-start p-3 rounded-lg transition-all text-left group",
                active ? "bg-indigo-50 text-indigo-700" : "hover:bg-slate-100 text-slate-600"
            )}
        >
            <div className={cn("mt-0.5 mr-3", active ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-600")}>
                {icon}
            </div>
            <div>
                <p className={cn("text-sm font-semibold", active ? "text-indigo-900" : "text-slate-700")}>{label}</p>
                <p className={cn("text-[10px]", active ? "text-indigo-600/80" : "text-slate-400")}>{subLabel}</p>
            </div>
        </button>
    )
}

export default App
