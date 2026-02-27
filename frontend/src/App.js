import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import ClimateImpact from "./pages/ClimateImpact";
import EnergyIntelligence from "./pages/EnergyIntelligence";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/climate" element={<ClimateImpact />} />
          <Route path="/energy" element={<EnergyIntelligence />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
