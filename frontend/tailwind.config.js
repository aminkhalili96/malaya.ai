/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Claude.ai exact color scheme
                primary: "#DA7756",
                secondary: "#1A1915",
                background: "#FAF9F7",
                foreground: "#1A1915",
                panel: "#FFFFFF",
                border: "#E8E5DE",
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
