import Dashboard from '../components/Dashboard'

interface Props {
  onSelectMemory: (id: string) => void
  onNavigateToFilter: (filter: string, type: 'tag' | 'maturity') => void
  refreshTrigger: number
  onCreateMemory: () => void
  onError: (message: string) => void
}

export default function DashboardPage({
  onSelectMemory,
  onNavigateToFilter,
  refreshTrigger,
  onCreateMemory,
  onError,
}: Props) {
  return (
    <div style={{ flex: 1, overflow: 'hidden' }}>
      <Dashboard
        onSelectMemory={onSelectMemory}
        onNavigateToFilter={onNavigateToFilter}
        refreshTrigger={refreshTrigger}
        onCreateMemory={onCreateMemory}
        onError={onError}
      />
    </div>
  )
}
