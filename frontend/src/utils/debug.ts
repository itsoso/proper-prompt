/**
 * Debug logging utility for frontend
 * Provides structured logging with timestamps and levels
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  data?: unknown
  component?: string
}

const LOG_STORAGE_KEY = 'proper_prompts_logs'
const MAX_LOGS = 1000

class DebugLogger {
  private enabled: boolean
  private logs: LogEntry[] = []

  constructor() {
    // Enable debug logging in development
    this.enabled = import.meta.env.DEV || localStorage.getItem('debug') === 'true'
    
    // Load existing logs
    try {
      const stored = localStorage.getItem(LOG_STORAGE_KEY)
      if (stored) {
        this.logs = JSON.parse(stored)
      }
    } catch {
      this.logs = []
    }
  }

  private formatTimestamp(): string {
    return new Date().toISOString()
  }

  private log(level: LogLevel, message: string, data?: unknown, component?: string) {
    if (!this.enabled && level === 'debug') return

    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level,
      message,
      data,
      component,
    }

    // Add to memory
    this.logs.push(entry)
    if (this.logs.length > MAX_LOGS) {
      this.logs = this.logs.slice(-MAX_LOGS)
    }

    // Console output with styling
    const styles = {
      debug: 'color: #94a3b8',
      info: 'color: #0ea5e9',
      warn: 'color: #eab308',
      error: 'color: #ef4444',
    }

    const prefix = component ? `[${component}]` : ''
    console.log(
      `%c[${entry.timestamp}] ${level.toUpperCase()} ${prefix} ${message}`,
      styles[level],
      data !== undefined ? data : ''
    )

    // Persist to localStorage periodically
    this.persistLogs()
  }

  private persistLogs() {
    try {
      localStorage.setItem(LOG_STORAGE_KEY, JSON.stringify(this.logs.slice(-100)))
    } catch {
      // Storage full or unavailable
    }
  }

  debug(message: string, data?: unknown, component?: string) {
    this.log('debug', message, data, component)
  }

  info(message: string, data?: unknown, component?: string) {
    this.log('info', message, data, component)
  }

  warn(message: string, data?: unknown, component?: string) {
    this.log('warn', message, data, component)
  }

  error(message: string, data?: unknown, component?: string) {
    this.log('error', message, data, component)
  }

  // Performance timing
  time(label: string): () => void {
    const start = performance.now()
    return () => {
      const duration = performance.now() - start
      this.debug(`${label} took ${duration.toFixed(2)}ms`)
    }
  }

  // Get all logs
  getLogs(): LogEntry[] {
    return [...this.logs]
  }

  // Clear logs
  clear() {
    this.logs = []
    localStorage.removeItem(LOG_STORAGE_KEY)
    this.info('Logs cleared')
  }

  // Enable/disable debug mode
  setEnabled(enabled: boolean) {
    this.enabled = enabled
    localStorage.setItem('debug', String(enabled))
    this.info(`Debug mode ${enabled ? 'enabled' : 'disabled'}`)
  }

  // Export logs as JSON
  export(): string {
    return JSON.stringify(this.logs, null, 2)
  }
}

export const debugLog = new DebugLogger()

// Expose to window for console access
if (typeof window !== 'undefined') {
  (window as unknown as { debugLog: DebugLogger }).debugLog = debugLog
}

