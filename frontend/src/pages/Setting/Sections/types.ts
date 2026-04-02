// /src/pages/Setting/sections/types.ts
// /src/pages/Setting/sections/types.ts
export type SettingsKey = "general" | "notifications" | "security" | "account";

export const SETTINGS_MENU: { key: SettingsKey; label: string; icon: string }[] = [
  { key: "general", label: "General", icon: "⚙️" },
  { key: "notifications", label: "Notifications", icon: "🔔" },
  { key: "security", label: "Security", icon: "🛡️" },
  { key: "account", label: "Account", icon: "👤" },
];



