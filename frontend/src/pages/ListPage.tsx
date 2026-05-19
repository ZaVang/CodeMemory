import MemoryList from '../components/MemoryList'

interface Props {
  onSelectMemory: (id: string) => void
  refreshTrigger: number
  initialFilter: string
  onCreateMemory: () => void
}

export default function ListPage({ onSelectMemory, refreshTrigger, initialFilter, onCreateMemory }: Props) {
  return (
    <div style={{ flex: 1, overflow: 'hidden' }}>
      <MemoryList
        onSelectMemory={onSelectMemory}
        refreshTrigger={refreshTrigger}
        initialFilter={initialFilter}
        onCreateMemory={onCreateMemory}
      />
    </div>
  )
}
