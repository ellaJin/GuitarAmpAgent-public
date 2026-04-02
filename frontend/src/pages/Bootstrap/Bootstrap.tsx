// src/pages/Bootstrap/Bootstrap.tsx
import React from "react";
import "./Bootstrap.css";
import { useBootstrap } from "./useBootstrap";

export default function Bootstrap() {
  // 执行初始化跳转逻辑
  useBootstrap();

  return (
    <div className="boot-container">
      <div className="boot-loader"></div>
      <p className="boot-text">正在检查账号状态...</p>
    </div>
  );
}