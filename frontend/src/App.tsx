import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login/Login";
import Bootstrap from "./pages/Bootstrap/Bootstrap";
import Chat from "./pages/Chat/Chat";
import Register from "./pages/Register/Register";
import Device from "./pages/Onboarding/Device/Device";
import AuthSuccess from "./pages/Login/AuthSuccess";
import ForgotPassword from "./pages/Login/ForgotPassword";
import DeviceAdmin from "./pages/Admin/DeviceAdmin/DeviceAdmin";
import AdminHome from "./pages/Admin/AdminHome/AdminHome";
import AddDocument from "./pages/Admin/AddDocument/AddDocument";
import SongLibrary from "./pages/Songs/SongLibrary";
import MyDevices from "./pages/MyDevices/MyDevices";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Auth */}
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/auth-success" element={<AuthSuccess />} />
        <Route path="/register" element={<Register />} />

        {/* Routing hub after login */}
        <Route path="/bootstrap" element={<Bootstrap />} />

        {/* Onboarding */}
        <Route path="/onboarding">
          <Route path="device" element={<Device />} />
        </Route>

        {/* Main feature */}
        <Route path="/chat" element={<Chat />} />
        <Route path="/songs" element={<SongLibrary />} />
        <Route path="/devices" element={<MyDevices />} />

        {/* Admin */}
        <Route path="/admin" element={<AdminHome />} />
        <Route path="/admin/device" element={<DeviceAdmin />} />
        <Route path="/admin/add-document/:deviceModelId" element={<AddDocument />} />

        {/* 404 */}
        <Route path="*" element={<div style={{ padding: 24 }}>404</div>} />
      </Routes>
    </BrowserRouter>
  );
}