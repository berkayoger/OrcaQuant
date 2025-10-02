import { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message?: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = { hasError: false };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message };
  }

  public componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('ErrorBoundary caught an error', error, info);
  }

  public render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 text-center text-white">
          <h1 className="text-3xl font-bold">Bir şeyler ters gitti.</h1>
          <p className="mt-4 max-w-md text-slate-300">
            {this.state.message ?? 'Beklenmedik bir hata oluştu. Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.'}
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}
