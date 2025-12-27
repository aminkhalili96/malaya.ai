import React from 'react';
import { trackEvent } from '../utils/analytics';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        trackEvent('ui_error', {
            message: error?.message,
            stack: error?.stack,
            componentStack: info?.componentStack,
        });
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null });
        if (typeof window !== 'undefined') {
            window.location.reload();
        }
    };

    render() {
        if (!this.state.hasError) {
            return this.props.children;
        }

        return (
            <div className="flex h-screen items-center justify-center bg-[#FAF9F7] px-6 text-[#1A1915]">
                <div className="max-w-md rounded-2xl border border-[#E8E5DE] bg-white p-6 shadow-sm">
                    <div className="text-sm uppercase tracking-[0.2em] text-[#A7A19A]">Something went wrong</div>
                    <div className="mt-2 text-lg font-semibold">We hit a UI error</div>
                    <div className="mt-3 text-sm text-[#6F6A63]">
                        Try reloading the app. If the issue persists, check the console logs for details.
                    </div>
                    <button
                        type="button"
                        onClick={this.handleReset}
                        className="mt-4 rounded-lg bg-[#DA7756] px-4 py-2 text-sm font-medium text-white hover:bg-[#C4654A]"
                    >
                        Reload
                    </button>
                </div>
            </div>
        );
    }
}

export default ErrorBoundary;
