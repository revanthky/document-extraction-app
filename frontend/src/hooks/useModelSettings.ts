import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ModelSettingsResponse } from "../types";

export function useModelSettings() {
  const [settings, setSettings] = useState<ModelSettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getModelSettings();
      setSettings(result);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const isConfigured = Boolean(settings?.api_base_url && settings?.model_name);

  return { settings, loading, isConfigured, refresh };
}
