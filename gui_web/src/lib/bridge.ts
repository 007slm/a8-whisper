// bridge.ts - Pywebview Native Bridge

declare global {
    interface Window {
        pywebview?: {
            api: any;
        };
        // For events from Python
        handlePywebviewMessage?: (message: { type: string; data: any }) => void;
        handleAudioLevel?: (level: number) => void;
    }
}

class Bridge {
    private readyPromise: Promise<any>;
    private listeners: { [key: string]: ((data: any) => void)[] } = {};

    constructor() {
        // Initialize Promise that resolves when pywebview is ready
        this.readyPromise = new Promise((resolve) => {
            if (window.pywebview) {
                console.log("✅ Pywebview already ready");
                resolve(window.pywebview.api);
            } else {
                console.log("⏳ Waiting for pywebviewready...");
                window.addEventListener('pywebviewready', () => {
                    console.log("✅ Pywebview ready event fired");
                    resolve(window.pywebview!.api);
                });
            }
        });

        // Setup global handlers for Python -> JS calls
        window.handlePywebviewMessage = (msg: { type: string; data: any }) => {
            console.log("🔔 Received message from Python:", msg.type, msg.data);
            this.emit(msg.type, msg.data);

            // Dispatch global CustomEvent for components listening directly on window (e.g. App.tsx)
            // This allows loose coupling and supports 'init_status' etc.
            window.dispatchEvent(new CustomEvent(msg.type, { detail: msg.data }));
        };

        window.handleAudioLevel = (level: number) => {
            // Dispatch to specific event name
            this.emit("audio_level", level);
        }
    }

    // Generic Event Emitter
    on(event: string, callback: (data: any) => void) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event: string, callback: (data: any) => void) {
        if (!this.listeners[event]) return;
        this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }

    emit(event: string, data: any) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(cb => cb(data));
        }
    }

    // --- Helper Methods (Restored for App.tsx compatibility) ---

    async getConfig(): Promise<any> {
        return new Promise(async (resolve) => {
            // 1. Setup listener *before* requesting
            const handler = (data: any) => {
                this.off('config', handler);
                resolve(data);
            };
            this.on('config', handler);

            // 2. Request (fire-and-forget)
            try {
                await this.requestConfig();
            } catch (e) {
                console.error("Failed to request config", e);
            }

            // 3. Timeout fallback
            setTimeout(() => {
                this.off('config', handler);
                // Start with default config if timeout
                resolve({});
            }, 2000);
        });
    }

    onConfigChanged(callback: (config: any) => void) {
        this.on('config', callback);
    }

    onLlmDownloadProgress(callback: (progress: number) => void) {
        this.on('llm_progress', callback);
    }

    onDownloadProgress(callback: (model: string, progress: number) => void) {
        this.on('model_progress', (data: { model: string; progress: number }) => {
            callback(data.model, data.progress);
        });
    }

    // --- API Methods ---

    async call(method: string, ...args: any[]): Promise<any> {
        const api = await this.readyPromise;
        if (api && typeof api[method] === 'function') {
            try {
                return await api[method](...args);
            } catch (e) {
                console.error(`Bridge Call Error [${method}]:`, e);
                throw e;
            }
        } else {
            console.error(`Method ${method} not found in pywebview api`);
            throw new Error(`Method ${method} not found`);
        }
    }

    // Typed Wrappers
    async requestConfig() { return this.call('requestConfig'); }
    async saveConfig(config: any) { return this.call('saveConfig', config); }
    async minimizeWindow() { return this.call('minimizeWindow'); }
    async maximizeWindow() { return this.call('maximizeWindow'); } // If implemented
    async closeWindow() { return this.call('closeWindow'); }
    async startDrag() { return this.call('startDrag'); }
    async downloadModel(model: string) { return this.call('downloadModel', model); }
    async openExternal(url: string) { return this.call('openExternal', url); }

    // LLM
    async checkLLMFileExists() { return this.call('checkLLMFileExists'); }
    async downloadLLMModel() { return this.call('downloadLLMModel'); }
}

export const bridge = new Bridge();
