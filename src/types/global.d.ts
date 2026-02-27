export {};

// Tauri API is imported directly from @tauri-apps/api
// No need for global window declarations

declare global {
  interface Window {
    // Kept for backward compatibility during migration
    // All components should use Tauri API directly
  }
}
