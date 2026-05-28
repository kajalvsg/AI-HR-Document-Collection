import { AlertCircle, CheckCircle2, Info } from 'lucide-react'

type AlertVariant = 'success' | 'error' | 'info'

interface AlertProps {
  variant: AlertVariant
  title?: string
  message: string
}

const styles: Record<AlertVariant, string> = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  error: 'border-red-200 bg-red-50 text-red-900',
  info: 'border-sky-200 bg-sky-50 text-sky-900',
}

const icons: Record<AlertVariant, typeof CheckCircle2> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
}

export default function Alert({ variant, title, message }: AlertProps) {
  const Icon = icons[variant]
  return (
    <div className={`flex gap-3 rounded-lg border px-4 py-3 ${styles[variant]}`}>
      <Icon className="mt-0.5 h-5 w-5 shrink-0" />
      <div>
        {title && <p className="font-semibold">{title}</p>}
        <p className={`text-sm ${title ? 'mt-1 opacity-90' : ''}`}>{message}</p>
      </div>
    </div>
  )
}
