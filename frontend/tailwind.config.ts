import type { Config } from 'tailwindcss';
const config: Config = { content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'], theme: { extend: { colors: { ink: '#17382f', leaf: '#2f6b4f', sand: '#f6f3ec', saffron: '#e6a24a' }, boxShadow: { soft: '0 18px 50px rgba(23,56,47,.08)' } } }, plugins: [] };
export default config;
