interface StatusBadgeProps {
  label: string
  variant?: 'extraction' | 'document'
}

function normalize(label: string) {
  return label?.toLowerCase() ?? ''
}

function extractionClass(status: string) {
  switch (normalize(status)) {
    case 'parsed':
      return 'bg-emerald-100 text-emerald-800 ring-emerald-200'
    case 'partial':
      return 'bg-amber-100 text-amber-800 ring-amber-200'
    case 'failed':
      return 'bg-red-100 text-red-800 ring-red-200'
    case 'pending':
    default:
      return 'bg-slate-100 text-slate-700 ring-slate-200'
  }
}

function documentClass(status: string) {
  switch (normalize(status)) {
    case 'complete':
      return 'bg-emerald-100 text-emerald-800 ring-emerald-200'
    case 'partial':
      return 'bg-amber-100 text-amber-800 ring-amber-200'
    case 'none':
    default:
      return 'bg-slate-100 text-slate-700 ring-slate-200'
  }
}

export default function StatusBadge({ label, variant = 'extraction' }: StatusBadgeProps) {
  const display = label || 'Unknown'
  const className =
    variant === 'document' ? documentClass(display) : extractionClass(display)

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${className}`}
    >
      {display}
    </span>
  )
}
