import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ChatArea from "./components/ChatArea";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ChatArea />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
