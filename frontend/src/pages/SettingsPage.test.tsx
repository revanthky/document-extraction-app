import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import { SettingsPage } from "./SettingsPage";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return {
    ...actual,
    api: {
      ...actual.api,
      getModelSettings: vi.fn(),
      updateModelSettings: vi.fn(),
      testConnection: vi.fn(),
      fetchModels: vi.fn(),
    },
  };
});

const baseSettings = {
  provider: "openai_compatible",
  api_base_url: "http://localhost:8000/v1",
  api_key_masked: "",
  api_key_configured: false,
  model_name: "vision-model",
  temperature: 0,
  max_tokens: 4096,
  timeout: 120,
  pdf_render_dpi: 150,
};

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.mocked(api.getModelSettings).mockResolvedValue({ ...baseSettings });
  });

  it("loads and displays existing settings", async () => {
    render(<SettingsPage />);
    expect(await screen.findByDisplayValue("http://localhost:8000/v1")).toBeInTheDocument();
    expect(screen.getByDisplayValue("vision-model")).toBeInTheDocument();
  });

  it("never renders the raw API key, even when configured", async () => {
    vi.mocked(api.getModelSettings).mockResolvedValue({
      ...baseSettings,
      api_key_configured: true,
      api_key_masked: "****************",
    });
    render(<SettingsPage />);
    await screen.findByDisplayValue("http://localhost:8000/v1");
    expect(screen.queryByText("****************")).not.toBeInTheDocument();
    expect(screen.getByText(/\(configured\)/)).toBeInTheDocument();
  });

  it("saves updated settings", async () => {
    vi.mocked(api.updateModelSettings).mockResolvedValue({
      ...baseSettings,
      model_name: "new-model",
      api_key_configured: true,
    });
    render(<SettingsPage />);
    await screen.findByDisplayValue("http://localhost:8000/v1");

    fireEvent.change(screen.getByDisplayValue("vision-model"), { target: { value: "new-model" } });
    fireEvent.click(screen.getByText("Save Settings"));

    await waitFor(() => expect(api.updateModelSettings).toHaveBeenCalled());
    expect(await screen.findByText("Settings saved.")).toBeInTheDocument();
  });

  it("shows a success message with response time after a successful test connection", async () => {
    vi.mocked(api.testConnection).mockResolvedValue({
      success: true,
      message: "Connection successful",
      model: "vision-model",
      response_time_ms: 2400,
    });
    render(<SettingsPage />);
    await screen.findByDisplayValue("http://localhost:8000/v1");

    fireEvent.click(screen.getByText("Test Connection"));

    expect(await screen.findByText("✓ Connection successful")).toBeInTheDocument();
    expect(screen.getByText("Response time: 2.4 seconds")).toBeInTheDocument();
  });

  it("shows a failure message when the connection test fails", async () => {
    vi.mocked(api.testConnection).mockResolvedValue({
      success: false,
      message: "Authentication failed.",
      model: null,
      response_time_ms: 500,
    });
    render(<SettingsPage />);
    await screen.findByDisplayValue("http://localhost:8000/v1");

    fireEvent.click(screen.getByText("Test Connection"));

    expect(await screen.findByText("Authentication failed.")).toBeInTheDocument();
  });

  it("auto-fills the DKubeX base URL only when currently empty", async () => {
    vi.mocked(api.getModelSettings).mockResolvedValue({ ...baseSettings, api_base_url: "" });
    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("dkubex.example.com");

    render(<SettingsPage />);
    await screen.findByDisplayValue("vision-model");

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "dkubex" } });

    expect(promptSpy).toHaveBeenCalled();
    expect(await screen.findByDisplayValue("https://dkubex.example.com/securellm/v1")).toBeInTheDocument();
  });
});
