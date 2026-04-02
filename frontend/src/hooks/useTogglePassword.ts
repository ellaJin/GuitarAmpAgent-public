// src/hooks/useTogglePassword.ts
import { useState } from "react";

export const useTogglePassword = () => {
  const [showPwd, setShowPwd] = useState(false);
  const toggle = () => setShowPwd(prev => !prev);
  return { showPwd, toggle };
};