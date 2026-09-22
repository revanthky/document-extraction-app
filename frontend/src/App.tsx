import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ExtractionPage } from "./pages/ExtractionPage";
import { SettingsPage } from "./pages/SettingsPage";

const basename = import.meta.env.BASE_URL.replace(/\/$/, "") || "/";

export function App() {
  return (
    <Router basename={basename}>
      <Layout>
        <Routes>
          <Route path="/" element={<SettingsPage />} />
          <Route path="/extract" element={<ExtractionPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
