import type { RequestLog } from '../types/candidate'

interface RequestLogCardProps {
  log: RequestLog
}

function SourceBadge({ source }: { source: RequestLog['source'] }) {
  const isAi = source === 'ai'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        isAi
          ? 'bg-indigo-100 text-indigo-800 ring-1 ring-inset ring-indigo-200'
          : 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200'
      }`}
    >
      {isAi ? 'AI' : 'Template'}
    </span>
  )
}

function formatLabel(value: string): string {
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
}

function formatChannel(channel: string): string {
  if (channel.toLowerCase() === 'email') return 'Email'
  return formatLabel(channel)
}

function formatDeliveryStatus(status: string | null): string {
  if (!status) return '—'
  if (status === 'sent_simulated') return 'Sent Simulated'
  return formatLabel(status)
}

export default function RequestLogCard({ log }: RequestLogCardProps) {
  const timestamp = log.created_at
    ? new Date(log.created_at).toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : null

  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50 px-4 py-3">
        <SourceBadge source={log.source} />
        {timestamp && (
          <time className="text-xs text-slate-500" dateTime={log.created_at ?? undefined}>
            {timestamp}
          </time>
        )}
      </div>
      <dl className="grid gap-3 border-b border-slate-100 px-4 py-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Channel
          </dt>
          <dd className="mt-0.5 font-medium text-slate-900">
            {formatChannel(log.channel || 'email')}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Recipient
          </dt>
          <dd className="mt-0.5 break-all font-medium text-slate-900">
            {log.recipient || '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Delivery Status
          </dt>
          <dd className="mt-0.5 font-medium text-slate-900">
            {formatDeliveryStatus(log.delivery_status)}
          </dd>
        </div>
      </dl>
      <div className="px-4 py-4">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
          Generated message
        </p>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
          {log.message || '—'}
        </p>
      </div>
    </article>
  )
}
