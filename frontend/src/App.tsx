import { BrowserRouter, Route, Routes } from "react-router-dom";
import ViewerPage from "./pages/ViewerPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ViewerPage />} />
      </Routes>
    </BrowserRouter>
  );
}
