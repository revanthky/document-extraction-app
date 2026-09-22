import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import type { ModelSettingsResponse, TestConnectionResponse } from "../types";

const DKUBEX_PROVIDER = "dkubex";
const OPENAI_COMPATIBLE_PROVIDER = "openai_compatible";

interface FormState {
  provider: string;
  apiBaseUrl: string;
  apiKey: string;
  modelName: string;
  temperature: number;
  maxTokens: number;
  timeout: number;
  pdfDpi: number;
}

function toFormState(settings: ModelSettingsResponse): FormState {
  return {
    provider: settings.provider,
    apiBaseUrl: settings.api_base_url,
    apiKey: "",
    modelName: settings.model_name,
    temperature: settings.temperature,
    maxTokens: settings.max_tokens,
    timeout: settings.timeout,
    pdfDpi: settings.pdf_render_dpi,
  };
}

export function SettingsPage() {
  const [form, setForm] = useState<FormState | null>(null);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestConnectionResponse | null>(null);
  const [testing, setTesting] = useState(false);
  const [modelOptions, setModelOptions] = useState<string[]>([]);
  const [fetchModelsError, setFetchModelsError] = useState<string | null>(null);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  useEffect(() => {
    api
      .getModelSettings()
      .then((settings) => {
        setForm(toFormState(settings));
        setApiKeyConfigured(settings.api_key_configured);
      })
      .finally(() => setLoading(false));
  }, []);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
    setSaveMessage(null);
    setTestResult(null);
  }

  function handleProviderChange(provider: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const next = { ...prev, provider };
      if (provider === DKUBEX_PROVIDER && !prev.apiBaseUrl) {
        const host = window.prompt("Enter your DKubeX host (e.g. dkubex.example.com):");
        if (host) {
          next.apiBaseUrl = `https://${host}/securellm/v1`;
        }
      }
      return next;
    });
  }

  async function handleSave() {
    if (!form) return;
    setSaving(true);
    setSaveMessage(null);
    try {
      const updated = await api.updateModelSettings({
        provider: form.provider,
        api_base_url: form.apiBaseUrl,
        api_key: form.apiKey || null,
        model_name: form.modelName,
        temperature: form.temperature,
        max_tokens: form.maxTokens,
        timeout: form.timeout,
        pdf_render_dpi: form.pdfDpi,
      });
      setApiKeyConfigured(updated.api_key_configured);
      setForm(toFormState(updated));
      setSaveMessage("Settings saved.");
    } catch (err) {
      setSaveMessage(err instanceof ApiError ? err.message : "Failed to save settings.");
    } finally {
      setSaving(false);
    }
  }

  async function handleTestConnection() {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.testConnection();
      setTestResult(result);
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof ApiError ? err.message : "Connection test failed.",
        model: null,
        response_time_ms: null,
      });
    } finally {
      setTesting(false);
    }
  }

  async function handleFetchModels() {
    if (!form) return;
    setFetchingModels(true);
    setFetchModelsError(null);
    try {
      const result = await api.fetchModels(form.apiBaseUrl, form.apiKey);
      setModelOptions(result.models);
      setShowModelDropdown(true);
    } catch (err) {
      setFetchModelsError(err instanceof ApiError ? err.message : "Failed to fetch models.");
    } finally {
      setFetchingModels(false);
    }
  }

  if (loading || !form) {
    return <div className="text-slate-500">Loading settings...</div>;
  }

  const filteredModels = modelOptions.filter((m) =>
    m.toLowerCase().includes(form.modelName.toLowerCase())
  );

  return (
    <div className="max-w-2xl">
      <h2 className="mb-1 text-xl font-semibold text-slate-900">Vision Model Settings</h2>
      <p className="mb-6 text-sm text-slate-500">
        Configure the Vision Model used for document extraction before uploading documents.
      </p>

      <div className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Provider</label>
          <select
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.provider}
            onChange={(e) => handleProviderChange(e.target.value)}
          >
            <option value={OPENAI_COMPATIBLE_PROVIDER}>OpenAI Compatible</option>
            <option value={DKUBEX_PROVIDER}>DKubeX (SecureLLM)</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">API Base URL</label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.apiBaseUrl}
            onChange={(e) => update("apiBaseUrl", e.target.value)}
            placeholder="http://localhost:8000/v1"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            API Key {apiKeyConfigured && <span className="text-xs text-emerald-600">(configured)</span>}
          </label>
          <input
            type="password"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.apiKey}
            onChange={(e) => update("apiKey", e.target.value)}
            placeholder={apiKeyConfigured ? "••••••••••••••••" : "Enter API key"}
            autoComplete="off"
          />
        </div>

        <div className="relative">
          <label className="mb-1 block text-sm font-medium text-slate-700">Model</label>
          <div className="flex gap-2">
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.modelName}
              onChange={(e) => update("modelName", e.target.value)}
              onFocus={() => modelOptions.length > 0 && setShowModelDropdown(true)}
              onBlur={() => setTimeout(() => setShowModelDropdown(false), 150)}
              placeholder="Qwen3-VL-32B-Instruct"
            />
            <button
              type="button"
              onClick={handleFetchModels}
              disabled={fetchingModels || !form.apiBaseUrl}
              className="whitespace-nowrap rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {fetchingModels ? "Fetching..." : "Fetch Models"}
            </button>
          </div>
          {showModelDropdown && filteredModels.length > 0 && (
            <ul className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
              {filteredModels.map((model) => (
                <li
                  key={model}
                  className="cursor-pointer px-3 py-2 text-sm hover:bg-slate-100"
                  onMouseDown={() => {
                    update("modelName", model);
                    setShowModelDropdown(false);
                  }}
                >
                  {model}
                </li>
              ))}
            </ul>
          )}
          {fetchModelsError && <p className="mt-1 text-xs text-amber-600">{fetchModelsError}</p>}
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Temperature</label>
            <input
              type="number"
              step="0.1"
              min={0}
              max={2}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.temperature}
              onChange={(e) => update("temperature", Number(e.target.value))}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Max Tokens</label>
            <input
              type="number"
              min={1}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.maxTokens}
              onChange={(e) => update("maxTokens", Number(e.target.value))}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Timeout (s)</label>
            <input
              type="number"
              min={1}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.timeout}
              onChange={(e) => update("timeout", Number(e.target.value))}
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">PDF Rendering DPI</label>
          <input
            type="number"
            min={72}
            max={600}
            className="w-40 rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.pdfDpi}
            onChange={(e) => update("pdfDpi", Number(e.target.value))}
          />
        </div>

        <div className="flex items-center gap-3 border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testing}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            {testing ? "Testing..." : "Test Connection"}
          </button>
          {saveMessage && <span className="text-sm text-slate-600">{saveMessage}</span>}
        </div>

        {testResult && (
          <div
            className={`rounded-md p-3 text-sm ${
              testResult.success ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"
            }`}
          >
            {testResult.success ? (
              <>
                <p className="font-medium">✓ Connection successful</p>
                {testResult.model && <p>Model: {testResult.model}</p>}
                {testResult.response_time_ms != null && (
                  <p>Response time: {(testResult.response_time_ms / 1000).toFixed(1)} seconds</p>
                )}
              </>
            ) : (
              <p>{testResult.message}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
