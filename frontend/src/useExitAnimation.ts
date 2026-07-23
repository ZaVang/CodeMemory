import { useState, useEffect, useRef } from 'react'

/**
 * Reusable hook for exit animations.
 *
 * When ``show`` transitions from true to false, the hook enters a "closing"
 * state for ``duration`` ms before setting ``visible`` to false. This allows
 * exit-animation CSS classes to play before the DOM element is removed.
 *
 * Usage:
 *   const { visible, closing } = useExitAnimation(!!props.open)
 *   if (!visible) return null
 *   return <div className={closing ? 'panel-slide-exit' : 'panel-slide-enter'}>...
 */
export function useExitAnimation(show: boolean, duration = 250) {
  const [visible, setVisible] = useState(false)
  const [closing, setClosing] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wasShownRef = useRef(false)

  useEffect(() => {
    if (show) {
      // Opening or already open
      wasShownRef.current = true
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setClosing(false)
      setVisible(true)
    } else if (wasShownRef.current) {
      // Parent closed — play exit animation before unmounting
      setClosing(true)
      timerRef.current = setTimeout(() => {
        setClosing(false)
        setVisible(false)
        wasShownRef.current = false
      }, duration)
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }
  }, [show, duration])

  return { visible, closing }
}
