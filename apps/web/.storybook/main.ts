import react from "@vitejs/plugin-react";
import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  stories: ["../app/**/*.stories.tsx"],
  addons: ["@storybook/addon-a11y"],
  framework: { name: "@storybook/react-vite", options: {} },
  // SB10/rolldown não injeta o preset JSX no preview neste ambiente — injeção manual
  viteFinal: async (c) => {
    c.plugins = [...(c.plugins ?? []), react()];
    return c;
  },
};
export default config;
